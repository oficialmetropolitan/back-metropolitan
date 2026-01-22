import re

cpf_re = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")

def _only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def validar_cpf_formatado(cpf: str) -> bool:
    if not cpf_re.match(cpf):
        return False
    return validar_cpf(_only_digits(cpf))

def validar_cpf(cpf_digits: str) -> bool:
    # Rejeita CPFs com todos os dígitos iguais
    if len(cpf_digits) != 11 or cpf_digits == cpf_digits[0] * 11:
        return False
    
    def calc_dv(nums, peso_ini):
        soma = sum(int(d)*p for d, p in zip(nums, range(peso_ini, 1, -1)))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    dv1 = calc_dv(cpf_digits[:9], 10)
    dv2 = calc_dv(cpf_digits[:9] + dv1, 11)
    return cpf_digits[-2:] == dv1 + dv2

def senha_forte(s: str) -> tuple[bool, str]:
    # Regra simples: 8+ chars, maiúscula, minúscula, número e símbolo
    if len(s) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    if not re.search(r"[A-Z]", s):
        return False, "Senha deve ter pelo menos 1 letra maiúscula"
    if not re.search(r"[a-z]", s):
        return False, "Senha deve ter pelo menos 1 letra minúscula"
    if not re.search(r"\d", s):
        return False, "Senha deve ter pelo menos 1 número"
    if not re.search(r"[^A-Za-z0-9]", s):
        return False, "Senha deve ter pelo menos 1 símbolo"
    return True, ""