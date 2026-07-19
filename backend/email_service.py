import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("suenalotto.email")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@suenalotto.com")
APP_URL = os.getenv("APP_URL", "http://localhost:8501")


def is_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def _send_email(to: str, subject: str, html: str) -> bool:
    if not is_configured():
        logger.warning("SMTP not configured; skipping email to %s", to)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, [to], msg.as_string())
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def send_verification_email(to: str, token: str) -> bool:
    link = f"{APP_URL}/verify-email?token={token}"
    html = f"""
    <html><body style="font-family:sans-serif;background:#0a0e1a;padding:2rem;">
    <div style="max-width:480px;margin:auto;background:#1e293b;border-radius:1rem;padding:2rem;border:1px solid #334155;">
    <h1 style="color:#fbbf24;text-align:center;">🌟 SueñaLotto</h1>
    <p style="color:#94a3b8;text-align:center;">Gracias por registrarte. Verifica tu email para activar tu cuenta.</p>
    <div style="text-align:center;margin:2rem 0;">
    <a href="{link}" style="background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#0f172a;padding:0.8rem 2rem;border-radius:0.5rem;text-decoration:none;font-weight:700;">Verificar Email</a>
    </div>
    <p style="color:#64748b;font-size:0.8rem;text-align:center;">Si no creaste esta cuenta, ignora este mensaje.</p>
    </div></body></html>"""
    return _send_email(to, "Verifica tu email - SueñaLotto", html)


def send_password_reset(to: str, token: str) -> bool:
    link = f"{APP_URL}/reset-password?token={token}"
    html = f"""
    <html><body style="font-family:sans-serif;background:#0a0e1a;padding:2rem;">
    <div style="max-width:480px;margin:auto;background:#1e293b;border-radius:1rem;padding:2rem;border:1px solid #334155;">
    <h1 style="color:#fbbf24;text-align:center;">🌟 SueñaLotto</h1>
    <p style="color:#94a3b8;text-align:center;">Recibimos una solicitud para restablecer tu contraseña.</p>
    <div style="text-align:center;margin:2rem 0;">
    <a href="{link}" style="background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#0f172a;padding:0.8rem 2rem;border-radius:0.5rem;text-decoration:none;font-weight:700;">Restablecer Contraseña</a>
    </div>
    <p style="color:#64748b;font-size:0.8rem;text-align:center;">Si no solicitaste esto, ignora este mensaje. El enlace expira en 1 hora.</p>
    </div></body></html>"""
    return _send_email(to, "Restablece tu contraseña - SueñaLotto", html)


def send_welcome_email(to: str, username: str) -> bool:
    html = f"""
    <html><body style="font-family:sans-serif;background:#0a0e1a;padding:2rem;">
    <div style="max-width:480px;margin:auto;background:#1e293b;border-radius:1rem;padding:2rem;border:1px solid #334155;">
    <h1 style="color:#fbbf24;text-align:center;">🌟 Bienvenido, {username}!</h1>
    <p style="color:#94a3b8;">Tu cuenta en SueñaLotto está activa. Explora estadísticas, la Charada Cubana, y más.</p>
    <p style="color:#64748b;font-size:0.85rem;">🎯 Análisis de lotería · 🔢 Matriz Charada · 🤖 IA para adivinanzas</p>
    <div style="text-align:center;margin:1.5rem 0;">
    <a href="{APP_URL}" style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:white;padding:0.8rem 2rem;border-radius:0.5rem;text-decoration:none;font-weight:700;">Ir a SueñaLotto</a>
    </div>
    </div></body></html>"""
    return _send_email(to, "Bienvenido a SueñaLotto", html)


def send_payment_receipt(to: str, username: str, plan: str, amount: str, tx_id: str) -> bool:
    html = f"""
    <html><body style="font-family:sans-serif;background:#0a0e1a;padding:2rem;">
    <div style="max-width:480px;margin:auto;background:#1e293b;border-radius:1rem;padding:2rem;border:1px solid #334155;">
    <h1 style="color:#fbbf24;text-align:center;">🌟 Pago Confirmado</h1>
    <p style="color:#94a3b8;text-align:center;">Gracias, {username}!</p>
    <div style="background:#334155;border-radius:0.5rem;padding:1rem;margin:1rem 0;">
    <p style="color:#f1f5f9;"><strong>Plan:</strong> {plan}</p>
    <p style="color:#f1f5f9;"><strong>Monto:</strong> {amount}</p>
    <p style="color:#f1f5f9;"><strong>Transacción:</strong> {tx_id}</p>
    </div>
    <p style="color:#64748b;font-size:0.85rem;">Ya puedes disfrutar de todas las funcionalidades de tu plan.</p>
    </div></body></html>"""
    return _send_email(to, f"Recibo de pago {plan} - SueñaLotto", html)
