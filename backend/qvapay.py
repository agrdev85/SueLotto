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

QVAPAY_API_URL = os.getenv("QVAPAY_API_URL", "https://qvapay.com/api/v1")
QVAPAY_APP_ID = os.getenv("QVAPAY_APP_ID", "")
QVAPAY_SECRET = os.getenv("QVAPAY_SECRET", "")
QVAPAY_WEBHOOK_SECRET = os.getenv("QVAPAY_WEBHOOK_SECRET", "")
APP_URL = os.getenv("APP_URL", "http://localhost:8501")

PROMO_LIFETIME_PRICE = float(os.getenv("PROMO_LIFETIME_PRICE", "50.00"))
PROMO_MAX_USERS = int(os.getenv("PROMO_MAX_USERS", "100"))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMO_FILE = os.path.join(BASE_DIR, "data", "promo_status.json")
_promo_lock = threading.Lock()

PLANS = {
    "pro": {
        "name": "Pro Mensual",
        "amount": 1.00,
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


def _sign(data: dict) -> str:
    msg = json.dumps(data, separators=(",", ":"))
    return hmac.new(
        QVAPAY_SECRET.encode(), msg.encode(), hashlib.sha256
    ).hexdigest()


def create_payment_url(
    plan_id: str, username: str, email: str, user_id: int
) -> Optional[dict]:
    if not is_configured():
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
        "app_id": QVAPAY_APP_ID,
        "amount": amount,
        "currency": plan["currency"],
        "description": f"{plan['name']} - {username}",
        "external_id": f"sl_{user_id}_{plan_id}_{int(datetime.utcnow().timestamp())}",
        "callback_url": f"{APP_URL.rstrip('/')}/api/payments/webhook",
        "success_url": f"{APP_URL}/payment/success?plan={plan_id}",
        "cancel_url": f"{APP_URL}/payment/cancel",
        "customer_email": email,
        "customer_username": username,
    }
    payload["signature"] = _sign(payload)

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(f"{QVAPAY_API_URL}/payment/create", json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "Qvapay payment created for %s (%s): %s",
                username, plan_id, data.get("payment_url", ""),
            )
            return {
                "payment_url": data.get("payment_url"),
                "payment_id": data.get("payment_id"),
                "external_id": payload["external_id"],
                "amount": amount,
                "currency": plan["currency"],
                "promo": promo_info,
            }
    except Exception as e:
        logger.error("Qvapay payment creation failed for %s: %s", username, e)
        return None


def verify_webhook(data: dict, signature: str) -> bool:
    expected = _sign(data)
    return hmac.compare_digest(expected, signature)


def process_webhook(data: dict) -> Optional[dict]:
    payment_id = data.get("payment_id", "")
    external_id = data.get("external_id", "")
    status = data.get("status", "")
    logger.info("Qvapay webhook: payment=%s status=%s external=%s", payment_id, status, external_id)

    if status not in ("completed", "confirmed"):
        return {"action": "ignored", "status": status}

    parts = external_id.split("_")
    if len(parts) < 3 or parts[0] != "sl":
        logger.warning("Invalid external_id format: %s", external_id)
        return {"action": "error", "reason": "invalid_external_id"}

    user_id = int(parts[1])
    plan_id = parts[2]

    return {
        "action": "activate",
        "user_id": user_id,
        "plan_id": plan_id,
        "payment_id": payment_id,
        "status": status,
    }
