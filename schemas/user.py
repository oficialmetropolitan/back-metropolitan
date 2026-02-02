# schemas/user.py

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from validators import validar_cpf, _only_digits # Ajuste o caminho se necessário

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
    is_admin: bool

    class Config:
        from_attributes = True