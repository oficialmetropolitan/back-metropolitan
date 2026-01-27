from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, Float, ForeignKey, 
                        Boolean, Date, Numeric, UniqueConstraint, func, JSON) 

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from db import Base



    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False)
    cpf = Column(String(14), nullable=False, unique=True, index=True)
    
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
  
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True, index=True)
    verification_expires_at = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)


    perfil = relationship("PerfilUsuario", back_populates="user", uselist=False, cascade="all, delete-orphan")
    simulacoes = relationship("Simulacao", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("cpf", name="uq_users_cpf"),
    )


class PerfilUsuario(Base):
    __tablename__ = "perfis_usuarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    genero = Column(String(20), nullable=True)
    escolaridade = Column(String(100), nullable=True)
    estado_civil = Column(String(50), nullable=True)
    nome_mae = Column(String(150), nullable=True)

    cep = Column(String(10), nullable=True)
    logradouro = Column(String(150), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)

    possui_veiculo = Column(Boolean, default=False)
    possui_imovel = Column(Boolean, default=False)
    profissao = Column(String(100), nullable=True)
    data_admissao = Column(Date, nullable=True)
    renda_mensal = Column(Numeric(10, 2), nullable=True)


    user = relationship("User", back_populates="perfil")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)
    data_nascimento = Column(Date, nullable=True)
    
    # Relacionamento: Um Lead pode ter várias simulações
    simulacoes = relationship("Simulacao", back_populates="lead")
    
    # Caso ele vire usuário depois
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

class Simulacao(Base):
    __tablename__ = "simulacoes"

    id = Column(Integer, primary_key=True, index=True)
    
    # AJUSTE: user_id agora é nullable=True (opcional no início)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # NOVO: Chave estrangeira para o Lead
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)

    valor_desejado = Column(Numeric(12, 2), nullable=False) 
    prazo_meses = Column(Integer, nullable=False)          
    motivo_emprestimo = Column(String(150), nullable=False) 
    tipo_emprestimo = Column(String(50), nullable=False)   

    dados_especificos = Column(JSON, nullable=True)

    valor_parcela = Column(Numeric(12, 2), nullable=True)
    valor_total = Column(Numeric(12, 2), nullable=True)
    juros_total = Column(Numeric(12, 2), nullable=True)
    
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pendente")

    # Relacionamentos
    user = relationship("User", back_populates="simulacoes")
    lead = relationship("Lead", back_populates="simulacoes") 