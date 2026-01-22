# schemas/credit_analysis.py

from pydantic import BaseModel, Field
from typing import Optional, Literal

class CreditAnalysisRequest(BaseModel):
    cpf: str = Field(..., description="CPF do cliente para análise.", example="111.222.333-44")
    requested_amount: float = Field(..., gt=0, description="Valor do empréstimo solicitado.", example=10000.0)
    installments: int = Field(..., gt=0, description="Número de parcelas desejado.", example=24)

class CreditAnalysisResponse(BaseModel):
    cpf: str
    decision: Literal["Aprovado", "Negado", "Análise Manual"]
    message: str
    credit_score: int
    approved_amount: Optional[float] = None
    approved_installments: Optional[int] = None
    
# -- Modelos para dados de fontes externas --

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