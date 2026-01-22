# routes/profile.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Imports dos módulos do projeto
import schemas.perfil as schemas  # <--- Use o schema de perfil CORRIGIDO
import security
from db import get_db
from models.models import PerfilUsuario, User # Importe os modelos

router = APIRouter(
    prefix="/api/perfil",
    tags=["Perfil do Usuário"],
    dependencies=[Depends(security.get_current_active_user)]
)

@router.get("/me", response_model=schemas.PerfilUsuarioOut, summary="Obter perfil do usuário logado")
def obter_perfil(db: Session = Depends(get_db), current_user: User = Depends(security.get_current_active_user)):
    """
    Obtém o perfil de dados detalhados do usuário logado.
    Útil para o frontend preencher a Etapa 3 se o usuário já tiver dados.
    """
    perfil = db.query(PerfilUsuario).filter(PerfilUsuario.user_id == current_user.id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não encontrado para este usuário.")
    return perfil


@router.put("/me", response_model=schemas.PerfilUsuarioOut, summary="Atualizar ou Criar perfil do usuário logado (Upsert)")
def atualizar_ou_criar_perfil(
    payload: schemas.PerfilUsuarioCreate, # <-- Usa o schema de perfil CORRIGIDO
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_active_user)
):
    """
    Atualiza o perfil do usuário logado. 
    Se o perfil não existir, ele é criado (Upsert).
    Esta é a rota que deve ser chamada na ETAPA 3 do fluxo de simulação.
    """
    # 1. Tenta encontrar o perfil existente
    perfil = db.query(PerfilUsuario).filter(PerfilUsuario.user_id == current_user.id).first()
    
    # Use .model_dump() para Pydantic v2 (ou .dict() para v1)
    payload_data = payload.model_dump(exclude_unset=True)

    if perfil:
        # 2. Se ENCONTROU -> ATUALIZA
        print("Perfil encontrado. Atualizando...")
        for key, value in payload_data.items():
            setattr(perfil, key, value)
    else:
        # 3. Se NÃO ENCONTROU -> CRIA
        print("Perfil não encontrado. Criando...")
        payload_data['user_id'] = current_user.id # Associa ao usuário logado
        perfil = PerfilUsuario(**payload_data)
        db.add(perfil)
    
    # 4. Salva as mudanças no banco
    db.commit()
    db.refresh(perfil)
    return perfil