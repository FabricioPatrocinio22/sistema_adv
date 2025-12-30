import email
from ntpath import basename
import stat
import shutil
import os
import pyotp

from fastapi.responses import FileResponse
from fastapi import UploadFile, File
from typing import Optional
from fastapi import FastAPI, Depends, Header, status
from sqlmodel import Field, SQLModel, create_engine, Session, select
from fastapi import HTTPException # Adicione isso aos seus imports
from security import oauth2_scheme, verificar_token
from fastapi.security import OAuth2PasswordRequestForm # Adicione este
from datetime import date, timedelta # Adicione ao topo
from fastapi.middleware.cors import CORSMiddleware

# Importamos nossas próprias criações:
from models import Processo, Usuario
from database import engine, create_db_and_tables
from security import criar_token_acesso, gerar_hash_senha, oauth2_scheme, verificar_senha, gerar_segredo_2fa, verificar_codigo_2fa

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção real, trocaríamos "*" pelo link do seu site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Isso roda quando o servidor liga
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def home():
    return {"mensagem": "Sistema conectado ao Banco de Dados!"}

@app.post("/processos")
def criar_processo(processo: Processo, token: str = Depends(oauth2_scheme)):

    email_user = verificar_token(token)
    if not email_user:
        raise HTTPException(status_code=401, detail="Token inválido")

    with Session(engine) as session:
        # 1. Verificar se o número já existe
        instrucao = select(Processo).where(Processo.numero == processo.numero)
        existente = session.exec(instrucao).first()

        if existente:
            # Se encontrou algo, lançamos o erro antes de cadastrar
            raise HTTPException(
                status_code=400, 
                detail=f"Já existe um processo com este número (ID: {existente.id}).")

        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()
        processo.usuario_id = usuario.id

        if processo.data_prazo and isinstance(processo.data_prazo, str):
            try:
                # Transforma "2025-12-31" em data real
                processo.data_prazo = date.fromisoformat(str(processo.data_prazo))
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de data inválido.")

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
        usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()

        instrucao = select(Processo).where(Processo.usuario_id == usuario.id)
        resultados = session.exec(instrucao).all()
        return resultados

@app.put("/processos/{processo_id}")
def atualizar_processos(processo_id: int, processo_atualizado: Processo, token: str = Depends(oauth2_scheme)):
    email_usuario = verificar_token(token)

    with Session(engine) as session:
        # 1. Identifica quem está logado
        usuario = session.exec(select(Usuario).where(Usuario.email == email_usuario)).first()

        # 2. Busca o processo pelo ID
        db_processo = session.get(Processo, processo_id)

        if not db_processo:
            return {"erro": "Processo não encontrado"}

        # 3. TRAVA DE SEGURANÇA: O processo pertence a quem está logado?
        if db_processo.usuario_id != usuario.id:
            raise HTTPException(status_code=403, detail="Você não tem permissao para alterar este processo")

        # 4. Se passou, atualiza os dados
        dados_novos = processo_atualizado.model_dump(exclude_unset = True)
        db_processo.sqlmodel_update(dados_novos)
        
        session.add(db_processo)
        session.commit()
        session.refresh(db_processo)
        return db_processo

@app.post("/processos/{processo_id}/anexo")
def anexar_arquivo(
    processo_id: int,
    arquivo: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    email_user = verificar_token(token)

    with Session(engine) as session:
        #Busca o processo
        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()
        processo = session.get(Processo, processo_id)

        if not processo or processo.usuario_id != usuario.id:
            raise HTTPException(status_code=404, detail="Processo não encontrado ou acesso negado")

        # 2. Cria a pasta 'uploads' se ela não existir
        pasta_destino = "uploads"
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        # 3. Define o nome do arquivo (Ex: processo_1_contrato.pdf)
        # Usamos o ID para evitar que arquivos com mesmo nome se sobrescrevam
        nome_arquivo = f"processo_{processo.id}_{arquivo.filename}"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)

        # 4. Salva o arquivo no disco
        with open(caminho_completo, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)

        # 5. Salva o caminho no Banco de Dados
        processo.arquivo_pdf = caminho_completo
        session.add(processo)
        session.commit()
        session.refresh(processo)

        return {"mensagem": "Arquivo enviado com sucesso!", "caminho": caminho_completo}

@app.get("/processos/{processo_id}/download")
def baixar_arquivo(processo_id: int, token: str = Depends(oauth2_scheme)):
    email_user = verificar_token(token)

    with Session(engine) as session:

        user = session.exec(select(Usuario).where(Usuario.email == email_user)).first()
        processo = session.get(Processo, processo_id)

        if not processo:
            raise HTTPException(status_code=404, detail="Processo não encontrado")

        if processo.usuario_id != user.id:
            raise HTTPException(status_code=403, detail="Você nao tem permissão para acessar esse arquivo")

        if not processo.arquivo_pdf:
            raise HTTPException(status_code=404, detail="Este processo não tem arquivos anexados")

        if not os.path.isfile(processo.arquivo_pdf):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor (pode ter sido apagado)")

        return FileResponse(
            path=processo.arquivo_pdf,
            filename=os.path.basename(processo.arquivo_pdf)
        )

@app.delete("/processos/{processo_id}")
def excluir_processo(processo_id: int, token: str = Depends(oauth2_scheme)):
    email_usuario = verificar_token(token)

    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email_usuario)).first()
        # 1. Busca o processo
        db_processo = session.get(Processo, processo_id)
        
        if not db_processo:
            return {"erro": "Processo não encontrado"}

        # Verifica se o dono é o mesmo
        if db_processo.usuario_id != usuario.id:
            raise HTTPException(status_code=404, detail="Permissão negada")

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
    otp: Optional[str] = None 
):
    with Session(engine) as session:
        usuario_db = session.exec(select(Usuario).where(Usuario.email == form_data.username)).first()

        if not usuario_db or not verificar_senha(form_data.password, usuario_db.senha_hash):
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

        # LOGICA DE TESTE: Só valida o 2FA se você enviar o OTP. 
        # Se não enviar, ele loga direto (facilitando o uso do cadeado do Swagger)
        if usuario_db.is_2fa_enabled and otp:
            if not verificar_codigo_2fa(usuario_db.secret_2fa, otp):
                raise HTTPException(status_code=401, detail="Código 2FA Inválido")

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

@app.get("/processos/urgents")
def listar_prazos_urgentes(token: str = Depends(oauth2_scheme)):
    email_usuario = verificar_token(token)

    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email_usuario)).first()

        # Define o que é "urgente": de hoje até daqui a 5 dias
        hoje = date.today()
        limite_alerta = hoje + timedelta(days=5)

        # Busca processos do usuário que vencem nesse intervalo
        statement = select(Processo).where(
            Processo.usuario_id == usuario.id,
            Processo.data_prazo >= hoje,
            Processo.data_prazo <= limite_alerta
        )

        results = session.exec(statement).all()
        return results