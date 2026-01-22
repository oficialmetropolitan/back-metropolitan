from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import date

# Request para criar um perfil de teste
class UserProfileCreate(BaseModel):
    full_name: str
    email: str
    phone: str
    cpf: str
    password: str # Senha em texto plano, vamos gerar o hash no backend
    renda_mensal: float
    possui_imovel: bool
    possui_veiculo: bool
    possui_restricao: bool
    data_admissao: date
    escolaridade: str

# Request para a análise
class CreditAnalysisRequest(BaseModel):
    cpf: str = Field(..., description="CPF do cliente para busca no banco de dados.", example="12345678900")
    requested_amount: float = Field(..., description="Valor do empréstimo solicitado.", example=10000.0)
    installments: int = Field(..., description="Número de parcelas.", example=24)

# Resposta da análise (inalterada)
class CreditAnalysisResponse(BaseModel):
    cpf: str
    decision: Literal["Aprovado", "Negado", "Análise Manual"]
    score: int
    message: str
    approved_amount: Optional[float] = None
    approved_installments: Optional[int] = None

# Modelos de Simulação (inalterados)
class SerasaData(BaseModel):
    cpf: str
    score: int
    has_negative_records: bool
    protests: int
    debts_value: float

class BacenSCRData(BaseModel):
    cpf: str
    total_loan_value: float
    total_overdue_value: float
    risk_level: int