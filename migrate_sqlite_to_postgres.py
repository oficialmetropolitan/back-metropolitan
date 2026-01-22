import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajuste estes imports para os seus modelos
from models.models import User, PerfilUsuario, Simulacao
from db import Base  # mesmo Base do projeto
from dotenv import load_dotenv
load_dotenv()

SQLITE_URL = "sqlite:///./app.db"
POSTGRES_URL = os.getenv("DATABASE_URL")  # defina no ambiente

src_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
dst_engine = create_engine(POSTGRES_URL, pool_pre_ping=True)

SrcSession = sessionmaker(bind=src_engine, autoflush=False, autocommit=False)
DstSession = sessionmaker(bind=dst_engine, autoflush=False, autocommit=False)

def copy_table(model):
    src = SrcSession()
    dst = DstSession()
    try:
        rows = src.query(model).all()
        for r in rows:
            # cria um novo objeto sem o estado de sessão
            data = {c.name: getattr(r, c.name) for c in model.__table__.columns}
            obj = model(**data)
            dst.merge(obj)  # merge evita duplicidade por PK
        dst.commit()
        print(f"Copiados {len(rows)} registros de {model.__tablename__}")
    finally:
        src.close()
        dst.close()

if __name__ == "__main__":
    # garante tabelas no destino
    Base.metadata.create_all(bind=dst_engine)

    for model in [User, PerfilUsuario, Simulacao]:
        copy_table(model)