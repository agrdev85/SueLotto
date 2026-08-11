import streamlit as st
import os, sys
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
TELEGRAM_BOT_URL = "https://t.me/SuenaLotteryBot"

st.set_page_config(page_title="Soporte - SueñaLotto", page_icon="🛟", layout="wide")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.shared import render_global_header, api_get, init_session_state

init_session_state()

if not st.session_state.get("user"):
    st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">Acceso Restringido</h2><p style="color:#94a3b8;">Necesitas iniciar sesión.</p></div>', unsafe_allow_html=True)
    st.stop()

render_global_header()

st.markdown("""
<style>
    .sup-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; backdrop-filter: blur(8px); box-shadow: var(--card-shadow); }
    .sup-card h3 { color: var(--text-primary); margin-bottom: 0.5rem; font-weight: 700; }
    .sup-card p { color: var(--text-secondary); font-size: 0.9rem; }
    .sup-badge { display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.35); color: #93c5fd; border-radius: 2rem; padding: 0.25rem 0.9rem; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.75rem; }
    .sup-badge.cuba { background: rgba(59,130,246,0.15); border-color: rgba(59,130,246,0.45); color: #60a5fa; }
    .sup-badge.promo { background: rgba(251,191,36,0.12); border-color: rgba(251,191,36,0.4); color: #fbbf24; }
    .sup-badge.tg { background: rgba(56,189,248,0.12); border-color: rgba(56,189,248,0.45); color: #38bdf8; }
    .sup-highlight { background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(139,92,246,0.12)); border: 1px solid rgba(99,102,241,0.4); border-radius: 0.75rem; padding: 1rem; margin: 0.75rem 0; }
    .sup-highlight p { margin: 0.25rem 0; }
    .sup-faq { border-bottom: 1px solid rgba(51,65,85,0.6); padding: 0.6rem 0; }
    .sup-faq:last-child { border-bottom: none; }
    .sup-faq b { color: var(--text-primary); }
    .sup-faq p { margin: 0.2rem 0 0; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🛟 Soporte y Ayuda</h1><p>Estamos aquí para ayudarte con tu cuenta, suscripciones, pagos y mucho más</p></div>', unsafe_allow_html=True)

# ─── ¿Qué hace esta página? ────────────────────────────────────────────────
st.markdown("""
<div class="sup-card">
    <span class="sup-badge">💬 Centro de ayuda oficial</span>
    <h3>¿En qué podemos ayudarte?</h3>
    <p>Este es el canal oficial de atención al usuario de SueñaLotto. A través de esta página puedes:</p>
    <p>✅ Reportar problemas con tu cuenta o acceso &nbsp;·&nbsp; ✅ Consultar sobre planes y suscripciones &nbsp;·&nbsp; ✅
    Resolver dudas de <strong>pagos</strong>, especialmente si estás en <strong>Cuba</strong> &nbsp;·&nbsp; ✅
    Consultar <strong>códigos promocionales</strong> disponibles &nbsp;·&nbsp; ✅ Recibir ayuda técnica con la app.</p>
    <p>Toda la atención se realiza a través de <strong>Telegram</strong>. Escribe al bot oficial
    <strong>@SuenaLotteryBot</strong> con el formulario de abajo y tu consulta llegará con el <strong>Motivo</strong>
    ya indicado como asunto del mensaje.</p>
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns(2)

# ─── Usuarios en Cuba ───────────────────────────────────────────────────────
with c1:
    st.markdown("""
<div class="sup-card">
    <span class="sup-badge cuba">🇨🇺 Usuarios en Cuba</span>
    <h3>Pagos sin tarjeta internacional</h3>
    <p>Si estás en Cuba y no puedes acceder a métodos de pago internacionales
    (tarjetas, PayPal, etc.), <strong>no te preocupes</strong>: tenemos alternativas pensadas para ti.</p>
    <div class="sup-highlight">
        <p>💠 Pago en <strong>CUP</strong> o <strong>USDT</strong> mediante Qvapay</p>
        <p>📲 Transferencia a tu monedero (Zelle / USD / CUP)</p>
        <p>🎟️ Acceso a <strong>códigos promocionales</strong> exclusivos</p>
    </div>
    <p>Escríbenos al bot de Telegram eligiendo el motivo <strong>"Usuarios en Cuba — métodos de pago"</strong> e
    indica el método de pago al que tienes acceso. Te indicaremos la vía más cómoda para activar tu plan Pro o De por Vida.</p>
</div>
""", unsafe_allow_html=True)

# ─── Códigos promocionales ──────────────────────────────────────────────────
with c2:
    _plans = api_get("/api/payments/plans") or {}
    _promo = _plans.get("promo", {})
    st.markdown("""
<div class="sup-card">
    <span class="sup-badge promo">🎟️ Códigos promocionales</span>
    <h3>Promociones vigentes</h3>
""", unsafe_allow_html=True)
    if _promo.get("active"):
        st.markdown(
            f"""
            <div class="sup-highlight" style="border-color:rgba(251,191,36,0.5);">
                <p style="color:#fbbf24;font-weight:700;">🔥 Promoción De por Vida: ${_promo.get('promo_price', 50.0):.2f}</p>
                <p>Precio normal: <s>${_promo.get('full_price', 99.99):.2f}</s></p>
                <p>Quedan <strong>{_promo.get('remaining', 0)}</strong> cupos con descuento.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("""
        <p style="margin-top:0.5rem;">
        ¿Quieres un <strong>código promocional</strong> adicional o un descuento especial?
        Escríbenos por <strong>Telegram</strong> eligiendo el motivo <strong>"Códigos promocionales"</strong> y cuéntanos tu caso.
        Si estás en Cuba, revisa la sección anterior.</p>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sup-highlight">
            <p>Actualmente no hay promociones activas.</p>
        </div>
        <p style="margin-top:0.5rem;">Los códigos promocionales y descuentos se publican aquí cuando están disponibles.
        También puedes solicitarlos a través de <strong>Telegram</strong>.</p>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Contacto por Telegram ───────────────────────────────────────────────────
st.markdown("""
<div class="sup-card">
    <span class="sup-badge tg">📨 Escríbenos por Telegram</span>
    <h3>Contacta con soporte</h3>
    <p>Completa el formulario y pulsa <strong>"Enviar por Telegram"</strong>. Se abrirá el chat con el bot oficial
    <strong>@SuenaLotteryBot</strong> con el <strong>Motivo de tu consulta</strong> listo como asunto del mensaje:
    solo tendrás que pulsar <strong>Enviar</strong> 🔘.</p>
</div>
""", unsafe_allow_html=True)

_user = st.session_state.get("user", {})
with st.form("support_tg_form"):
    col_a, col_b = st.columns(2)
    with col_a:
        sup_name = st.text_input("Tu usuario", value=_user.get("username", ""), key="sup_name")
    with col_b:
        sup_subject = st.selectbox(
            "Motivo de tu consulta",
            [
                "Pagos y suscripciones",
                "Usuarios en Cuba — métodos de pago",
                "Códigos promocionales",
                "Problemas con mi cuenta o acceso",
                "Error o fallo en la app",
                "Otra consulta",
            ],
            key="sup_subject",
        )
    sup_msg = st.text_area(
        "Detalle de tu consulta (opcional)",
        placeholder="Cuéntanos tu consulta con el mayor detalle posible…",
        height=120,
        key="sup_msg",
    )
    sup_send = st.form_submit_button("💬 Enviar por Telegram", type="primary")

if sup_send:
    tg_text = f"Motivo: {sup_subject}"
    if sup_name.strip() and sup_name.strip() != _user.get("username", ""):
        tg_text += f"\nUsuario: {sup_name.strip()}"
    elif _user.get("username"):
        tg_text += f"\nUsuario: {_user['username']}"
    if sup_msg.strip():
        tg_text += f"\n\nMensaje:\n{sup_msg.strip()}"
    st.session_state["tg_url"] = f"{TELEGRAM_BOT_URL}?text={quote(tg_text)}"
    st.rerun()

tg_url = st.session_state.get("tg_url")
if tg_url:
    st.markdown(
        f'<div class="sup-highlight" style="border-color:rgba(56,189,248,0.5);margin-top:0.75rem;">'
        f'<p style="color:#38bdf8;font-weight:700;">Tu mensaje está listo en Telegram 🟦</p>'
        f'<p>Pulsa el botón de abajo. En el chat del bot, dale a <strong>Iniciar/START</strong> si es la primera vez '
        f'y luego a <strong>Enviar ▶</strong>: el Motivo ya estará escrito como asunto.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.link_button("🟦 Abrir Telegram y enviar", tg_url, type="primary", use_container_width=True)
    if st.button("↩️ Hacer otra consulta"):
        st.session_state.pop("tg_url", None)
        st.rerun()
    st.markdown(
        f'<p style="text-align:center;margin-top:0.5rem;font-size:0.8rem;color:#64748b;">'
        f'¿Prefieres escribir directo? <a href="{TELEGRAM_BOT_URL}" style="color:#38bdf8;">Abrir @SuenaLotteryBot</a>'
        f' y escribe tu mensaje tú mismo.</p>',
        unsafe_allow_html=True,
    )

# ─── Preguntas frecuentes ────────────────────────────────────────────────────
st.markdown("""
<div class="sup-card">
    <span class="sup-badge">❓ Preguntas frecuentes</span>
    <h3>Respuestas rápidas</h3>
    <div class="sup-faq"><b>¿Cómo contacto el soporte?</b><p>Por <strong>Telegram</strong>, escribiendo al bot @SuenaLotteryBot. Usa el formulario de arriba para no olvidar de indicar el motivo de tu consulta.</p></div>
    <div class="sup-faq"><b>¿Qué incluye el plan De por vida?</b><p>Todo el contenido Pro de por vida: estadísticas, matriz charada, adivinanzas con IA y búsquedas sin límite. Sin renovaciones.</p></div>
    <div class="sup-faq"><b>¿Cómo actualizo mi plan?</b><p>Desde la página principal, en la sección de planes, elige Pro o De por Vida y sigue el flujo de pago. Si estás en Cuba, contacta por Telegram para alternativas.</p></div>
    <div class="sup-faq"><b>¿Los códigos promocionales son gratis?</b><p>Sí. Los códigos y descuentos se publican en esta página o se entregan a través del soporte.</p></div>
    <div class="sup-faq"><b>¿Qué hago si olvidé mi contraseña?</b><p>Usa la opción "¿Olvidaste tu contraseña?" en la pantalla de inicio de sesión. Recibirás un enlace por email.</p></div>
</div>
""", unsafe_allow_html=True)