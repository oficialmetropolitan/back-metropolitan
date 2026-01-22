# routes/auth.py

from datetime import timedelta, datetime, timezone
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr # --- NOVO ---

# Seus imports existentes
import schemas.user as schemas
import security
from db import get_db
from models.models import User

# --- NOVO: Imports para envio de e-mail ---
from fastapi_mail import FastMail, MessageSchema
# Reutilizando a configuração de e-mail do seu arquivo de contato
from routes.contact import conf 



router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticação"]
)

class ForgotPasswordPayload(BaseModel):
    email: EmailStr

class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str


# --- NOVO: Schema Pydantic para a verificação ---
class VerificationPayload(BaseModel):
    email: EmailStr
    code: str

class ResendVerificationPayload(BaseModel):
    email: EmailStr

# --- NOVA ROTA: Endpoint para reenviar o código de verificação ---
@router.post("/resend-verification", status_code=status.HTTP_200_OK, summary="Reenviar código de verificação")
def resend_verification_code(
    payload: ResendVerificationPayload,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    user = security.get_user_by_email(db, email=payload.email)

    if not user:
        # Nota: Não informamos que o usuário não existe por segurança, para evitar enumeração de e-mails.
        # Apenas retornamos uma resposta de sucesso genérica.
        return {"message": "Se um usuário com este e-mail existir, um novo código será enviado."}

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já foi verificado."
        )

    # Gera um novo código e uma nova data de expiração
    new_code = create_verification_code()
    new_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    user.verification_code = new_code
    user.verification_expires_at = new_expires_at
    db.commit()

    # Envia o novo código por e-mail em background
    html_body = f"""
        <div style="font-family: Arial, sans-serif; background-color: #f4f4f7; padding: 20px;">
    <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden;">
        
        <div style="padding: 20px; text-align: center; border-bottom: 1px solid #e2e8f0;">
            <img src="https://res.cloudinary.com/daeczbv7v/image/upload/v1758805746/Metropolitan_logo_semfundo_as8xh0.png" 
                 alt="Metropolitan Logo" 
                 style="width: 140px; height: auto;"/>
        </div>

        <div style="padding: 30px; line-height: 1.6; color: #333;">
            <h2 style="font-size: 20px; color: #1a202c; margin-top: 0;">Seu Código de Verificação</h2>
            <p style="font-size: 16px;">Olá <strong>{novo_usuario.full_name}</strong>,</p>
            <p style="font-size: 16px;">Para ativar sua conta na <strong>Metropolitan</strong>, utilize o código de verificação abaixo:</p>
            
            <div style="background-color: #f7fafc; padding: 20px; text-align: center; border-radius: 6px; margin: 25px 0;">
                <p style="font-size: 32px; letter-spacing: 8px; margin: 0; color: #2d3748; font-weight: bold;">{verification_code}</p>
            </div>
            
            <p style="font-size: 14px; color: #555;">Este código expira em <strong>15 minutos</strong>. Por segurança, não o compartilhe com ninguém.</p>
        </div>

        <div style="padding: 20px; font-size: 12px; color: #718096; text-align: center; background-color: #f7fafc; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0;">© 2025 Metropolitan Ltd. Todos os direitos reservados.</p>
            <p style="margin: 5px 0 0 0;">Você recebeu esta mensagem como parte do seu processo de cadastro.</p>
        </div>
    </div>
</div>
    """
    message = MessageSchema(
        subject="Seu Novo Código de Verificação - Metropolitan",
        recipients=[user.email],
        body=html_body,
        subtype="html"
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

    return {"message": "Se um usuário com este e-mail existir, um novo código será enviado."}


# --- NOVO: Função para gerar o código (movida para cá) ---
def create_verification_code(length: int = 6) -> str:
    """Gera um código de verificação numérico aleatório."""
    return "".join(random.choices(string.digits, k=length))


# Rota de Login agora verifica se o e-mail foi confirmado ---
@router.post("/token")
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = security.get_user_by_email(db, email=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox for the verification code."
        )
  
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "is_admin": user.is_admin 
    }


# --- ALTERADO: Rota de Cadastro agora envia o e-mail de verificação ---
@router.post("/clientes", status_code=status.HTTP_201_CREATED, summary="Criar um novo cliente")
def criar_cliente(payload: schemas.UserCreate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    # Suas validações de e-mail e CPF continuam as mesmas
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    if db.query(User).filter(User.cpf == payload.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")

    # Geração do código e data de expiração
    verification_code = create_verification_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15) 

    hashed_pwd = security.hash_password(payload.password)
    
    # Cria o usuário com o status de verificação como Falso
    novo_usuario = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower().strip(),
        phone=payload.phone.strip(),
        cpf=payload.cpf.strip(),
        password_hash=hashed_pwd,
        # --- NOVOS CAMPOS ---
        is_verified=False,
        verification_code=verification_code,
        verification_expires_at=expires_at
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    # --- LÓGICA DE ENVIO DE E-MAIL ---
    html_body = f""" 
        <div style="font-family: Arial, sans-serif; background-color: #f4f4f7; padding: 20px;">
    <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden;">
        
        <div style="padding: 20px; text-align: center; border-bottom: 1px solid #e2e8f0;">
            <img src="https://res.cloudinary.com/daeczbv7v/image/upload/v1758805746/Metropolitan_logo_semfundo_as8xh0.png" 
                 alt="Metropolitan Logo" 
                 style="width: 140px; height: auto;"/>
        </div>

        <div style="padding: 30px; line-height: 1.6; color: #333;">
            <h2 style="font-size: 20px; color: #1a202c; margin-top: 0;">Seu Código de Verificação</h2>
            <p style="font-size: 16px;">Olá <strong>{novo_usuario.full_name}</strong>,</p>
            <p style="font-size: 16px;">Para ativar sua conta na <strong>Metropolitan</strong>, utilize o código de verificação abaixo:</p>
            
            <div style="background-color: #f7fafc; padding: 20px; text-align: center; border-radius: 6px; margin: 25px 0;">
                <p style="font-size: 32px; letter-spacing: 8px; margin: 0; color: #2d3748; font-weight: bold;">{verification_code}</p>
            </div>
            
            <p style="font-size: 14px; color: #555;">Este código expira em <strong>15 minutos</strong>. Por segurança, não o compartilhe com ninguém.</p>
        </div>

        <div style="padding: 20px; font-size: 12px; color: #718096; text-align: center; background-color: #f7fafc; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0;">© 2025 Metropolitan Ltd. Todos os direitos reservados.</p>
            <p style="margin: 5px 0 0 0;">Você recebeu esta mensagem como parte do seu processo de cadastro.</p>
        </div>
    </div>
</div>
        """
    message = MessageSchema(
        subject="Seu Código de Verificação - Metropolitan",
        recipients=[novo_usuario.email],
        body=html_body,
        subtype="html"
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

    return {"message": "Cliente criado com sucesso. Um código foi enviado para o seu e-mail para verificação."}


@router.post("/verify", status_code=status.HTTP_200_OK, summary="Verificar e-mail do usuário")
def verify_user_email(payload: VerificationPayload, db: Session = Depends(get_db)):
    user = security.get_user_by_email(db, email=payload.email)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já verificado.")

    if user.verification_code != payload.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código de verificação inválido.")
    
   
    # Agora estamos comparando duas datas que são "cientes" do fuso horário UTC
    if datetime.now(timezone.utc) > user.verification_expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código de verificação expirado.")

    # Se tudo estiver correto, verifica o usuário
    user.is_verified = True
    user.verification_code = None
    user.verification_expires_at = None
    db.commit()

    return {"message": "E-mail verificado com sucesso! Você já pode fazer login."}


# ------redefinir senha  -----------

@router.post("/forgot-password", status_code=status.HTTP_200_OK, summary="Solicitar redefinição de senha")
def request_password_reset(
    payload: ForgotPasswordPayload,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    user = security.get_user_by_email(db, email=payload.email)
   

    if user:
        # Cria um token de curta duração (ex: 15 minutos)
        expires_delta = timedelta(minutes=15)
        reset_token = security.create_access_token(
            data={"sub": user.email, "type": "reset"}, expires_delta=expires_delta
        )
        
        reset_link = f"http://localhost:8080/redefinir-senha?token={reset_token}"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; background-color: #f4f4f7; padding: 20px;">
    <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden;">
        
        <div style="padding: 20px; text-align: center; border-bottom: 1px solid #e2e8f0;">
            <img src="https://res.cloudinary.com/daeczbv7v/image/upload/v1758805746/Metropolitan_logo_semfundo_as8xh0.png" 
                 alt="Metropolitan Logo" 
                 style="width: 140px; height: auto;"/>
        </div>

        <div style="padding: 30px; line-height: 1.6; color: #333;">
            <h2 style="font-size: 20px; color: #1a202c; margin-top: 0;">Redefinição de Senha</h2>
            <p style="font-size: 16px;">Olá <strong>{user.full_name}</strong>,</p>
            <p style="font-size: 16px;">Recebemos uma solicitação para redefinir sua senha. Clique no botão abaixo para criar uma nova:</p>
            <div style="text-align: center; margin: 25px 0;">
                <a href="{reset_link}" style="background-color: #4a3aff; color: #ffffff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
                    Redefinir Minha Senha
                </a>
            </div>
            
            <p style="font-size: 14px; color: #555;">Se você não solicitou isso, pode ignorar este e-mail com segurança.</p>
            <p style="font-size: 14px; color: #555;">Este link é válido por <strong>15 minutos</strong>.</p>
        </div>

        <div style="padding: 20px; font-size: 12px; color: #718096; text-align: center; background-color: #f7fafc; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0;">© 2025 Metropolitan Ltd. Todos os direitos reservados.</p>
            <p style="margin: 5px 0 0 0;">Você recebeu esta mensagem porque uma redefinição de senha foi solicitada.</p>
        </div>
    </div>
</div>
"""
        message = MessageSchema(
            subject="Redefinição de Senha - Metropolitan",
            recipients=[user.email],
            body=html_body,
            subtype="html"
        )
        fm = FastMail(conf)
        background_tasks.add_task(fm.send_message, message)

    return {"message": "Se uma conta com este e-mail existir, um link para redefinição de senha foi enviado."}


@router.post("/reset-password", status_code=status.HTTP_200_OK, summary="Redefinir a senha")
def reset_password(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = security.verify_token(payload.token, credentials_exception)
    user = security.get_user_by_email(db, email=email)

    if not user:
        raise credentials_exception # Não deveria acontecer se o token for válido, mas é uma segurança extra

    # Atualiza a senha do usuário
    new_hashed_password = security.hash_password(payload.new_password)
    user.password_hash = new_hashed_password
    db.commit()

    return {"message": "Sua senha foi redefinida com sucesso!"}