from typing import Optional
from fastapi import FastAPI, Depends, Header
from sqlmodel import Field, SQLModel, create_engine, Session, select
from fastapi import HTTPException # Adicione isso aos seus imports
from security import oauth2_scheme, verificar_token
from fastapi.security import OAuth2PasswordRequestForm # Adicione este
import pyotp

# Importamos nossas próprias criações:
from models import Processo, Usuario
from database import engine, create_db_and_tables
from security import criar_token_acesso, gerar_hash_senha, oauth2_scheme, verificar_senha, gerar_segredo_2fa, verificar_codigo_2fa

app = FastAPI()

# Isso roda quando o servidor liga
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def home():
    return {"mensagem": "Sistema conectado ao Banco de Dados!"}

@app.post("/processos")
def criar_processo(processo: Processo):
    with Session(engine) as session:
        # 1. Verificar se o número já existe
        instrucao = select(Processo).where(Processo.numero == processo.numero)
        existente = session.exec(instrucao).first()

        if existente:
            # Se encontrou algo, lançamos o erro antes de cadastrar
            raise HTTPException(
                status_code=400, 
                detail=f"Já existe um processo com este número (ID: {existente.id}).")

        session.add(processo)
        session.commit()
        session.refresh(processo)
        return processo

@app.get('/processos')
def listar_processos(token: str = Depends(oauth2_scheme)):

    email = verificar_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    with Session(engine) as session:
        instrucao = select(Processo)
        resultados = session.exec(instrucao).all()
        return resultados

@app.put("/processos/{processo_id}")
def atualizar_processos(processo_id: int, processo_atualizado: Processo):
    with Session(engine) as session:
        db_processo = session.get(Processo, processo_id)

        if not db_processo:
            return {"erro": "Processo não encontrado"}

        dados_novos = processo_atualizado.dict(exclude_unset = True)
        for chave, valor in dados_novos.items():
            setattr(db_processo, chave, valor)
        
        session.add(db_processo)
        session.commit()
        session.refresh(db_processo)
        return db_processo

@app.delete("/processos/{processo_id}")
def excluir_processo(processo_id: int):
    with Session(engine) as session:
        # 1. Busca o processo
        db_processo = session.get(Processo, processo_id)
        
        if not db_processo:
            return {"erro": "Processo não encontrado"}

        # 2. Deleta e confirma
        session.delete(db_processo)
        session.commit()
        
        return {"mensagem": f"Processo {processo_id} excluído com sucesso"}

@app.post("/usuarios")
def cadastrar_usuario(usuario_data: Usuario):
    with Session(engine) as session:

        print(f"DEBUG: Senha recebida: {usuario_data.senha_hash}") # Adicione esta linha
        print(f"DEBUG: Tamanho da senha: {len(usuario_data.senha_hash)}") # E esta
        # 1. Verificar se o e-mail já existe
        statement = select(Usuario).where(Usuario.email == usuario_data.email)
        usuario_existente = session.exec(statement).first()

        if usuario_existente:
            raise HTTPException(
                status_code=400,
                detail="Este e-mail já está cadastrado."
            )

        # 2. Gerar o hash da senha (nunca salvamos a senha pura!)
        senha_criptografada = gerar_hash_senha(usuario_data.senha_hash)

        # 3. Substituir a senha original pelo hash antes de salvar
        usuario_data.senha_hash = senha_criptografada

        # 4. Salvar no banco
        session.add(usuario_data)
        session.commit()
        session.refresh(usuario_data)

        return {"mensagem": "Usuario criado com sucesso", "id": usuario_data.id}

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    x_otp: Optional[str] = Header(None)    
):
    with Session(engine) as session:

        statement = select(Usuario).where(Usuario.email == form_data.username)
        usuario_db = session.exec(statement).first()

        #válida senha e login
        if not usuario_db or not verificar_senha(form_data.password, usuario_db.senha_hash):
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

        #válida se o 2FA ta ativo e pede codigo
        if usuario_db.is_2fa_enabled:
            if not x_otp:
                raise HTTPException(
                    status_code=403,
                    detail="2FA_REQUIRED"
                )

            if not verificar_codigo_2fa(usuario_db.secret_2fa, x_otp):
                raise HTTPException(status_code=401, detail="Código 2FA Inválido")

        #Se passou por tudo, gera o token
        token = criar_token_acesso(dados={"sub": usuario_db.email})

        return {"access_token": token, "token_type": "bearer"}

@app.post("/usuarios/ativar-2fa")
def ativar_2fa(token: str = Depends(oauth2_scheme)):
    email = verificar_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
        
        # Gera o segredo e salva no banco
        novo_segredo = gerar_segredo_2fa()
        usuario.secret_2fa = novo_segredo
        usuario.is_2fa_enabled = True
        
        session.add(usuario)
        session.commit()

        # Link para o Google Authenticator (TOTP)
        link_auth = pyotp.totp.TOTP(novo_segredo).provisioning_uri(
            name=email, 
            issuer_name="Sistema Juridico"
        )
        
        return {
            "mensagem": "2FA Ativado com sucesso!",
            "segredo_manual": novo_segredo,
            "link_qr_code": link_auth
        }

@app.post("/usuarios/confirmar-2fa")
def confirmar_2fa(codigo: str, token: str = Depends(oauth2_scheme)):
    email = verificar_token(token)
    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
        
        # Usamos a função do security.py para validar o código de 6 dígitos
        if verificar_codigo_2fa(usuario.secret_2fa, codigo):
            usuario.is_2fa_enabled = True # Agora sim, está oficialmente ativo!
            session.add(usuario)
            session.commit()
            return {"mensagem": "2FA ativado com sucesso! Seu sistema está protegido."}
        else:
            raise HTTPException(status_code=400, detail="Código 2FA inválido ou expirado")