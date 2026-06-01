import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Importe seus módulos locais
from db import get_db
from models.models import User

# --- Configuração de Segurança ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "a_secret_key_super_strong_for_dev_purpose")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def hash_password(password: str):
    """Gera o hash de uma senha."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verifica se a senha fornecida corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria um novo token de acesso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Lógica de Dependências de Autenticação ---

def get_user_by_email(db: Session, email: str):
    """Busca um usuário pelo e-mail."""
    return db.query(User).filter(User.email == email).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decodifica o token, valida o usuário e retorna o objeto User."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Verifica se o usuário obtido pelo token está ativo."""
    # Você pode adicionar lógicas de verificação aqui (ex: usuário banido)
    return current_user


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception

def get_current_admin(current_user: User = Depends(get_current_active_user)):
    """Verifica se o usuário logado é um administrador."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Esta área é restrita a administradores."
        )
    return current_user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    
    # 🛡️ PROTEÇÃO 1: Se a rota não enviou um 'type', assumimos que é um token de Login normal ('access')
    if "type" not in to_encode:
        to_encode["type"] = "access"
        
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 🛡️ PROTEÇÃO 2: Adicionamos o parâmetro 'expected_type' com padrão "access"
def verify_token(token: str, credentials_exception, expected_type: str = "access"):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type") # Lemos a etiqueta do token
        
        if email is None:
            raise credentials_exception
            
        # 🛡️ PROTEÇÃO 3: Se o cara mandou um token de 'access' pra resetar a senha, a gente barra!
        if token_type != expected_type:
            # Você pode até criar uma exceção customizada aqui se quiser ser mais específico no erro
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Tipo de token inválido. Esperado: {expected_type}, Recebido: {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return email
        
    except JWTError: # Mude para pyjwt.InvalidTokenError se estiver usando a biblioteca PyJWT
        raise credentials_exception