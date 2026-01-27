from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import Enum

class StatusSimulacao(str, Enum):
    PENDENTE = "pendente"
    EM_ANALISE = "em_analise"
    APOVADO = "aprovado"
    REPROVADO = "reprovado"

# Schema Base (Campos comuns)
class SimulacaoBase(BaseModel):
    valor_desejado: float
    prazo_meses: int
    motivo_emprestimo: str
    tipo_emprestimo: str
    dados_especificos: Optional[Dict[str, Any]] = None

# Para o cálculo imediato (não salva nada)
class SimulacaoPublicaRequest(BaseModel):
    valor_desejado: float
    prazo_meses: int
    tipo_emprestimo: str

# NOVO: Para criar o Lead junto com a Simulação (Passo de conversão)
class LeadComSimulacaoCreate(SimulacaoBase):
    full_name: str
    email: str
    phone: str
    data_nascimento: date
    cidade: str
    estado: str
    # Esses campos devem existir aqui para a rota conseguir ler
    dados_entrada: Dict[str, Any]      # O que o usuário preencheu
    resultado_simulacao: Dict[str, Any]
# Para usuários já logados
class SimulacaoCreate(SimulacaoBase):
    pass

class SimulacaoUpdateStatus(BaseModel):
    status: StatusSimulacao

# Resposta padrão da API
class SimulacaoOut(SimulacaoBase):
    id: int
    user_id: Optional[int] = None
    lead_id: Optional[int] = None
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