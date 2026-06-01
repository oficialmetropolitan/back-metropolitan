# schemas/user.py

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from validators import validar_cpf, _only_digits, senha_forte

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
    
    @validator('password')
    def validate_password(cls, value: str) -> str:
        # Capturamos os dois valores retornados pela função
        valida, mensagem = senha_forte(value)
        
        if not valida:
            # Lançamos o erro com a mensagem específica que veio da função
            raise ValueError(mensagem)
            
        return value

class UserOut(UserBase):
    id: int
    created_at: datetime
    is_admin: bool

    class Config:
        from_attributes = True