"""NOWPayments — pasarela de pago automático en cripto (USDT, BTC, etc.).

Flujo:
  1. create_payment_url() crea la factura en NOWPayments y devuelve su URL de pago.
  2. El usuario paga en la pasarela.
  3. NOWPayments notifica el pago a /api/payments/webhook/nowpayments (IPN, firmado).
  4. process_webhook() traduce el order_id y activa el plan del usuario.
  5. Si el IPN se pierde, el frontend puede llamar a /api/payments/nowpayments/status
     para comprobar el estado directamente contra la API y activar el plan.

Variables de entorno: NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_SECRET,
NOWPAYMENTS_PAY_CURRENCY, NOWPAYMENTS_PRICE_CURRENCY, NOWPAYMENTS_SANDBOX,
NOWPAYMENTS_API_URL.
"""
import os
import hmac
import hashlib
import logging
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
import httpx

from backend.qvapay import PLANS, get_lifetime_price

load_dotenv()

logger = logging.getLogger("suenalotto.nowpayments")

_SANDBOX = os.getenv("NOWPAYMENTS_SANDBOX", "").strip().lower() in ("1", "true", "yes", "on")
NOWPAYMENTS_API_URL = os.getenv(
    "NOWPAYMENTS_API_URL",
    "https://api-sandbox.nowpayments.io/v1" if _SANDBOX else "https://api.nowpayments.io/v1",
).rstrip("/")
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "").strip()
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "").strip()
NOWPAYMENTS_PAY_CURRENCY = os.getenv("NOWPAYMENTS_PAY_CURRENCY", "usdttbsc").strip().lower()
NOWPAYMENTS_PRICE_CURRENCY = os.getenv("NOWPAYMENTS_PRICE_CURRENCY", "usd").strip().lower()

APP_URL = os.getenv("APP_URL", "http://localhost:8501")
API_PUBLIC_URL = os.getenv("API_PUBLIC_URL", os.getenv("FASTAPI_URL", "http://localhost:8000"))

IPN_PATH = "/api/payments/webhook/nowpayments"
FINISHED_STATUSES = ("finished", "confirmed", "completed")


def is_configured() -> bool:
    """NOWPayments queda habilitado solo con la API key (el secreto IPN es
    necesario únicamente para recibir webhooks firmados)."""
    return bool(NOWPAYMENTS_API_KEY)


def ipn_secret() -> str:
    return NOWPAYMENTS_IPN_SECRET or NOWPAYMENTS_API_KEY


def create_payment_url(
    plan_id: str, username: str, email: str, user_id: int
) -> Optional[dict]:
    """Crea la factura de NOWPayments y devuelve la URL de pago."""
    if not is_configured():
        logger.warning("NOWPayments not configured; skipping payment creation")
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

    order_id = f"sl_{user_id}_{plan_id}_{int(datetime.utcnow().timestamp())}"
    payload = {
        "price_amount": amount,
        "price_currency": NOWPAYMENTS_PRICE_CURRENCY,
        "pay_currency": NOWPAYMENTS_PAY_CURRENCY,
        "order_id": order_id,
        "order_description": f"{plan['name']} - {username}",
        "ipn_callback_url": f"{API_PUBLIC_URL.rstrip('/')}{IPN_PATH}",
        "success_url": f"{APP_URL.rstrip('/')}/10_payment_success?plan={plan_id}",
        "fail_url": f"{APP_URL.rstrip('/')}/11_payment_cancel",
        "is_fiat": False,
    }
    if _SANDBOX:
        payload["sandbox"] = True

    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.post(
                f"{NOWPAYMENTS_API_URL}/payment", json=payload, headers=headers
            )
            if resp.status_code >= 400:
                logger.error(
                    "NOWPayments rejected the payment (%s): %s",
                    resp.status_code, resp.text[:300],
                )
                return None
            data = resp.json()
            logger.info(
                "NOWPayments payment created for %s (%s): payment_id=%s amount=%s %s",
                username, plan_id, data.get("payment_id"),
                data.get("pay_amount"), data.get("pay_currency"),
            )
            return {
                "payment_url": data.get("payment_url"),
                "payment_id": str(data.get("payment_id", "")),
                "external_id": order_id,
                "amount": amount,
                "currency": plan["currency"],
                "pay_amount": data.get("pay_amount"),
                "pay_currency": data.get("pay_currency"),
                "promo": promo_info,
                "method": "nowpayments",
            }
    except Exception as e:
        logger.error("NOWPayments payment creation failed for %s: %s", username, e)
        return None


def verify_webhook(raw_body: bytes, signature_header: str) -> bool:
    """Valida la firma HMAC-SHA512 del IPN (header x-nowpayments-sig)."""
    signature = (signature_header or "").strip().lower()
    secret = ipn_secret()
    if not secret:
        logger.error("NOWPayments IPN received but no IPN secret is configured")
        return False
    if not signature:
        logger.warning("NOWPayments IPN missing signature value")
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)


def process_webhook(data: dict) -> Optional[dict]:
    """Traduce el payload del IPN al mismo formato que usa QvaPay."""
    payment_id = str(data.get("payment_id", ""))
    external_id = str(data.get("order_id", "") or "")
    status = (data.get("payment_status") or "").lower()
    logger.info(
        "NOWPayments IPN: payment=%s status=%s order=%s", payment_id, status, external_id
    )

    if status not in FINISHED_STATUSES:
        return {"action": "ignored", "status": status}

    parts = external_id.split("_")
    if len(parts) < 3 or parts[0] != "sl":
        logger.warning("Invalid order_id format: %s", external_id)
        return {"action": "error", "reason": "invalid_external_id"}

    try:
        user_id = int(parts[1])
    except (TypeError, ValueError):
        logger.warning("Invalid user_id in order_id: %s", external_id)
        return {"action": "error", "reason": "invalid_external_id"}

    return {
        "action": "activate",
        "user_id": user_id,
        "plan_id": parts[2],
        "payment_id": payment_id,
        "status": status,
    }


def get_payment_status(payment_id: str) -> Optional[dict]:
    """Consulta el estado real de un pago en NOWPayments (respaldo del IPN)."""
    if not is_configured() or not payment_id:
        return None
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{NOWPAYMENTS_API_URL}/payment/{payment_id}",
                headers={"x-api-key": NOWPAYMENTS_API_KEY},
            )
            if resp.status_code >= 400:
                logger.warning(
                    "NOWPayments status check failed (%s): %s",
                    resp.status_code, resp.text[:200],
                )
                return None
            return resp.json()
    except Exception as e:
        logger.error("NOWPayments status check error: %s", e)
        return None