import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv # Importar dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Pega a URL. Se não existir, usa SQLite como fallback seguro
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# CORREÇÃO PARA O NEON/RENDER:
# O SQLAlchemy removeu suporte a 'postgres://', precisa ser 'postgresql://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configura argumentos específicos
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True, # Mantém a conexão viva (ótimo para nuvem)
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()