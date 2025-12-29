from sqlmodel import SQLModel, create_engine

sqlite_file_name = "advocacia.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True) # echo=True ajuda a ver o SQL no terminal

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)