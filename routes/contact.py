# routes/contact.py

import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

from dotenv import load_dotenv
load_dotenv()
# ---- Validação dos Dados de Entrada ----
class ContactSchema(BaseModel):
    nome: str
    email: EmailStr
    telefone: str | None = None
    assunto: str
    mensagem: str

# ---- Configuração do E-mail (Lendo do .env) ----
conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER = os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "False").lower() == 'true',
    MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "True").lower() == 'true',
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

router = APIRouter()

@router.post("/contact/send-email", status_code=status.HTTP_200_OK)
async def send_email(contact_data: ContactSchema, background_tasks: BackgroundTasks):
    """
    Endpoint para receber dados de um formulário de contato e enviar um e-mail.
    O envio é feito em background para não bloquear a resposta da API.
    """
    try:
        html_body = f"""
            <h1>Nova Mensagem do Formulário de Contato</h1>
            <p><strong>Nome:</strong> {contact_data.nome}</p>
            <p><strong>Email para resposta:</strong> {contact_data.email}</p>
            <p><strong>Telefone:</strong> {contact_data.telefone or "Não informado"}</p>
            <p><strong>Assunto:</strong> {contact_data.assunto}</p>
            <hr>
            <p><strong>Mensagem:</strong></p>
            <p>{contact_data.mensagem.replace('\n', '<br>')}</p>
        """

        message = MessageSchema(
            subject=f"Contato via Site: {contact_data.assunto}",
            recipients=["suporte.metropolitan@bancometropolitan.com.br"], # E-mail que vai RECEBER a mensagem
            body=html_body,
            subtype="html",
            reply_to=[contact_data.email]
        )

        fm = FastMail(conf)
        
        # Envia o e-mail em background para não travar a API
        background_tasks.add_task(fm.send_message, message)

        return {"message": "Mensagem recebida e agendada para envio."}

    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao tentar enviar o e-mail."
        )