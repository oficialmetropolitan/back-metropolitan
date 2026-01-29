from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db import get_db
import schemas.user as schemas
import security
from models.models import User

router = APIRouter(
    prefix="/api/users",
    tags=["Usuários"]
)

@router.get("/me", response_model=schemas.UserOut, summary="Obter dados do usuário logado")
async def read_users_me(current_user: User = Depends(security.get_current_active_user)):
    """Retorna as informações do usuário atualmente autenticado."""
    return current_user

# --- NOVA ROTA: LISTAR TODOS OS USUÁRIOS ---
@router.get("/", response_model=List[schemas.UserOut]) # Esta é a nova rota
def listar_todos_usuarios(
    db: Session = Depends(get_db),
    current_admin: User = Depends(security.get_current_admin)
):
    return db.query(User).all()

@router.get("admin/{user_id}", response_model=schemas.UserOut)
def buscar_usuario_por_id(
    user_id: int, 
    db: Session = Depends(get_db),
    current_admin: User = Depends(security.get_current_admin)
):
    """Rota administrativa para puxar dados do usuário, incluindo CPF."""
    usuario = db.query(User).filter(User.id == user_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    return usuario