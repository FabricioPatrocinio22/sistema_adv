import email
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

# CHAVE_MESTRA: Use uma frase secreta e complexa. Nunca a revele!
SECRET_KEY = "sua_chave_secreta_super_segura_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def criar_token_acesso(dados: dict):
    """Gera o 'crachá' digital (JWT)"""
    a_copiar = dados.copy()
    expiracao = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    a_copiar.update({"exp": expiracao})
    return jwt.encode(a_copiar, SECRET_KEY, algorithm=ALGORITHM)

# Configuramos o algoritmo de criptografia (bcrypt é o padrão de mercado)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Para:
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b")

def gerar_hash_senha(senha: str) -> str:
    """Transforma a senha pura em um hash seguro."""
    return pwd_context.hash(senha)

def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    """Verifica se a senha digitada condiz com o hash salvo."""
    return pwd_context.verify(senha_pura, senha_hash)

# Isso diz ao FastAPI onde o usuário deve ir para se autenticar
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verificar_token(token: str):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        print(f"Erro na validação do token: {e}") # Isso vai aparecer no seu terminal!
        return None

import pyotp

def gerar_segredo_2fa():
    """Gera uma chave aleatória que será o segredo do Google Authenticator."""
    return pyotp.random_base32()

def verificar_codigo_2fa(segredo: str, codigo: str):
    """Verifica se o código de 6 dígitos digitado pelo usuário é válido agora."""
    totp = pyotp.TOTP(segredo)
    return totp.verify(codigo)