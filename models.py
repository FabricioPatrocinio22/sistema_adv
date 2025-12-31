from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import date
from sqlalchemy import Text

class UsuarioCreate(SQLModel):
    email: str
    senha: str

class Processo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    numero: str = Field(index=True, unique=True) # Adicionamos unique aqui também no nível do banco!
    cliente: str
    contra_parte: str
    status: str = "Em Andamento"
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    data_prazo: Optional[date] = None
    arquivo_pdf: Optional[str] = None
    resumo_ia: Optional[str] = Field(default=None, sa_type=Text)

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    senha_hash: str
    secret_2fa: Optional[str] = None  # Para o Google Authenticator (TOTP)
    is_2fa_enabled: bool = False      # Controle de ativação