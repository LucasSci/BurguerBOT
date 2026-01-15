from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base

# Cria um arquivo chamado 'burguer.db' na raiz do projeto
DATABASE_URL = "sqlite:///./burguer.db"

# Engine de conexão
engine = create_engine(DATABASE_URL, echo=False) # echo=True mostra o SQL no terminal (bom pra debug)

# Sessão (é o que usamos para fazer queries)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def criar_tabelas():
    # Cria todas as tabelas definidas no models.py
    Base.metadata.create_all(bind=engine)

def get_db():
    # Função utilitária para pegar uma sessão de banco
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()