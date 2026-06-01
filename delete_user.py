from sqlalchemy.orm import sessionmaker

# Importe o 'engine' do seu arquivo de configuração do banco de dados
from db import engine 

# Importe seu modelo de usuário
from models.models import User

# Crie uma classe de Sessão para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def delete_user_by_id(user_id: int):
    """
    Conecta-se ao banco de dados, encontra um usuário pelo seu ID e o apaga.
    """
    # Inicia uma nova sessão
    db_session = SessionLocal()
    
    print(f"Tentando apagar usuário com ID: {user_id}...")
    
    try:
        # 1. Encontra o usuário no banco de dados
        user_to_delete = db_session.query(User).filter(User.id == user_id).first()
        
        # 2. Verifica se o usuário foi encontrado
        if user_to_delete:
            # 3. Apaga o usuário da sessão
            db_session.delete(user_to_delete)
            
            # 4. Confirma (commit) a transação para salvar a remoção no banco
            db_session.commit()
            
            print(f"✅ Usuário '{user_to_delete.full_name}' (ID: {user_id}) foi apagado com sucesso!")
        else:
            print(f"⚠️ Usuário com ID {user_id} não encontrado no banco de dados.")
            
    except Exception as e:
        # Em caso de erro, reverte a transação para não corromper os dados
        print(f"❌ Ocorreu um erro ao apagar o usuário: {e}")
        db_session.rollback()
    finally:
        # 5. Garante que a sessão seja sempre fechada
        print("Fechando a sessão com o banco de dados.")
        db_session.close()

# --- SCRIPT PRINCIPAL ---
if __name__ == "__main__":
    # Defina aqui o ID do usuário que você quer apagar
    # Pela sua imagem, o ID da 'isabella' é 1.
    USER_ID_TO_DELETE = 3
    
    delete_user_by_id(USER_ID_TO_DELETE)

