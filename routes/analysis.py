from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Imports dos módulos do projeto
import schemas.schemas as schemas
import security
from db import get_db
from models.models import User

# Imports dos novos módulos de análise
from analysis.data_sources import consultar_serasa, consultar_banco_central_scr
from analysis.scoring import calculate_credit_score
from analysis.decision import make_decision

router = APIRouter(
    prefix="/api",
    tags=["Análise de Crédito"],
    dependencies=[Depends(security.get_current_active_user)]
)

@router.post("/analise-credito", response_model=schemas.CreditAnalysisResponse, summary="Executar análise de crédito")
def analisar_credito(
    payload: schemas.CreditAnalysisRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_active_user)
):
    """
    Executa uma análise de crédito completa para o usuário autenticado.
    """
    print(f"\n--- INICIANDO ANÁLISE DE CRÉDITO PARA USUÁRIO: {current_user.email} ---")

    if current_user.cpf != payload.cpf:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é permitido solicitar análise para outro CPF."
        )

    perfil = current_user.perfil
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Perfil de usuário não encontrado. Crie um perfil antes de solicitar a análise."
        )

    try:
        serasa_data = consultar_serasa(perfil)
        bacen_data = consultar_banco_central_scr(perfil)
        score = calculate_credit_score(serasa_data, bacen_data, perfil, payload)
        decision = make_decision(score, payload, perfil)
        
        print(f"DECISÃO FINAL: {decision.decision} - {decision.message}")
        print("--- FIM DA ANÁLI-SE ---\n")
        
        return decision
    except Exception as e:
        print(f"ERRO INESPERADO: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao processar a análise.")

