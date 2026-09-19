import os
import hmac
import hashlib
import logging
import json
import threading
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
import httpx

load_dotenv()

logger = logging.getLogger("suenalotto.qvapay")

QVAPAY_API_URL = os.getenv("QVAPAY_API_URL", "https://api.qvapay.com")
QVAPAY_APP_ID = os.getenv("QVAPAY_APP_ID", "")
QVAPAY_SECRET = os.getenv("QVAPAY_SECRET", "")
QVAPAY_WEBHOOK_SECRET = os.getenv("QVAPAY_WEBHOOK_SECRET", "")
APP_URL = os.getenv("APP_URL", "http://localhost:8501")
API_PUBLIC_URL = os.getenv("API_PUBLIC_URL", os.getenv("FASTAPI_URL", "http://localhost:8000"))

PROMO_LIFETIME_PRICE = float(os.getenv("PROMO_LIFETIME_PRICE", "50.00"))
PROMO_MAX_USERS = int(os.getenv("PROMO_MAX_USERS", "100"))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMO_FILE = os.path.join(BASE_DIR, "data", "promo_status.json")
_promo_lock = threading.Lock()

PLANS = {
    "pro": {
        "name": "Pro Mensual",
        "amount": 1.99,
        "currency": "USD",
        "days": 30,
    },
    "lifetime": {
        "name": "De por Vida",
        "amount": 99.99,
        "currency": "USD",
        "days": 36525,
    },
}

# ─── Promo helpers ─────────────────────────────────────────────────

def get_promo_status() -> dict:
    with _promo_lock:
        if os.path.exists(PROMO_FILE):
            with open(PROMO_FILE, "r") as f:
                return json.load(f)
        return {"total_purchased": 0}

def save_promo_status(data: dict):
    with _promo_lock:
        os.makedirs(os.path.dirname(PROMO_FILE), exist_ok=True)
        with open(PROMO_FILE, "w") as f:
            json.dump(data, f)

def get_lifetime_price() -> tuple[float, bool, int]:
    status = get_promo_status()
    remaining = max(PROMO_MAX_USERS - status["total_purchased"], 0)
    if remaining > 0:
        return PROMO_LIFETIME_PRICE, True, remaining
    return PLANS["lifetime"]["amount"], False, 0

def increment_promo_purchases() -> int:
    status = get_promo_status()
    status["total_purchased"] += 1
    save_promo_status(status)
    return status["total_purchased"]

def get_promo_info() -> dict:
    status = get_promo_status()
    remaining = max(PROMO_MAX_USERS - status["total_purchased"], 0)
    return {
        "active": remaining > 0,
        "price": PROMO_LIFETIME_PRICE if remaining > 0 else PLANS["lifetime"]["amount"],
        "full_price": PLANS["lifetime"]["amount"],
        "promo_price": PROMO_LIFETIME_PRICE,
        "remaining": remaining,
        "total_purchased": status["total_purchased"],
        "max_promo": PROMO_MAX_USERS,
    }


def is_configured() -> bool:
    return bool(QVAPAY_APP_ID and QVAPAY_SECRET)


def mock_enabled() -> bool:
    """True cuando Qvapay no está configurado y el entorno permite pagos simulados.

    Se activa explícitamente con QVAPAY_MOCK_MODE=1 o automáticamente en entornos
    de desarrollo (ENVIRONMENT vacío/local/dev/test). Nunca se activa en producción.
    """
    if QVAPAY_APP_ID and QVAPAY_SECRET:
        return False
    mode = os.getenv("QVAPAY_MOCK_MODE", "").strip().lower()
    if mode in ("1", "true", "yes", "on"):
        return True
    env_name = os.getenv("ENVIRONMENT", "").strip().lower()
    return env_name in ("", "local", "development", "dev", "test")


def _sign_webhook(raw_body: bytes, secret: str) -> str:
    return hmac.new(
        secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()


def create_payment_url(
    plan_id: str, username: str, email: str, user_id: int
) -> Optional[dict]:
    if not is_configured():
        if mock_enabled():
            logger.warning("Qvapay not configured; using MOCK payment for %s", username)
            plan = PLANS.get(plan_id)
            if not plan:
                logger.error("Invalid plan id: %s", plan_id)
                return None
            amount = plan["amount"]
            promo_info = None
            if plan_id == "lifetime":
                amount, is_promo, remaining = get_lifetime_price()
                promo_info = {"active": is_promo, "remaining": remaining}
            external_id = f"sl_{user_id}_{plan_id}_{int(datetime.utcnow().timestamp())}"
            return {
                "payment_url": (
                    f"{API_PUBLIC_URL.rstrip('/')}/api/payments/mock/confirm?ext={external_id}"
                ),
                "payment_id": f"mock_{external_id}",
                "external_id": external_id,
                "amount": amount,
                "currency": plan["currency"],
                "promo": promo_info,
                "mock": True,
            }
        logger.warning("Qvapay not configured; skipping payment creation")
        return None

    plan = PLANS.get(plan_id)
    if not plan:
        logger.error("Invalid plan id: %s", plan_id)
        return None

    amount = plan["amount"]
    promo_info = None
    if plan_id == "lifetime":
        amount, is_promo, remaining = get_lifetime_price()
        promo_info = {"active": is_promo, "remaining": remaining}

    payload = {
        "amount": amount,
        "description": f"{plan['name']} - {username}",
        "remote_id": f"sl_{user_id}_{plan_id}_{int(datetime.utcnow().timestamp())}",
        "webhook": f"{APP_URL.rstrip('/')}/api/payments/webhook",
    }

    headers = {
        "Content-Type": "application/json",
        "app-id": QVAPAY_APP_ID,
        "app-secret": QVAPAY_SECRET,
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{QVAPAY_API_URL}/v2/create_invoice",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "Qvapay payment created for %s (%s): %s",
                username, plan_id, data.get("url", ""),
            )
            return {
                "payment_url": data.get("url"),
                "payment_id": data.get("transaction_uuid"),
                "external_id": payload["remote_id"],
                "amount": amount,
                "currency": plan["currency"],
                "promo": promo_info,
            }
    except Exception as e:
        logger.error("Qvapay payment creation failed for %s: %s", username, e)
        return None


def verify_webhook(raw_body: bytes, signature_header: str) -> bool:
    signature = (signature_header or "").strip()
    if signature.startswith("sha256="):
        signature = signature[len("sha256="):]
    if not signature:
        logger.warning("Qvapay webhook missing signature value")
        return False
    secret = QVAPAY_WEBHOOK_SECRET or QVAPAY_SECRET
    expected = _sign_webhook(raw_body, secret)
    return hmac.compare_digest(expected, signature.lower())


def process_webhook(data: dict) -> Optional[dict]:
    payment_id = data.get("payment_id") or data.get("uuid") or data.get("transaction_uuid") or ""
    external_id = data.get("external_id") or data.get("remote_id") or ""
    status = (data.get("status") or "").lower()
    logger.info("Qvapay webhook: payment=%s status=%s external=%s", payment_id, status, external_id)

    if status not in ("completed", "confirmed", "paid"):
        return {"action": "ignored", "status": status}

    parts = external_id.split("_")
    if len(parts) < 3 or parts[0] != "sl":
        logger.warning("Invalid external_id format: %s", external_id)
        return {"action": "error", "reason": "invalid_external_id"}

    try:
        user_id = int(parts[1])
    except (TypeError, ValueError):
        logger.warning("Invalid user_id in external_id: %s", external_id)
        return {"action": "error", "reason": "invalid_external_id"}
    plan_id = parts[2]

    return {
        "action": "activate",
        "user_id": user_id,
        "plan_id": plan_id,
        "payment_id": payment_id,
        "status": status,
    }
