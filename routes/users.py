from fastapi import APIRouter, Depends
import schemas.user as schemas, security
from models.models import User

router = APIRouter(
    prefix="/api/users",
    tags=["Usuários"]
)

@router.get("/me", response_model=schemas.UserOut, summary="Obter dados do usuário logado")
async def read_users_me(current_user: User = Depends(security.get_current_active_user)):
    """
    Retorna as informações do usuário atualmente autenticado.
    """
    return current_user