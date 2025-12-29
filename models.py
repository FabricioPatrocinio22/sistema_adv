from typing import Optional
from sqlmodel import Field, SQLModel

class Processo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    numero: str = Field(index=True, unique=True) # Adicionamos unique aqui também no nível do banco!
    cliente: str
    contra_parte: str
    status: str = "Em Andamento"

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    senha_hash: str
    secret_2fa: Optional[str] = None  # Para o Google Authenticator (TOTP)
    is_2fa_enabled: bool = False      # Controle de ativação