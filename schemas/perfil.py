# schemas/perfil.py

from pydantic import BaseModel
from typing import Optional
from datetime import date

class PerfilUsuarioBase(BaseModel):

    data_nascimento: Optional[date] = None
    genero: Optional[str] = None
    escolaridade: Optional[str] = None
    estado_civil: Optional[str] = None
    nome_mae: Optional[str] = None

    cep: Optional[str] = None
    logradouro: Optional[str] = None 
    numero: Optional[str] = None
    bairro: Optional[str] = None 
    cidade: Optional[str] = None
    estado: Optional[str] = None 
    
    # Ocupação
    profissao: Optional[str] = None    
    data_admissao: Optional[date] = None  
    renda_mensal: Optional[float] = None
    
    # Bens
    possui_veiculo: Optional[bool] = False
    possui_imovel: Optional[bool] = False

class PerfilUsuarioCreate(PerfilUsuarioBase):
    pass

class PerfilUsuarioOut(PerfilUsuarioBase):
    user_id: int
    class Config:
        from_attributes = True