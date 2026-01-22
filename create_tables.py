# create_tables.py

# Importe sua 'engine' e 'Base' do db.py
from db import engine, Base 

# Importe TODOS os seus modelos
# (O Python precisa "vê-los" para saber o que criar)
from models.models import User, PerfilUsuario, Simulacao 

print("Iniciando a recriação das tabelas...")

# Apaga todas as tabelas existentes
print("Apagando tabelas antigas (se existirem)...")
Base.metadata.drop_all(bind=engine)

# Cria todas as tabelas novas, baseadas nos seus modelos
print("Criando tabelas novas...")
Base.metadata.create_all(bind=engine)

print("Tabelas recriadas com sucesso!")