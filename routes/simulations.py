from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import schemas.simulacao as schemas 
import security
from db import get_db
from models.models import Simulacao, User 

router = APIRouter(prefix="/api/simulacoes", tags=["Simulações"])

def calcular_valores_simulacao(valor_desejado: float, prazo_meses: int, tipo_emprestimo: str):
    taxa_juros_mensal = 0.02 
    if tipo_emprestimo == 'imovel-garantia': taxa_juros_mensal = 0.01
    elif tipo_emprestimo == 'veiculo-garantia': taxa_juros_mensal = 0.015

    juros_total = (valor_desejado * taxa_juros_mensal) * prazo_meses
    valor_total = valor_desejado + juros_total
    valor_parcela = valor_total / prazo_meses
    
    return {
        "valor_parcela": round(valor_parcela, 2),
        "valor_total": round(valor_total, 2),
        "juros_total": round(juros_total, 2)
    }

# ==========================================
# ROTAS DO USUÁRIO (CLIENTE)
# ==========================================

@router.post("/", response_model=schemas.SimulacaoOut, status_code=status.HTTP_201_CREATED)
def criar_simulacao(
    payload: schemas.SimulacaoCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_active_user)
):
    simulacao_data = payload.model_dump() 
    calculos = calcular_valores_simulacao(
        payload.valor_desejado, payload.prazo_meses, payload.tipo_emprestimo
    )
    
    simulacao_data.update(calculos)
    nova_simulacao = Simulacao(**simulacao_data, user_id=current_user.id, status="pendente")
    
    db.add(nova_simulacao)
    db.commit()
    db.refresh(nova_simulacao)
    return nova_simulacao

@router.get("/me", response_model=List[schemas.SimulacaoOut])
def listar_minhas_simulacoes(
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_active_user)
):
    return db.query(Simulacao).filter(Simulacao.user_id == current_user.id).all()

# ==========================================
# ROTAS DO FINANCEIRO (ADMIN)
# ==========================================

@router.get("/admin/todas", response_model=List[schemas.SimulacaoOut])
def admin_listar_tudo(
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_active_user)
):
    # Aqui você deveria checar se o current_user.is_admin == True
    # Por enquanto, vamos listar tudo
    return db.query(Simulacao).all()

@router.patch("/admin/{simulacao_id}/status", response_model=schemas.SimulacaoOut)
def admin_atualizar_status(
    simulacao_id: int,
    payload: schemas.SimulacaoUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    Rota para a colega do financeiro aprovar ou reprovar
    """
    simulacao = db.query(Simulacao).filter(Simulacao.id == simulacao_id).first()
    
    if not simulacao:
        raise HTTPException(status_code=404, detail="Simulação não encontrada")
    
    simulacao.status = payload.status
    db.commit()
    db.refresh(simulacao)
    return simulacao

@router.get("/admin/todas", response_model=List[schemas.SimulacaoOut])
def admin_listar_tudo(
    db: Session = Depends(get_db), 
    current_admin: User = Depends(security.get_current_admin) # <--- BLOQUEIO AQUI
):
    """Apenas administradores podem ver todas as simulações do banco."""
    return db.query(Simulacao).all()


@router.patch("/admin/{simulacao_id}/ajustar", response_model=schemas.SimulacaoOut)
def admin_ajustar_valores(
    simulacao_id: int,
    payload: schemas.SimulacaoAjusteFinanceiro,
    db: Session = Depends(get_db),
    current_admin: User = Depends(security.get_current_admin)
):
    simulacao = db.query(Simulacao).filter(Simulacao.id == simulacao_id).first()
    if not simulacao:
        raise HTTPException(status_code=404, detail="Simulação não encontrada")


    simulacao.valor_parcela = payload.valor_parcela
    simulacao.valor_total = payload.valor_total
    simulacao.juros_total = payload.juros_total
    
    db.commit()
    db.refresh(simulacao)
    return simulacao