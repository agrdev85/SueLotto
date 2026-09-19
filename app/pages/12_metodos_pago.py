import streamlit as st
import os, sys
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
TELEGRAM_BOT_URL = "https://t.me/SuenaLotteryBot"

st.set_page_config(page_title="Métodos de Pago - SueñaLotto", page_icon="💳", layout="wide")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.shared import render_global_header, api_get, init_session_state

init_session_state()

is_logged_in = bool(st.session_state.get("user"))

render_global_header()

_promo = (api_get("/api/payments/plans") or {}).get("promo", {})
_plan_prices = (api_get("/api/payments/plans") or {}).get("plans", {})
_lifetime_price = _promo.get("promo_price", _plan_prices.get("lifetime", {}).get("amount", 50.0)) if _promo.get("active") else _plan_prices.get("lifetime", {}).get("amount", 99.99)
_pro_price = _plan_prices.get("pro", {}).get("amount", 1.99)

_manual_pay_info = {}
try:
    import httpx as _httpx
    _r_mp = _httpx.get(f"{API_URL}/api/payments/manual/info", timeout=5)
    if _r_mp.status_code == 200:
        _manual_pay_info = _r_mp.json() or {}
except Exception:
    pass

st.markdown("""
<style>
    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #0f172a;
        --bg-card: rgba(30, 41, 59, 0.9);
        --border-color: rgba(51, 65, 85, 0.8);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent: #fbbf24;
        --danger: #ef4444;
        --success: #22c55e;
        --info: #3b82f6;
        --purple: #8b5cf6;
        --card-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .stApp { background: radial-gradient(900px 700px at 12% -8%, rgba(139, 92, 246, 0.16), transparent 60%), radial-gradient(900px 500px at 95% 0%, rgba(59, 130, 246, 0.14), transparent 55%), radial-gradient(900px 700px at 50% 115%, rgba(251, 191, 36, 0.10), transparent 60%), var(--bg-primary); }
    .hero { text-align: center; padding: 0.5rem 0 1rem; }
    .hero h1 { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #ef4444, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; letter-spacing: -1px; }
    .hero p { color: var(--text-secondary); font-size: 0.85rem; max-width: 600px; margin: 0 auto; }
    .pay-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; backdrop-filter: blur(8px); box-shadow: var(--card-shadow); }
    .pay-card h3 { color: var(--text-primary); margin-bottom: 0.5rem; font-weight: 700; }
    .pay-card p { color: var(--text-secondary); font-size: 0.9rem; }
    .pay-method { display: inline-flex; align-items: center; gap: 0.4rem; border-radius: 2rem; padding: 0.25rem 0.9rem; font-size: 0.75rem; font-weight: 700; margin-bottom: 0.75rem; }
    .pay-method.qvapay { background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.45); color: #c4b5fd; }
    .pay-method.manual { background: rgba(255,107,0,0.12); border: 1px solid rgba(255,152,56,0.5); color: #fdba74; }
    .step { display: flex; gap: 0.75rem; margin: 0.5rem 0; align-items: flex-start; }
    .step-num { flex-shrink: 0; width: 1.7rem; height: 1.7rem; border-radius: 50%; background: rgba(251,191,36,0.15); border: 1px solid rgba(251,191,36,0.4); color: #fbbf24; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; margin-top: 0.1rem; }
    .step-body { color: var(--text-secondary); font-size: 0.9rem; }
    .step-body b { color: var(--text-primary); }
    .pay-note { background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.35); border-radius: 0.75rem; padding: 0.75rem 1rem; margin: 0.5rem 0; color: #7dd3fc; font-size: 0.85rem; }
    .pay-warn { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.35); border-radius: 0.75rem; padding: 0.75rem 1rem; margin: 0.5rem 0; color: #fca5a5; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>💳 Métodos de Pago</h1><p>Aprende a pagar tu plan Pro o De por Vida paso a paso, tanto por Qvapay como por Transfermóvil / MLC.</p></div>', unsafe_allow_html=True)

# ─── Comparación de métodos ───────────────────────────────────────────────
st.markdown("""
<div class="pay-card">
    <h3>¿Qué método me conviene?</h3>
    <div style="background:#0f172a;border:1px solid #334155;border-radius:0.75rem;padding:0.75rem 1rem;margin-bottom:0.75rem;display:flex;gap:1rem;flex-wrap:wrap;">
        <div style="flex:1;min-width:220px;">
            <span class="pay-method qvapay">⚡ Qvapay — automático</span>
            <p><b>Instantáneo.</b> Pagas con CUP o USDT y tu plan se activa solo en segundos, sin esperar a nadie. Ideal si ya tienes saldo en Qvapay.</p>
        </div>
        <div style="flex:1;min-width:220px;">
            <span class="pay-method manual">📲 Transfermóvil / MLC — manual</span>
            <p><b>Para usuarios en Cuba.</b> Pagas por transferencia y el administrador verifica tu comprobante y activa el plan minutos después. Necesitas contacto con el soporte.</p>
        </div>
    </div>
    <div class="pay-note">💡 <b>Tip:</b> si nunca has usado Qvapay y estás en Cuba, la vía <b>Transfermóvil/MLC</b> suele ser más directa. Si ya tienes saldo en Qvapay o tarjetas internacionales, <b>Qvapay</b> es más rápido.</div>
</div>
""", unsafe_allow_html=True)

# ─── Método 1: Qvapay ─────────────────────────────────────────────────────
st.markdown("""
<div class="pay-card">
    <span class="pay-method qvapay">⚡ Método 1 · Automático</span>
    <h3>Pagar con Qvapay (CUP / USDT)</h3>
    <p>Qvapay es una pasarela de pago cubana que acepta <b>CUP</b> y <b>USDT</b> (cripto). El pago se confirma automáticamente y tu plan se activa al instante.</p>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="step"><div class="step-num">1</div><div class="step-body"><b>Crea una cuenta en Qvapay.</b> Regístrate en <a href="https://qvapay.com" style="color:#c4b5fd;">qvapay.com</a> con tu email y verifica tu teléfono.</div></div>
<div class="step"><div class="step-num">2</div><div class="step-body"><b>Consigue saldo (CUP o USDT).</b> Si ya tienes USDT en cualquier exchange, envíalo a tu dirección de Qvapay. Si solo tienes CUP, compra USDT en Qvapay mediante transferencia <b>Transfermóvil</b> (P2P/OTC) o usa el saldo directo en CUP si la factura lo permite.</div></div>
<div class="step"><div class="step-num">3</div><div class="step-body"><b>Inicia el pago en la app.</b> Elige tu plan (Pro o De por Vida) y el método <b>"Qvapay (automático)"</b>. Se abrirá la pasarela con la factura ya generada.</div></div>
<div class="step"><div class="step-num">4</div><div class="step-body"><b>Confirma el pago.</b> Revisa el <b>monto</b> que aparece y confirma. La app te redirige a una pantalla de <b>"Pago Exitoso"</b> cuando se confirme.</div></div>
<div class="step"><div class="step-num">5</div><div class="step-body"><b>Disfruta tu plan.</b> Tu cuenta queda activada automáticamente (de inmediato, sin esperar a nadie).</div></div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="pay-warn">⚠️ <b>Importante:</b> asegúrate de tener saldo <b>suficiente</b> antes de pagar. Si la factura vence o el pago falla, el enlace de pago caduca: vuelve a la app y genera uno nuevo. Si tienes problemas recargando saldo, el Método 2 (Transfermóvil/MLC) es buena alternativa.</div>
</div>
""", unsafe_allow_html=True)

# ─── Método 2: Transfermóvil / MLC ────────────────────────────────────────
st.markdown("""
<div class="pay-card">
    <span class="pay-method manual">📲 Método 2 · Manual</span>
    <h3>Pagar con Transfermóvil / MLC (para Cuba)</h3>
    <p>Sin tarjeta internacional ni crypto. Pagas por <b>Transfermóvil</b> o <b>Enzona</b> a la cuenta que te indique el soporte, subes tu comprobante y el administrador activa tu plan.</p>
""", unsafe_allow_html=True)

_paso_cuba = ("""
<div class="step"><div class="step-num">1</div><div class="step-body"><b>Elige el método manual.</b> Al comprar tu plan, selecciona <b>"Transfermóvil / MLC (manual)"</b> en lugar de Qvapay.</div></div>
""")

_pay_data_lines = []
if _manual_pay_info.get("owner"):
    _pay_data_lines.append(f"Titular: <b>{_manual_pay_info['owner']}</b>")
if _manual_pay_info.get("account"):
    _pay_data_lines.append(f"Número/cuenta: <b>{_manual_pay_info['account']}</b>")
if _manual_pay_info.get("phone"):
    _pay_data_lines.append(f"Teléfono: <b>{_manual_pay_info['phone']}</b>")
if _manual_pay_info.get("reference"):
    _pay_data_lines.append(f"Referencia a escribir: <b>{_manual_pay_info['reference']}</b>")
if _manual_pay_info.get("telegram"):
    _pay_data_lines.append(f"Telegram: <b>{_manual_pay_info['telegram']}</b>")
_paso2_body = (
    "<b>Usa los datos de la cuenta.</b> La cuenta para transferir está configurada:<br>🧾 "
    + " · ".join(_pay_data_lines)
    if _pay_data_lines
    else "<b>Contacta al soporte para recibir los datos.</b> Escribe al bot de Telegram <b>@SuenaLotteryBot</b> con el motivo <b>'Usuarios en Cuba — métodos de pago'</b>."
)

st.markdown(_paso_cuba + f"""
<div class="step"><div class="step-num">2</div><div class="step-body">{_paso2_body} Debes transferir <b>${_lifetime_price:.2f}</b> (plan De por Vida) o <b>${_pro_price:.2f}/mes (Pro)</b>.</div></div>
<div class="step"><div class="step-num">3</div><div class="step-body"><b>Haz la transferencia.</b> Por <b>Transfermóvil</b> (MLC/USD) o <b>Enzona</b>, por el monto exacto indicado.</div></div>
<div class="step"><div class="step-num">4</div><div class="step-body"><b>Sube el comprobante.</b> En el formulario de pago manual de la app, adjunta la <b>captura o PDF</b> de la transferencia y deja tu <b>nombre + teléfono</b> para identificarte.</div></div>
<div class="step"><div class="step-num">5</div><div class="step-body"><b>Espera la confirmación.</b> El administrador verifica el pago (generalmente en <b>minutos</b>) y activa tu plan automáticamente. Recibirás un correo de recibo y verás tu plan activo en la app.</div></div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="pay-warn">⚠️ <b>No transfieras sin confirmar los datos.</b> Comunícate primero con el soporte para recibir la cuenta correcta y el monto exacto. Nunca uses datos de terceros no verificados.</div>
</div>
""", unsafe_allow_html=True)

# ─── Precios / Promo ──────────────────────────────────────────────────────
st.markdown(f"""
<div class="pay-card">
    <h3>💰 Precios actuales</h3>
    <div style="display:flex;gap:1rem;flex-wrap:wrap;">
        <div style="flex:1;min-width:200px;background:#0f172a;border:1px solid #334155;border-radius:0.75rem;padding:1rem;text-align:center;">
            <div style="color:#94a3b8;font-size:0.85rem;">Pro — mensual</div>
            <div style="color:#fbbf24;font-size:1.6rem;font-weight:800;">${_pro_price:.2f}</div>
            <div style="color:#64748b;font-size:0.75rem;">Todo el contenido Pro por un mes</div>
        </div>
        <div style="flex:1;min-width:200px;background:#0f172a;border:1px solid rgba(251,191,36,0.4);border-radius:0.75rem;padding:1rem;text-align:center;">
            <div style="color:#fbbf24;font-size:0.85rem;">De por Vida {'· 🔥 PROMO' if _promo.get('active') else ''}</div>
            <div style="color:#fbbf24;font-size:1.6rem;font-weight:800;">${_lifetime_price:.2f}</div>
            <div style="color:#64748b;font-size:0.75rem;">{"Precio normal: <s>$" + str(_promo.get('full_price', _lifetime_price)) + "</s> · quedan " + str(_promo.get('remaining', 0)) + " cupos" if _promo.get('active') else 'Acceso Pro de por vida, sin renovaciones'}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Comprar ahora ────────────────────────────────────────────────────────
st.markdown("""
<div class="pay-card">
    <h3>🚀 ¿Listo para activar tu plan?</h3>
    <p>Ve a la página principal con tu sesión iniciada, elige tu plan y el método de pago. Si tienes cualquier duda, escríbenos por Telegram.</p>
</div>
""", unsafe_allow_html=True)

_user = st.session_state.get("user") or {}
tg_text = f"Necesito ayuda para pagar mi plan (Métodos de Pago)"
if _user.get("username"):
    tg_text += f"\nUsuario: {_user['username']}"
st.link_button("💬 Pedir ayuda con el pago por Telegram", f"{TELEGRAM_BOT_URL}?text={quote(tg_text)}", type="primary", use_container_width=True)

if not is_logged_in:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;color:var(--text-secondary);font-size:0.9rem;">'
        '¿Ya sabes cómo pagar? Vuelve a crear tu cuenta o inicia sesión.</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔙 Volver al Login / Registro", use_container_width=True, type="primary"):
        st.switch_page(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard.py")))
