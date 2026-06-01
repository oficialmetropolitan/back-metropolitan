"""
Execute este script UMA VEZ para adicionar as colunas de 2FA ao banco existente.
Uso: python add_2fa_columns.py
"""
from db import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64)"))
    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN NOT NULL DEFAULT FALSE"))
    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_recovery_codes VARCHAR(2048)"))
    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_2fa_at TIMESTAMPTZ"))
    conn.commit()

print("Colunas de 2FA adicionadas com sucesso!")
