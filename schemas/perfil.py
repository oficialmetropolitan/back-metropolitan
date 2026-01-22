# schemas/perfil.py

from pydantic import BaseModel
from typing import Optional
from datetime import date

class PerfilUsuarioBase(BaseModel):
    # Sua lista de "perguntas gerais sobre a pessoa"
    data_nascimento: Optional[date] = None
    genero: Optional[str] = None
    escolaridade: Optional[str] = None
    estado_civil: Optional[str] = None
    nome_mae: Optional[str] = None
    
    # Endereço residencial do usuário
    cep: Optional[str] = None
    logradouro: Optional[str] = None # Você pode adicionar
    numero: Optional[str] = None
    bairro: Optional[str] = None # Você pode adicionar
    cidade: Optional[str] = None # Você pode adicionar
    estado: Optional[str] = None # Você pode adicionar
    
    # Ocupação
    profissao: Optional[str] = None     # "Qual a sua ocupação?"
    data_admissao: Optional[date] = None  # "se a pessoa trabalha qual a data de admissão"
    renda_mensal: Optional[float] = None
    
    # Bens
    possui_veiculo: Optional[bool] = False
    possui_imovel: Optional[bool] = False

class PerfilUsuarioCreate(PerfilUsuarioBase):
    pass

class PerfilUsuarioOut(PerfilUsuarioBase):
    user_id: int
    class Config:
        orm_mode = True