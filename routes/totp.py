import base64
import io
import json
import secrets
import string
from datetime import datetime, timedelta, timezone

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

import security
from db import get_db
from models.models import User

router = APIRouter(prefix="/api/auth/2fa", tags=["2FA"])

_recovery_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
ISSUER = "Metropolitan Investimentos"


class EnablePayload(BaseModel):
    code: str


class VerifyPayload(BaseModel):
    temp_token: str
    code: str


class RecoveryPayload(BaseModel):
    temp_token: str
    recovery_code: str


class DisablePayload(BaseModel):
    code: str


def _gen_recovery_codes() -> list[str]:
    ab = string.ascii_uppercase + string.digits
    return [
        f"{''.join(secrets.choice(ab) for _ in range(4))}-{''.join(secrets.choice(ab) for _ in range(4))}"
        for _ in range(10)
    ]


def _check_and_remove(plain: str, hashed: list[str]) -> tuple[bool, list[str]]:
    for i, h in enumerate(hashed):
        if _recovery_ctx.verify(plain.upper(), h):
            return True, hashed[:i] + hashed[i + 1:]
    return False, hashed


@router.get("/status")
def get_status(current_user: User = Depends(security.get_current_active_user)):
    return {"totp_enabled": bool(current_user.totp_enabled)}


@router.post("/setup")
def setup(
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db),
):
    secret = pyotp.random_base32()
    uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name=ISSUER)

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    current_user.totp_secret = secret
    db.commit()

    return {
        "qr_code": f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}",
        "manual_key": secret,
    }


@router.post("/enable")
def enable(
    payload: EnablePayload,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA já está ativado.")
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Chame /setup antes de ativar.")
    if not pyotp.TOTP(current_user.totp_secret).verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código inválido.")

    plain = _gen_recovery_codes()
    current_user.totp_enabled = True
    current_user.totp_recovery_codes = json.dumps([_recovery_ctx.hash(c) for c in plain])
    current_user.last_2fa_at = datetime.now(timezone.utc)
    db.commit()

    return {"recovery_codes": plain}


@router.post("/verify")
def verify(payload: VerifyPayload, db: Session = Depends(get_db)):
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado.")
    email = security.verify_token(payload.temp_token, exc, expected_type="2fa_pending")
    user = security.get_user_by_email(db, email=email)
    if not user or not user.totp_enabled or not user.totp_secret:
        raise exc
    if not pyotp.TOTP(user.totp_secret).verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código inválido.")

    user.last_2fa_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "access_token": security.create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        "token_type": "bearer",
        "is_admin": user.is_admin,
        "session_2fa_token": security.create_access_token(
            data={"sub": user.email, "type": "2fa_session"},
            expires_delta=timedelta(days=30),
        ),
    }


@router.post("/recovery")
def recovery(payload: RecoveryPayload, db: Session = Depends(get_db)):
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado.")
    email = security.verify_token(payload.temp_token, exc, expected_type="2fa_pending")
    user = security.get_user_by_email(db, email=email)
    if not user or not user.totp_enabled or not user.totp_recovery_codes:
        raise exc

    hashed = json.loads(user.totp_recovery_codes)
    found, remaining = _check_and_remove(payload.recovery_code, hashed)
    if not found:
        raise HTTPException(status_code=400, detail="Código de recuperação inválido.")

    user.totp_recovery_codes = json.dumps(remaining)
    user.last_2fa_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "access_token": security.create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        "token_type": "bearer",
        "is_admin": user.is_admin,
        "session_2fa_token": security.create_access_token(
            data={"sub": user.email, "type": "2fa_session"},
            expires_delta=timedelta(days=30),
        ),
        "remaining_codes": len(remaining),
    }


@router.post("/disable")
def disable(
    payload: DisablePayload,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db),
):
    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA não está ativado.")
    if not pyotp.TOTP(current_user.totp_secret).verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código inválido.")

    current_user.totp_enabled = False
    current_user.totp_secret = None
    current_user.totp_recovery_codes = None
    current_user.last_2fa_at = None
    db.commit()

    return {"message": "2FA desativado com sucesso."}
