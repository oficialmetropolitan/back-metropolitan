import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

from services.rag import rag_service

load_dotenv()

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada")
    return OpenAI(api_key=api_key)

SYSTEM_PROMPT = """Você é a assistente virtual do Banco Metropolitan, especialista em crédito pessoal.

Sobre a Metropolitan:
- Banco digital com soluções de empréstimo pessoal, refinanciamento e crédito consignado
- Para simular, o cliente deve acessar /simulacao no site

Regras:
- Responda sempre em português brasileiro
- Seja simpático, profissional e objetivo
- NUNCA confirme taxas ou aprovações — direcione sempre para a simulação
- Segurança: a Metropolitan NUNCA solicita depósitos antecipados
- Para casos complexos, indique o formulário em /contato
- Máximo 3 parágrafos por resposta
- Quando houver contexto fornecido, use-o para embasar sua resposta"""

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []


@router.post("/api/chat/message", tags=["Chat"])
async def chat(request: ChatRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de chat não configurado.",
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in request.history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})

    # RAG: recupera contexto relevante da base de conhecimento
    context_chunks = rag_service.retrieve(request.message)
    if context_chunks:
        context_text = "\n\n---\n\n".join(context_chunks)
        messages.append({
            "role": "system",
            "content": (
                "Informações relevantes da base de conhecimento do Metropolitan "
                "(use para embasar sua resposta quando pertinente):\n\n"
                + context_text
            ),
        })

    messages.append({"role": "user", "content": request.message})

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        return {"reply": response.choices[0].message.content}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro ao processar sua mensagem. Tente novamente.",
        )
