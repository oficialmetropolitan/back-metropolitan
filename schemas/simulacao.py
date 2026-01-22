from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class StatusSimulacao(str, Enum):
    PENDENTE = "pendente"
    EM_ANALISE = "em_analise"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"

class SimulacaoBase(BaseModel):
    valor_desejado: float
    prazo_meses: int
    motivo_emprestimo: str
    tipo_emprestimo: str
    dados_especificos: Dict[str, Any] 

class SimulacaoCreate(SimulacaoBase):
    pass

# Schema para a colega do financeiro usar
class SimulacaoUpdateStatus(BaseModel):
    status: StatusSimulacao

class SimulacaoOut(SimulacaoBase):
    id: int
    user_id: int
    criado_em: datetime
    status: str
    valor_parcela: float
    valor_total: float
    juros_total: float

    class Config:
        from_attributes = True 

class SimulacaoAjusteFinanceiro(BaseModel):
    valor_parcela: float
    valor_total: float
    juros_total: float