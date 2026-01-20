import os
from sqlmodel import SQLModel, create_engine

# Tenta pegar o endereço do banco das Variáveis de Ambiente (Nuvem)
# Se não achar, usa o sqlite local (Seu PC)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///advocacia.db")

# Ajuste técnico: O Render às vezes devolve "postgres://", mas o Python quer "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# connect_args só é necessário para SQLite
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)