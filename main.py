import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import models
from db import engine
from routes import auth, users, profile, simulations, contact, chat, totp
from services.rag import rag_service

load_dotenv()

models.Base.metadata.create_all(bind=engine)

# Lê o ambiente (development / production)
ENV = os.getenv("ENV", "development")
IS_PROD = ENV == "production"

# Origins vindas do .env (separadas por vírgula) + fallback para localhost em dev
origins_env = os.getenv("ALLOWED_ORIGINS", "")
origins = [o.strip() for o in origins_env.split(",") if o.strip()]

if not IS_PROD:
    origins += [
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    rag_service.load()
    yield


app = FastAPI(
    title="API de Empréstimos e Clientes",
    description="Uma API para gerenciar clientes, perfis, simulações e análise de crédito.",
    version="1.1.0",
    lifespan=lifespan,
    # Desabilita /docs e /openapi.json em produção
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explícito, sem wildcard
    allow_headers=["Authorization", "Content-Type", "X-2FA-Session-Token"],
)

app.include_router(auth.router)
app.include_router(totp.router)
app.include_router(users.router)
app.include_router(profile.router)
app.include_router(simulations.router)
app.include_router(contact.router, tags=["Contato"])
app.include_router(chat.router)

@app.get("/health", tags=["Status"])
def health():
    return {"status": "ok"}