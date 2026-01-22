import random
from models.api_models import SerasaData, BacenSCRData
from models.models import PerfilUsuario

def consultar_serasa(perfil: PerfilUsuario) -> SerasaData:
    print(f"SIMULADOR: Consultando Serasa para o CPF {perfil.user.cpf}...")
    
    base_score = 600
    
    # Simulação mais inteligente baseada no perfil
    if perfil.possui_restricao:
        base_score = 300
    elif perfil.renda_mensal > 10000:
        base_score = 800
    elif perfil.possui_imovel:
        base_score = 700

    return SerasaData(
        cpf=perfil.user.cpf,
        score=random.randint(base_score - 100, base_score + 100),
        has_negative_records=perfil.possui_restricao,
        protests=1 if perfil.possui_restricao else 0,
        debts_value=float(random.randint(5000, 15000)) if perfil.possui_restricao else float(random.randint(0, 5000))
    )

def consultar_banco_central_scr(perfil: PerfilUsuario) -> BacenSCRData:
    print(f"SIMULADOR: Consultando SCR do Bacen para o CPF {perfil.user.cpf}...")

    total_loan = 0
    if perfil.possui_imovel:
        total_loan += 150000
    if perfil.possui_veiculo:
        total_loan += 30000

    return BacenSCRData(
        cpf=perfil.user.cpf,
        total_loan_value=float(random.uniform(0.8, 1.2) * total_loan),
        total_overdue_value=float(random.randint(5000, 10000)) if perfil.possui_restricao else 0.0,
        risk_level=random.randint(3, 5) if perfil.possui_restricao else random.randint(1, 2)
    )