import email
import stat
import shutil
import os
import pyotp
import pyotp
import qrcode
import io
import base64
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from google import genai

from ntpath import basename
from fastapi import Body
from fastapi.responses import StreamingResponse
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
from pypdf import PdfReader
from dotenv import load_dotenv


# Importamos nossas próprias criações:
from ia import analisar_documento
from models import Processo, Usuario, UsuarioCreate, Financeiro
from database import engine, create_db_and_tables
from security import criar_token_acesso, gerar_hash_senha, oauth2_scheme, verificar_senha, gerar_segredo_2fa, verificar_codigo_2fa
import boto3
from botocore.exceptions import NoCredentialsError
from botocore.config import Config

# 1. Carrega as variáveis do arquivo .env
load_dotenv()

s3_client = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
    config=Config(signature_version='s3v4')
)

# 2. Pega a chave do ambiente seguro
chave_secreta = os.getenv("GEMINI_API_KEY")

if not chave_secreta:
    print("ERRO: Chave API não encontrada no arquivo .env")
else:
    # 3. Configura o Gemini
    genai.Client(api_key=chave_secreta)

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

@app.post("/2fa/setup")
def setup_2fa(token: str = Depends(oauth2_scheme)):
    email_user = verificar_token(token)

    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()

        # 1. Gera um segredo aleatório se ele não tiver
        if not usuario.totp_secret:
            usuario.totp_secret = pyotp.random_base32()
            session.add(usuario)
            session.commit()
            session.refresh(usuario)

        # 2. Cria a URL do QR Code (padrão do Google Authenticator)
        uri_otp = pyotp.totp.TOTP(usuario.totp_secret).provisioning_uri(
            name=usuario.email, 
            issuer_name="Advocacia SaaS"
        )

        # 3. Transforma em Imagem
        img = qrcode.make(uri_otp)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        # Retorna a imagem em Base64 para o Frontend mostrar fácil
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return {"qr_code_b64": img_b64, "segredo": usuario.totp_secret}

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

        nome_s3 = f"{processo.id}/{arquivo.filename}"

        try:
            s3_client.upload_fileobj(
                arquivo.file,
                os.getenv("AWS_BUCKET_NAME"),
                nome_s3
            )
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="Credenciais AWS não configuradas")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao enviar arquivo para S3: {str(e)}")

        # Salva o caminho no banco de dados
        processo.arquivo_pdf = nome_s3
        session.add(processo)
        session.commit()
        session.refresh(processo)

        return {"mensagem": "Arquivo salvo na nuvem AWS!", "caminho": processo.arquivo_pdf}

@app.get("/processos/{processo_id}/download")
def baixar_arquivo(processo_id: int, token: str = Depends(oauth2_scheme)):
    email_user = verificar_token(token)

    with Session(engine) as session:

        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()
        processo = session.get(Processo, processo_id)

        if not processo or processo.usuario_id != usuario.id:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        if not processo.arquivo_pdf:
             raise HTTPException(status_code=404, detail="Sem anexo")

        try:

            url = s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": os.getenv("AWS_BUCKET_NAME"),
                    "Key": processo.arquivo_pdf
                },
                ExpiresIn=3600
            )
            return {"url_download": url}
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="Credenciais AWS não configuradas")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao gerar URL de download: {str(e)}")

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

        financeiros = session.exec(select(Financeiro).where(Financeiro.processo_id == processo_id)).all()
        for item in financeiros:
            session.delete(item)

        if db_processo.arquivo_pdf:
            try:
                s3_client.delete_object(
                    Bucket=os.getenv("AWS_BUCKET_NAME"),
                    Key=db_processo.arquivo_pdf
                )
                print(f"Arquivo {db_processo.arquivo_pdf} apagado do S3.")
            except Exception as e:
                print(f"Erro ao apagar do S3 (mas vamos seguir): {e}")

        # 2. Deleta e confirma
        session.delete(db_processo)
        session.commit()
        
        return {"mensagem": f"Processo e todos os dados vinculados foram excluídos com sucesso"}

@app.post("/usuarios")
def cadastrar_usuario(usuario_data: UsuarioCreate):
    with Session(engine) as session:

        print(f"DEBUG: Senha recebida: {usuario_data.senha}") # Adicione esta linha
        print(f"DEBUG: Tamanho da senha: {len(usuario_data.email)}") # E esta
        # 1. Verificar se o e-mail já existe
        statement = select(Usuario).where(Usuario.email == usuario_data.email)
        usuario_existente = session.exec(statement).first()

        if usuario_existente:
            raise HTTPException(
                status_code=400,
                detail="Este e-mail já está cadastrado."
            )

        # 2. Gerar o hash da senha (nunca salvamos a senha pura!)
        senha_criptografada = gerar_hash_senha(usuario_data.senha)

        # 3. Substituir a senha original pelo hash antes de salvar
        novo_usuario = Usuario(
            email = usuario_data.email,
            senha_hash=senha_criptografada
        )

        # 4. Salvar no banco
        session.add(novo_usuario)
        session.commit()
        session.refresh(novo_usuario)

        return {"email": novo_usuario.email, "mensagem": "Usuario criado com sucesso"}

# --- Substitua a rota antiga /login por esta /token ---
@app.post("/token")
def login_para_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    codigo_2fa: Optional[str] = Header(default=None, alias="codigo_2fa") # Pega o código do cabeçalho enviado pelo Frontend
):
    with Session(engine) as session:
        # 1. Busca o usuário pelo e-mail
        usuario_db = session.exec(select(Usuario).where(Usuario.email == form_data.username)).first()

        # 2. Verifica se existe e se a senha bate
        if not usuario_db or not verificar_senha(form_data.password, usuario_db.senha_hash):
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

        # 3. LÓGICA DO 2FA (A Blindagem)
        # Verifica se o usuário tem o segredo no banco (ou seja, ativou o 2FA)
        if usuario_db.totp_secret:
            
            # Se tem 2FA ativado, o código é OBRIGATÓRIO
            if not codigo_2fa:
                raise HTTPException(status_code=401, detail="Código 2FA obrigatório para este usuário.")
            
            # Valida o código matemático usando a biblioteca pyotp
            totp = pyotp.TOTP(usuario_db.totp_secret)
            if not totp.verify(codigo_2fa):
                raise HTTPException(status_code=401, detail="Código 2FA inválido ou expirado.")

        # 4. Se passou por tudo, gera o token de acesso
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

@app.post("/processos/{processo_id}/analise-ia")
def solicitar_resumo_ia(processo_id: int, token: str = Depends(oauth2_scheme)):
    email_user = verificar_token(token)

    with Session(engine) as session:
        #Busca o processo
        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()
        processo = session.get(Processo, processo_id)

        if not processo or processo.usuario_id != usuario.id:
            raise HTTPException(status_code=404, detail="Processo não encontrado")

        if not processo.arquivo_pdf:
             raise HTTPException(status_code=400, detail="Este processo não tem PDF para ler.")

        texto_pdf = ''
        try:
            response = s3_client.get_object(Bucket=os.getenv("AWS_BUCKET_NAME"), Key=processo.arquivo_pdf)
            arquivo_memoria = io.BytesIO(response['Body'].read())
            pdf_reader = PdfReader(arquivo_memoria)

            for i, page in enumerate(pdf_reader.pages):
                if i > 20: break
                texto_pdf += page.extract_text()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao ler PDF: {str(e)}")

        prompt = f"""
        Você é um assistente jurídico sênior.
        Analise o texto do processo abaixo e gere um RESUMO EXECUTIVO em formato de texto (Markdown).
        NÃO retorne JSON. Retorne um texto legível para um advogado ler rápido.

        Estrutura sugerida:
        **📝 Resumo dos Fatos:** (O que aconteceu resumidamente)
        **⚖️ Partes:** (Quem está processando quem)
        **💰 Pedidos e Valores:** (O que está sendo pedido)
        **⚠️ Pontos de Atenção:** (Prazos ou riscos imediatos identificados)

        --- TEXTO DO PROCESSO ---
        {texto_pdf}
        """

        try:
            client = genai.Client(api_key=chave_secreta)
            response = client.models.generate_content(
                model="models/gemini-3-flash-preview",
                contents=prompt
            )
            resumo = response.text

            processo.resumo_ia = resumo
            session.add(processo)
            session.commit()

            return {"mensagem": "Resumo da IA gerado com sucesso!", "resumo": resumo}
        except Exception as e:
            print(f"Erro na extração: {e}")
            raise HTTPException(status_code=500, detail="Não foi possível extrair dados do PDF.")

@app.get("/dashboard/geral")
def dados_dashboard(token: str = Depends(oauth2_scheme)):
    email_user = verificar_token(token)

    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()
        processos = session.exec(select(Processo).where(Processo.usuario_id == usuario.id)).all()

        financeiro = session.exec(select(Financeiro).where(Financeiro.usuario_id == usuario.id)).all()

        total_honorarios = sum(l.valor for l in financeiro if l.tipo == "Honorários")
        total_recebido = sum(l.valor for l in financeiro if l.tipo == "Recebido")
        total_pendente = total_honorarios - total_recebido

        total_processos = len(processos)
        ativos = sum(1 for p in processos if p.status == "Em Andamento")
        concluidos = sum(1 for p in processos if p.status == "Concluído")

        hoje = date.today()
        limite_urgencia = hoje + timedelta(days=30)
        prazos_lista = []
        prazos_vencidos = 0

        for p in processos:
            if p.data_prazo:
                if p.data_prazo < hoje and p.status != "Concluído":
                    prazos_vencidos += 1
                elif hoje <= p.data_prazo <= limite_urgencia and p.status != "Concluído":
                    dias_restantes = (p.data_prazo - hoje).days
                    prazos_lista.append({
                        "numero": p.numero,
                        "cliente": p.cliente,
                        "data": p.data_prazo,
                        "dias_restantes": dias_restantes
                    })
        
        prazos_lista.sort(key=lambda x: x["dias_restantes"])
        status_distribuicao = {}
        for p in processos:
            status_distribuicao[p.status] = status_distribuicao.get(p.status, 0) + 1

        return {
            "total": total_processos,
            "ativos": ativos,
            "concluidos": concluidos,
            "vencidos": prazos_vencidos,
            "proximos_prazos": prazos_lista,
            "grafico_status": status_distribuicao,
            "total_honorarios": total_honorarios,
            "total_recebido": total_recebido,
            "total_pendente": total_pendente
        }

@app.post("/ia/extrair-dados")
async def extrair_dados_pdf(arquivo: UploadFile = File(...)):
    """
    Recebe um PDF, extrai o texto e pede ao Gemini para formatar como JSON
    para preenchimento automático de formulário.
    """
    try:
        #Ler o PDF
        pdf_reader = PdfReader(arquivo.file)
        texto_completo = ""
        # Lê apenas as primeiras 5 páginas para economizar tokens e ser mais rápido
        for i, page in enumerate(pdf_reader.pages):
            if i > 5: break
            texto_completo += page.extract_text()

        prompt = f"""
        Aja como um assistente jurídico. Analise o texto abaixo extraído de um processo judicial.
        Extraia as seguintes informações e retorne APENAS um objeto JSON (sem ```json no inicio):
        
        1. "numero_processo": O número do processo (formato CNJ se houver).
        2. "cliente": O nome da parte que parece ser o nosso cliente (ou Autor).
        3. "contra_parte": O nome da outra parte (Réu).
        4. "data_prazo": Uma data sugerida para o próximo prazo no formato YYYY-MM-DD. Se não achar, use a data de hoje.
        
        Texto do processo:
        {texto_completo}
        """

        # 3. Chamar a IA (SINTAXE NOVA CORRIGIDA)
        client = genai.Client(api_key=chave_secreta)

        # Na biblioteca nova, chamamos client.models.generate_content
        response = client.models.generate_content(
            model="models/gemini-3-flash-preview", 
            contents=prompt
        )

        resposta_texto = response.text.replace("```json", "").replace("```", "").strip()
        dados_json = json.loads(resposta_texto)

        return dados_json
    
    except Exception as e:
        print(f"Erro na extração: {e}")
        raise HTTPException(status_code=500, detail="Não foi possível extrair dados do PDF.")

@app.post("/processos/{processo_id}/chat")
def chat_com_processo(
    processo_id: int,
    dados: dict = (Body(...)),
    token: str = Depends(oauth2_scheme)
):
    email_user = verificar_token(token)

    with Session(engine) as session:
        # 1. Busca usuário e processo
        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()
        processo = session.get(Processo, processo_id)

        # 2. Validações de Segurança
        if not processo:
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        
        if processo.usuario_id != usuario.id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para acessar este processo.")
        
        if not processo.arquivo_pdf:
            raise HTTPException(status_code=400, detail="Este processo não tem PDF anexado para ler.")

        texto_pdf = ''
        try:
            
            response = s3_client.get_object(Bucket=os.getenv("AWS_BUCKET_NAME"), Key=processo.arquivo_pdf)

            arquivo_memoria = io.BytesIO(response['Body'].read())

            pdf_reader = PdfReader(arquivo_memoria)

            for i, page in enumerate(pdf_reader.pages):
                if i > 20: break
                texto_pdf += page.extract_text()

        except Exception as e:
            print(f"Erro ao ler PDF: {e}")
            raise HTTPException(status_code=500, detail="Erro ao baixar ou ler o arquivo PDF da nuvem.")
        
        pergunta = dados.get("pergunta")
        prompt_sistema = f"""
        Você é um assistente jurídico. Responda com base no texto abaixo.
        --- TEXTO DO PROCESSO ---
        {texto_pdf}
        --- FIM ---
        Pergunta: {pergunta}
        """

        try:

            client = genai.Client(api_key=chave_secreta)
            response = client.models.generate_content(
                model="models/gemini-3-flash-preview",
                contents=prompt_sistema
            )
            return {"resposta": response.text}
        except Exception as e:
            print(f"Erro na IA: {e}")
            raise HTTPException(status_code=500, detail="Erro ao processar resposta da IA.")

@app.post("/financeiro")
def criar_lancamento(lancamento: Financeiro, token: str = Depends(oauth2_scheme)):
    email_user = verificar_token(token)
    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()
        
        processo = session.get(Processo, lancamento.processo_id)
        if not processo or processo.usuario_id != usuario.id:
            raise HTTPException(status_code=404, detail="Processo não encontrado")

        lancamento.usuario_id = usuario.id

        if isinstance(lancamento.data_pagamento, str):
            lancamento.data_pagamento = date.fromisoformat(str(lancamento.data_pagamento))

        session.add(lancamento)
        session.commit()
        session.refresh(lancamento)
        return lancamento

@app.get("/processos/{processo_id}/financeiro")
def listar_financeiro_processo(processo_id: int, token: str = Depends(oauth2_scheme)):
    email_user = verificar_token(token)
    
    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email_user)).first()

        statement = select(Financeiro).where(
            Financeiro.processo_id == processo_id, 
            Financeiro.usuario_id == usuario.id
        )

        results = session.exec(statement).all()
        return results

def enviar_email_alerta(destinatario, processo_numero, cliente, dias_restantes):
    remetente = os.getenv("EMAIL_USER")
    senha = os.getenv("EMAIL_PASS")

    if not remetente or not senha:
        print("⚠️ Configuração de e-mail não encontrada. Pulei o envio.")
        return

    assunto = f"⚠️ ALERTA: Prazo vencendo - Processo {processo_numero}"
    corpo = f"""
    Olá, Doutor(a)!
    
    Este é um aviso automático do seu Sistema Jurídico.
    
    O processo do cliente **{cliente}** (Nº {processo_numero})
    vence em **{dias_restantes} dias**.
    
    Por favor, verifique o sistema para tomar as providências.
    """

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        text = msg.as_string()
        server.sendmail(remetente, destinatario, text)
        server.quit()
        print(f"📧 E-mail enviado para {destinatario}")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

def verificar_prazos_diarios():
    print("⏰ Robô iniciado: Verificando prazos...")

    with Session(engine) as session:
        hoje = date.today()
        data_alvo = hoje + timedelta(days=2) # Daqui a 2 dias

        processos = session.exec(select(Processo).where(Processo.data_prazo == data_alvo)).all()

        if not processos:
            print("✅ Nenhum prazo crítico para hoje.")
            return

        for p in processos:
            # Precisamos do e-mail do advogado dono do processo
            usuario = session.get(Usuario, p.usuario_id)
            if usuario:
                enviar_email_alerta(
                    destinatario=usuario.email,
                    processo_numero=p.numero,
                    cliente=p.cliente,
                    dias_restantes=2
                )

@app.on_event('startup')
def iniciar_agendador():
    scheduler = BackgroundScheduler()

    # Configura para rodar todo dia às 08:00 da manhã (Horário do Servidor)
    # Dica: O servidor do Render usa horário UTC (então 11:00 UTC = 08:00 Brasil)
    scheduler.add_job(verificar_prazos_diarios, 'cron', hour=11, minute=0)

    scheduler.start()
    print("🤖 Robô de Prazos ativado e agendado!")

# Rota só para testar se o e-mail chega (pode apagar depois)
@app.get("/teste-email")
def teste_email_manual():
    verificar_prazos_diarios()
    return {"mensagem": "Robô forçado manualmente! Verifique o console do Render e seu e-mail."}