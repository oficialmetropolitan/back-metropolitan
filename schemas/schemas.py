from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal  # <-- CORREÇÃO APLICADA AQUI
from validators import validar_cpf_formatado, senha_forte
from datetime import datetime, date

from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from validators import validar_cpf, _only_digits
# --- Schemas de Usuário ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str
    cpf: str = Field(..., min_length=11, max_length=14)

    @validator('cpf')
    def validate_cpf(cls, value: str) -> str:
        
        cpf_digits = _only_digits(value)
        
        if not validar_cpf(cpf_digits):
            raise ValueError('CPF inválido')
    
        return cpf_digits
        
class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

# --- Schemas dze Perfil ---
class PerfilUsuarioBase(BaseModel):
    # Dados pessoais
    data_nascimento: Optional[date] = None
    genero: Optional[str] = None
    escolaridade: Optional[str] = None
    estado_civil: Optional[str] = None
    nome_mae: Optional[str] = None
    tipo_documento: Optional[str] = None
    # Endereço
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    # Dados financeiros
    possui_restricao: Optional[bool] = False
    possui_veiculo: Optional[bool] = False
    possui_imovel: Optional[bool] = False
    banco: Optional[str] = None
    agencia: Optional[str] = None
    conta: Optional[str] = None
    digito: Optional[str] = None
    profissao: Optional[str] = None
    data_admissao: Optional[date] = None
    renda_mensal: Optional[float] = None

class PerfilUsuarioCreate(PerfilUsuarioBase):
    pass

class PerfilUsuarioOut(PerfilUsuarioBase):
    user_id: int
    class Config:
        orm_mode = True

# --- SCHEMAS DE SIMULAÇÃO (ATUALIZADOS) ---
class SimulacaoBase(BaseModel):
    # NOVO: Adicionar os campos aqui também
    client_category: str
    documento_tipo: Optional[str] = None
    documento_valor: Optional[str] = None
    
    valor: float
    parcelas: int
    tipo_emprestimo: str
    finalidade: str
    valor_parcela: float
    valor_total: float
    juros_total: float

class SimulacaoCreate(SimulacaoBase):
    pass

class SimulacaoOut(SimulacaoBase):
    id: int
    user_id: int
    criado_em: datetime
    class Config:
        orm_mode = True

# --- Schemas para Análise de Crédito ---
class CreditAnalysisRequest(BaseModel):
    cpf: str = Field(..., description="CPF do usuário para análise.")
    valor_emprestimo: float = Field(..., gt=0, description="Valor do empréstimo solicitado.")
    numero_parcelas: int = Field(..., gt=0, description="Número de parcelas desejado.")

class CreditAnalysisResponse(BaseModel):
    decision: str
    message: str
    credit_score: int
    approved_limit: float
    cpf: str


# --- Schemas para Análise de Crédito ---

class CreditAnalysisRequest(BaseModel):
    cpf: str = Field(..., description="CPF do cliente para busca no banco de dados.", example="111.222.333-44")
    requested_amount: float = Field(..., description="Valor do empréstimo solicitado.", example=10000.0)
    installments: int = Field(..., description="Número de parcelas.", example=24)

class CreditAnalysisResponse(BaseModel):
    cpf: str
    decision: Literal["Aprovado", "Negado", "Análise Manual"]
    score: int
    message: str
    approved_amount: Optional[float] = None
    approved_installments: Optional[int] = None

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


