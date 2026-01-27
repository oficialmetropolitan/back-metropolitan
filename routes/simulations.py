from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import schemas.simulacao as schemas 
import security
from db import get_db
from models.models import Simulacao, User, Lead # Certifique-se de ter criado a classe Lead no models.py

router = APIRouter(prefix="/api/simulacoes", tags=["Simulações"])

# Função de lógica interna (mantida e centralizada)
def calcular_valores_simulacao(valor_desejado: float, prazo_meses: int, tipo_emprestimo: str):
    """
    Calcula os valores de empréstimo com base na Tabela Price, 
    conforme identificado no Simulador Metrobank.
    """
    # 1. Definição da taxa de juros mensal
    taxa_juros_mensal = 0.02  # Taxa padrão (2%)
    if tipo_emprestimo == 'imovel-garantia':
        taxa_juros_mensal = 0.01
    elif tipo_emprestimo == 'veiculo-garantia':
        taxa_juros_mensal = 0.015

    # 2. Cálculo da Parcela (Fórmula da Tabela Price)
    # PMT = PV * [i * (1 + i)^n] / [(1 + i)^n - 1]
    i = taxa_juros_mensal
    n = prazo_meses
    pv = valor_desejado

    if i > 0:
        valor_parcela = pv * (i * (1 + i)**n) / ((1 + i)**n - 1)
    else:
        valor_parcela = pv / n

    # 3. Cálculo dos totais
    valor_total = valor_parcela * n
    juros_total = valor_total - pv
    
    return {
        "valor_parcela": round(valor_parcela, 2),
        "valor_total": round(valor_total, 2),
        "juros_total": round(juros_total, 2),
        "taxa_aplicada": f"{i*100:.2f}%",
        "prazo_meses": n
    }




@router.post("/calcular-imediato")
def calcular_imediato(payload: schemas.SimulacaoPublicaRequest):
    return calcular_valores_simulacao(
        payload.valor_desejado,
        payload.prazo_meses,
        payload.tipo_emprestimo,
        
    )

@router.post("/salvar-lead", status_code=201)
def salvar_lead_e_simulacao(
    payload: schemas.LeadComSimulacaoCreate,
    db: Session = Depends(get_db)
):
    # 1. Lead (Busca ou cria)
    lead = db.query(Lead).filter(Lead.email == payload.email).first()
    if not lead:
        lead = Lead(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            data_nascimento=payload.data_nascimento,
            cidade=payload.cidade,
            estado=payload.estado
        )
        db.add(lead)
        db.flush()

    # 2. Simulação (Salvando exatamente o que veio do front)
 
    simulacao = Simulacao(
        valor_desejado=payload.valor_desejado,
        prazo_meses=payload.prazo_meses,
        tipo_emprestimo=payload.tipo_emprestimo,
        motivo_emprestimo=payload.motivo_emprestimo,
      
        dados_especificos={
            "entrada": payload.dados_entrada,
            "resultado": payload.resultado_simulacao
        },
    
        valor_parcela=payload.resultado_simulacao.get("valor_parcela"),
        valor_total=payload.resultado_simulacao.get("valor_total"),
        juros_total=payload.resultado_simulacao.get("juros_total"),
        lead_id=lead.id,
        status="pendente"
    )

    db.add(simulacao)
    db.commit()
    db.refresh(simulacao)

    return simulacao

@router.post("/", response_model=schemas.SimulacaoOut, status_code=status.HTTP_201_CREATED)
def criar_simulacao_logada(
    payload: schemas.SimulacaoCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_active_user)
):
    """Rota para quando o usuário já está logado no sistema Metropolitan."""
    calculos = calcular_valores_simulacao(
        payload.valor_desejado, payload.prazo_meses, payload.tipo_emprestimo
    )
    
    nova_simulacao = Simulacao(
        **payload.model_dump(),
        **calculos,
        user_id=current_user.id,
        status="pendente"
    )
    
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
# 3. ROTAS ADMINISTRATIVAS (FINANCEIRO)
# ==========================================

@router.get("/admin/todas", response_model=List[schemas.SimulacaoOut])
def admin_listar_tudo(
    db: Session = Depends(get_db), 
    current_admin: User = Depends(security.get_current_admin)
):
    return db.query(Simulacao).all()

@router.patch("/admin/{simulacao_id}/status", response_model=schemas.SimulacaoOut)
def admin_atualizar_status(
    simulacao_id: int,
    payload: schemas.SimulacaoUpdateStatus,
    db: Session = Depends(get_db),
    current_admin: User = Depends(security.get_current_admin)
):
    simulacao = db.query(Simulacao).filter(Simulacao.id == simulacao_id).first()
    if not simulacao:
        raise HTTPException(status_code=404, detail="Simulação não encontrada")
    
    simulacao.status = payload.status
    db.commit()
    db.refresh(simulacao)
    return simulacao


@router.post("/vincular-simulacoes-pendentes")
def vincular_simulacoes(
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_active_user)
):

    simulacoes_pendentes = db.query(Simulacao).join(Lead).filter(
        Lead.email == current_user.email,
        Simulacao.user_id == None
    ).all()

    if not simulacoes_pendentes:
        return {"message": "Nenhuma simulação pendente para vincular."}


    for sim in simulacoes_pendentes:
        sim.user_id = current_user.id
    
    db.commit()
    return {"message": f"{len(simulacoes_pendentes)} simulações vinculadas com sucesso."}