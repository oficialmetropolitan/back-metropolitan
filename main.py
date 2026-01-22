from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importe seus modelos e o engine do DB
from models import models
from db import engine

# Importe os roteadores
from routes import auth, users, profile, simulations, contact

# Cria as tabelas no banco de dados (se não existirem)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Empréstimos e Clientes",
    description="Uma API para gerenciar clientes, perfis, simulações e análise de crédito.",
    version="1.1.0"
)

# --- CORREÇÃO APLICADA AQUI ---
# Adicionamos a porta 8000, onde seu front-end está rodando.
origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "https://bancometropolitan.com.br",       # Seu domínio oficial
    "https://www.bancometropolitan.com.br",   # Seu domínio com www
    "http://bancometropolitan.com.br",        # Versão http (por precaução)
    "http://www.bancometropolitan.com.br",
    "https://front-metropolitan.vercel.app",
]

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Usamos a lista definida acima
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os roteadores na aplicação principal
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profile.router)
app.include_router(simulations.router)
app.include_router(contact.router, tags=["Contato"])

@app.get("/health", tags=["Status"])
def health():
    """Endpoint para verificar a saúde da API."""
    return {"status": "ok"}
