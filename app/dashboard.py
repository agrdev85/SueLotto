import streamlit as st
import plotly.express as px
from datetime import date, datetime, timedelta
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Sorteos - SueñaLotto",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.shared import render_global_header, api_get, api_post, init_session_state

init_session_state()



@st.cache_data(ttl=300)
def fetch_plans_data():
    import httpx as _httpx
    try:
        r = _httpx.get(f"{API_URL}/api/payments/plans", timeout=5)
        return r.json()
    except:
        return {}


def _fmt_plan(pid: str, plans: dict, promo: dict) -> str:
    p = plans.get(pid)
    if not p:
        return pid
    amt = p["amount"]
    if pid == "lifetime" and promo.get("active"):
        full = promo.get("full_price", amt)
        return f"De por Vida — ${promo['promo_price']:.2f} (antes ${full:.2f}) 🔥"
    if pid == "pro":
        return f"Pro Mensual — ${amt:.2f}/mes"
    return "Gratis"


_plan_data = fetch_plans_data()
_plans_api = _plan_data.get("plans", {})
_promo_api = _plan_data.get("promo", {})

if not st.session_state.get("user"):
    st.markdown("""
<style>
    .stAppDeployButton, .stMainMenu, #MainMenu, footer { display: none !important; visibility: hidden !important; }
    header[data-testid="stHeader"], header { display: none !important; }

    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #0f172a;
        --bg-card: rgba(30, 41, 59, 0.92);
        --border-color: rgba(51, 65, 85, 0.8);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent: #fbbf24;
        --danger: #ef4444;
        --success: #22c55e;
        --info: #3b82f6;
        --purple: #8b5cf6;
    }

    .stApp {
        background:
            radial-gradient(900px 700px at 12% -8%, rgba(139, 92, 246, 0.16), transparent 60%),
            radial-gradient(900px 500px at 95% 0%, rgba(59, 130, 246, 0.14), transparent 55%),
            radial-gradient(900px 700px at 50% 115%, rgba(251, 191, 36, 0.10), transparent 60%),
            var(--bg-primary);
    }

    .hero.sparkle { text-align: center; padding: 2.4rem 0.5rem 0.9rem; position: relative; }
    .hero.sparkle h1 {
        font-size: 2.7rem; font-weight: 900; letter-spacing: -1px; margin-bottom: 0.35rem;
        background: linear-gradient(135deg, #fbbf24, #ef4444, #8b5cf6);
        background-size: 300% 100%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: heroShine 5s linear infinite;
    }
    .hero.sparkle::after { content: "🎰"; position: absolute; top: 0.5rem; right: 8%; font-size: 2.1rem; animation: floatY 3.2s ease-in-out infinite; filter: drop-shadow(0 0 10px rgba(251,191,36,0.5)); }
    .hero.sparkle p { color: var(--text-secondary); font-size: 0.9rem; max-width: 640px; margin: 0 auto; line-height: 1.5; }
    @keyframes gradientMove { to { background-position: 300% 0; } }
    @keyframes floatY { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
    @keyframes fadeSlideIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

    .card {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.96));
        border: 1px solid var(--border-color);
        border-radius: 1.25rem;
        padding: 1.4rem 1.1rem 1.2rem;
        box-shadow: 0 14px 44px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
        animation: fadeSlideIn 0.5s ease-out both;
    }
    .card h3 { color: var(--text-primary); margin-bottom: 0.9rem; letter-spacing: 0.3px; }

    .stTabs [data-baseweb="tab-list"] { gap: 0.35rem; background: rgba(30, 41, 59, 0.6); border: 1px solid var(--border-color); border-radius: 0.9rem; padding: 0.3rem; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 0.6rem; padding: 0.4rem 1rem; color: var(--text-secondary); font-size: 0.85rem; border: 1px solid transparent; transition: all 0.2s; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #0f172a; font-weight: 800; box-shadow: 0 4px 14px rgba(251,191,36,0.35); }

    .stTextInput>div>div>input, .stTextInput input { background: rgba(15, 23, 42, 0.9) !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.65rem !important; padding: 0.55rem 0.8rem !important; }
    .stTextInput>div>div>input:focus, .stTextInput input:focus { border-color: #fbbf24 !important; box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.25) !important; }
    .stTextInput>div>div>input::placeholder { color: #64748b !important; }

    .stFormSubmitButton>button, button[kind="primary"] {
        background: linear-gradient(135deg, #fbbf24, #f97316) !important; color: #0f172a !important;
        font-weight: 800 !important; border: none !important; border-radius: 0.65rem !important;
        padding: 0.55rem 1rem !important; transition: all 0.2s ease !important;
        box-shadow: 0 6px 18px rgba(251, 191, 36, 0.3);
    }
    .stFormSubmitButton button:hover, button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 10px 26px rgba(251, 191, 36, 0.45) !important; }

    .stRadio div[role="radiogroup"] { gap: 0.35rem; }
    .stRadio div[role="radiogroup"] label { background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 0.65rem; padding: 0.45rem 0.7rem; font-size: 0.85rem; transition: all 0.2s; }
    .stRadio div[role="radiogroup"] label:has(input:checked) { border-color: #fbbf24; background: rgba(251, 191, 36, 0.1); color: #fbbf24; font-weight: 600; }

    /* ── Planes de precios ─────────────────────────────────── */
    .tier-card {
        background: linear-gradient(170deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.97));
        border: 1px solid var(--border-color);
        border-radius: 1rem;
        padding: 1.25rem 1.05rem 1.05rem;
        text-align: center;
        position: relative;
        height: 100%;
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
        animation: fadeSlideIn 0.55s ease-out both;
    }
    .tier-card:nth-child(2) { animation-delay: 0.08s; }
    .tier-card:nth-child(3) { animation-delay: 0.16s; }
    .tier-card::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 1rem 1rem 0 0; background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.4), transparent); }
    .tier-card:hover { transform: translateY(-4px); box-shadow: 0 14px 34px rgba(0, 0, 0, 0.45); }
    .tier-card h4 { font-size: 0.98rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: 0.3px; }

    .tier-card .tier-badge {
        position: absolute; top: -0.55rem; left: 50%; transform: translateX(-50%);
        background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #0f172a;
        font-size: 0.6rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
        padding: 0.22rem 0.8rem; border-radius: 2rem; white-space: nowrap;
        box-shadow: 0 4px 14px rgba(251, 191, 36, 0.45); z-index: 2;
    }
    .tier-card.pro { border-color: rgba(251, 191, 36, 0.45); background: linear-gradient(170deg, rgba(30, 41, 59, 0.92), rgba(20, 18, 8, 0.98)); }
    .tier-card.pro::before { background: linear-gradient(90deg, transparent, #fbbf24, transparent); }
    .tier-card.pro:hover { box-shadow: 0 14px 34px rgba(0, 0, 0, 0.45), 0 0 28px rgba(251, 191, 36, 0.22); }
    .tier-card.lifetime { border-color: rgba(139, 92, 246, 0.5); background: linear-gradient(170deg, rgba(30, 41, 59, 0.92), rgba(17, 11, 34, 0.98)); }
    .tier-card.lifetime::before { background: linear-gradient(90deg, transparent, #8b5cf6, transparent); }
    .tier-card.lifetime:hover { box-shadow: 0 14px 34px rgba(0, 0, 0, 0.45), 0 0 32px rgba(139, 92, 246, 0.3); }
    .tier-card.lifetime .tier-badge { background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff; box-shadow: 0 4px 14px rgba(139, 92, 246, 0.5); }

    .tier-price { font-size: 2.15rem; font-weight: 900; line-height: 1.05; color: var(--text-primary); margin: 0.2rem 0 0.4rem; }
    .tier-price span { font-size: 0.78rem; font-weight: 600; color: var(--text-muted); }
    .tier-card.pro .tier-price { background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .tier-card.lifetime .tier-price { background: linear-gradient(135deg, #a78bfa, #8b5cf6, #fbbf24); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

    .tier-card p { margin: 0.3rem 0; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.4; }
    .tier-card p span { margin-right: 0.35rem; }
    .feature-yes { color: var(--success); font-weight: 800; }
    .feature-no { color: #64748b; opacity: 0.55; font-weight: 700; }

    /* ── Oferta psicológica de venta ── */
    .promo-flag { display: inline-block; background: linear-gradient(135deg, #ef4444, #f97316); color: #fff; font-size: 0.72rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; padding: 0.28rem 1rem; border-radius: 2rem; box-shadow: 0 0 18px rgba(239, 68, 68, 0.55); animation: promoPulse 1.5s ease-in-out infinite; }
    .promo-price-wrap { display: flex; align-items: baseline; justify-content: center; gap: 0.6rem; margin: 0.4rem 0 0.2rem; flex-wrap: wrap; }
    .promo-old { font-size: 1.15rem; font-weight: 700; color: #94a3b8; text-decoration: line-through; text-decoration-color: #ef4444; text-decoration-thickness: 2px; }
    .promo-new { font-size: 2.3rem; font-weight: 900; line-height: 1; background: linear-gradient(135deg, #fbbf24, #f97316, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 2px 10px rgba(251, 191, 36, 0.5)); }
    .promo-save { display: inline-block; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-size: 0.75rem; font-weight: 800; padding: 0.2rem 0.75rem; border-radius: 2rem; margin-top: 0.35rem; box-shadow: 0 0 14px rgba(34, 197, 94, 0.45); }
    .promo-urgency { margin-top: 0.5rem; font-size: 0.78rem; font-weight: 700; color: #f87171; animation: promoBlink 1.1s ease-in-out infinite; }
    @keyframes promoPulse { 0%, 100% { transform: scale(1); box-shadow: 0 0 12px rgba(239, 68, 68, 0.4); } 50% { transform: scale(1.07); box-shadow: 0 0 28px rgba(239, 68, 68, 0.8); } }
    @keyframes promoBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

    @media (max-width: 640px) {
        .hero.sparkle h1 { font-size: 1.9rem; }
        .hero.sparkle::after { display: none; }
        .tier-price, .promo-new { font-size: 1.8rem; }
        .card { padding: 1rem 0.7rem 0.9rem; }
    }
</style>
""", unsafe_allow_html=True)
    st.markdown('<div class="hero sparkle"><h1>🌟 SueñaLotto</h1><p>Tu guía inteligente para la lotería de Florida. Análisis, estadísticas y la sabiduría de la Charada Cubana.</p></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1.5])
    with col_a:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
        with tab_login:
            with st.form("login_form"):
                u = st.text_input("Usuario", placeholder="Tu nombre de usuario", key="login_user")
                p = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass")
                if st.form_submit_button("Iniciar Sesión", type="primary", width='stretch'):
                    res = api_post("/api/auth/login", {"username": u, "password": p})
                    if res and "access_token" in res:
                        st.session_state["token"] = res["access_token"]
                        st.session_state["user"] = res["user"]
                        st.session_state["login_time"] = time.time()
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
        with tab_register:
            with st.form("register_form"):
                ru = st.text_input("Usuario", placeholder="Elige un nombre", key="reg_user")
                re = st.text_input("Email", placeholder="tu@email.com", key="reg_email")
                rp = st.text_input("Contraseña", type="password", placeholder="Mínimo 4 caracteres", key="reg_pass")
                plan_opts = {
                    "free": "Gratis",
                    "pro": f"Pro Mensual — ${_plans_api.get('pro', {}).get('amount', 1):.2f}/mes",
                    "lifetime": _fmt_plan("lifetime", _plans_api, _promo_api),
                }
                plan_sel = st.radio("Elige tu plan", options=list(plan_opts.keys()), format_func=lambda x: plan_opts[x], index=0)
                if st.form_submit_button("Crear Cuenta", type="primary", width='stretch'):
                    res = api_post("/api/auth/register", {"username": ru, "email": re, "password": rp, "tier": plan_sel})
                    if res and "access_token" in res:
                        st.session_state["token"] = res["access_token"]
                        st.session_state["user"] = res["user"]
                        st.session_state["login_time"] = time.time()
                        st.rerun()
                    else:
                        st.error("Error al registrar. Revisa los datos e intenta de nuevo.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="card"><h3 style="text-align:center;">🚀 Planes</h3>', unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.markdown(
                '<div class="tier-card"><h4 style="color:#94a3b8;">Gratis</h4>'
                '<div class="tier-price">$0<span>/mes</span></div>'
                '<div style="text-align:left;margin-top:1rem;font-size:0.85rem;">'
                '<p><span class="feature-yes">✅</span> Últimos sorteos</p>'
                '<p><span class="feature-yes">✅</span> Búsqueda Histórica</p>'
                '<p><span class="feature-yes">✅</span> Sueños (1/día)</p>'
                '<p><span class="feature-no">❌</span> Estadísticas Pro</p>'
                '<p><span class="feature-no">❌</span> Adivinanzas IA</p>'
                '<p><span class="feature-no">❌</span> Matriz Charada</p></div></div>',
                unsafe_allow_html=True,
            )
        with tc2:
            st.markdown(
                '<div class="tier-card pro"><div class="tier-badge">⭐ Popular</div><h4 style="color:#fbbf24;">Pro Mensual</h4>'
                '<div class="tier-price">$1<span>/mes</span></div>'
                '<div style="text-align:left;margin-top:1rem;font-size:0.85rem;">'
                '<p><span class="feature-yes">✅</span> Todo incluido</p>'
                '<p><span class="feature-yes">✅</span> Sin límites</p>'
                '<p><span class="feature-yes">✅</span> IA + Adivinanzas</p>'
                '<p><span class="feature-yes">✅</span> Estadísticas Pro</p>'
                '<p><span class="feature-yes">✅</span> Matriz Charada</p>'
                '<p><span class="feature-yes">✅</span> Soporte prioritario</p></div></div>',
                unsafe_allow_html=True,
            )
        with tc3:
            _lt = _plans_api.get("lifetime", {})
            _lt_price = _lt.get("amount", 99.99)
            _lt_full = _promo_api.get("full_price", _lt_price)
            _lt_promo_html = ""
            if _promo_api.get("active"):
                _lt_promo_price = _promo_api["promo_price"]
                _lt_save = max(0, _lt_full - _lt_promo_price)
                _lt_pct = round(_lt_save / _lt_full * 100) if _lt_full else 0
                _lt_promo_html = (
                    '<div class="promo-flag">🔥 Oferta imperdible</div>'
                    '<div class="promo-price-wrap">'
                    f'<span class="promo-old">${_lt_full:.2f}</span>'
                    f'<span class="promo-new">${_lt_promo_price:.2f}</span>'
                    '</div>'
                    f'<div class="promo-save">💰 Ahorras ${_lt_save:.2f} · {_lt_pct}% OFF</div>'
                    f'<div class="promo-urgency">⚠️ ¡Solo quedan {_promo_api["remaining"]} cupos con descuento!</div>'
                )
            _lt_display_html = _lt_promo_html or f'<div class="tier-price">${_lt_price:.2f}<span> único</span></div>'
            st.markdown(
                f'<div class="tier-card lifetime"><div class="tier-badge">💎 Recomendado</div><h4 style="color:#8b5cf6;">De por Vida</h4>'
                f'{_lt_display_html}'
                f'<div style="text-align:left;margin-top:1rem;font-size:0.85rem;">'
                f'<p><span class="feature-yes">✅</span> Todo Pro</p>'
                f'<p><span class="feature-yes">✅</span> Actualizaciones gratis</p>'
                f'<p><span class="feature-yes">✅</span> Acceso vitalicio</p>'
                f'<p><span class="feature-yes">✅</span> Nuevas funciones</p>'
                f'<p><span class="feature-yes">✅</span> Sin ads</p>'
                f'<p><span class="feature-yes">✅</span> Soporte VIP</p></div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

render_global_header()

tier_info = api_get("/api/auth/tier")
if not tier_info:
    tier_info = {"tier": "free", "can_use_historica": False, "can_use_suenos": False, "can_use_adivinanzas": False, "can_use_matriz": False, "suenos_today": 0, "suenos_limit": 1, "historica_today": 0, "historica_limit": 3}

st.markdown("""
<style>
    .sorteo-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 1rem; padding: 1rem; margin-bottom: 0.75rem; box-shadow: var(--card-shadow); transition: transform 0.2s, box-shadow 0.2s; animation: fadeSlideIn 0.5s ease-out both; }
    .sorteo-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.4); }
    .sorteo-card.media { border-left: 4px solid #f97316; }
    .sorteo-card.noche { border-left: 4px solid #475569; }
    .sorteo-card .horario-badge { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.15rem 0.6rem; border-radius: 2rem; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .sorteo-card .horario-badge.media { background: rgba(249,115,22,0.15); color: #f97316; border: 1px solid rgba(249,115,22,0.3); }
    .sorteo-card .horario-badge.noche { background: rgba(100,116,139,0.15); color: #cbd5e1; border: 1px solid rgba(100,116,139,0.3); }
    .sorteo-card .fecha-text { color: var(--text-muted); font-size: 0.7rem; font-weight: 600; }
    .sorteo-card .card-body { display: flex; align-items: center; gap: 1rem; padding-top: 0.5rem; }
    .sorteo-card .fijo-section { flex: 1; text-align: center; }
    .sorteo-card .fijo-number { font-size: 2.8rem; font-weight: 900; letter-spacing: 4px; line-height: 1; color: var(--text-primary); }
    .sorteo-card .fijo-label { font-size: 0.6rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.1rem; }
    .sorteo-card .corridos-section { flex: 1; text-align: center; }
    .sorteo-card .corridos-digits { display: flex; justify-content: center; gap: 0.35rem; flex-wrap: wrap; }
    .sorteo-card .corridos-digit { display: inline-flex; align-items: center; justify-content: center; width: 2rem; height: 2rem; font-weight: 800; font-size: 0.9rem; border-radius: 50%; }
    .sorteo-card .corridos-digit.media { background: linear-gradient(135deg, #f97316, #ea580c); color: white; }
    .sorteo-card .corridos-digit.noche { background: linear-gradient(135deg, #475569, #334155); color: white; border: 1px solid #64748b; }
    .sorteo-card .corridos-label { font-size: 0.6rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.25rem; }

    .sorteo-card.day-card { background: linear-gradient(180deg, var(--bg-card) 0%, rgba(30,41,59,0.7) 100%); border-color: var(--border-color); padding: 0; overflow: hidden; }
    .sorteo-card.day-card .day-header { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 1rem; background: rgba(0,0,0,0.15); border-bottom: 1px solid var(--border-color); }
    .sorteo-card.day-card .day-header .day-date { font-size: 0.85rem; font-weight: 700; color: var(--text-primary); }
    .sorteo-card.day-card .day-header .day-count { font-size: 0.65rem; color: var(--text-muted); }
    .sorteo-card.day-card .draw-card { padding: 0.75rem 1rem; border-bottom: 1px solid rgba(51,65,85,0.4); }
    .sorteo-card.day-card .draw-card:last-child { border-bottom: none; }
    .sorteo-card.day-card .draw-card.media-draw { background: rgba(249,115,22,0.03); }
    .sorteo-card.day-card .draw-card.noche-draw { background: rgba(100,116,139,0.03); }

    .sorteo-list-row { display: grid; grid-template-columns: 1fr 1.5fr 2fr 2fr; gap: 0.5rem; align-items: center; padding: 0.5rem 1rem; border-bottom: 1px solid var(--border-color); font-size: 0.8rem; color: var(--text-primary); transition: background 0.2s; }
    .sorteo-list-row:hover { background: rgba(59,130,246,0.05); }
    .sorteo-list-row.header { color: var(--text-muted); font-weight: 600; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid var(--border-color); }
    .sorteo-list-row .list-fijo { font-weight: 800; font-size: 1rem; color: var(--accent); }
    .sorteo-list-row .list-corridos { font-weight: 700; font-size: 0.9rem; color: var(--text-secondary); }

    .sorteo-card.noche-draw .fijo-number { font-size: 2.2rem; }
    .sorteo-card.media-draw .fijo-number { font-size: 2.2rem; }

    .day-divider { display: flex; align-items: center; gap: 0.75rem; margin: 1rem 0 0.5rem; }
    .day-divider .line { flex: 1; height: 1px; background: var(--border-color); }
    .day-divider .day-label { font-size: 0.8rem; font-weight: 700; color: var(--text-primary); white-space: nowrap; }
    .day-divider .day-label small { color: var(--text-muted); font-weight: 400; font-size: 0.7rem; }

    .scraped-game-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 0.75rem; padding: 1rem; margin-bottom: 0.75rem; }
    .scraped-game-card .game-name { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.3rem; }
    .scraped-game-card .game-date { font-size: 0.7rem; color: var(--text-muted); }
    .scraped-game-card .game-numbers { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.5rem; }
    .scraped-game-card .game-numbers span { display: inline-flex; align-items: center; justify-content: center; width: 2rem; height: 2rem; border-radius: 50%; font-weight: 700; font-size: 0.85rem; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; }
    .scraped-game-card .game-numbers .xb { background: linear-gradient(135deg, #ef4444, #dc2626); }
    .scraped-game-card .game-numbers .xmb { background: linear-gradient(135deg, #22c55e, #16a34a); }
    .scraped-game-card .game-bonus-label { display: block; margin-top: 0.5rem; font-size: 0.7rem; color: var(--text-muted); }

    /* ── Indicador "descubre más abajo" ───────────────────────── */
    .discover-more { display: flex; justify-content: center; margin: 1.6rem 0 0.4rem; }
    .discover-card { position: relative; width: min(600px, 94vw); border-radius: 1.2rem; padding: 1.5rem 1.8rem 1.1rem; text-align: center; background: linear-gradient(165deg, rgba(30,41,59,0.9), rgba(15,23,42,0.92)); overflow: hidden; animation: discoverGlow 3.6s ease-in-out infinite; cursor: pointer; transition: transform 0.25s ease; }
    .discover-card:hover { transform: translateY(-3px); }
    .discover-card:active { transform: translateY(0) scale(0.98); }
    .discover-card.clicking { animation: discoverClick 0.7s cubic-bezier(0.34, 1.56, 0.64, 1); }
    .discover-card::after { content: ""; position: absolute; top: 0; left: -80%; width: 50%; height: 100%; background: linear-gradient(105deg, transparent, rgba(255,255,255,0.22), transparent); transform: skewX(-20deg); opacity: 0; pointer-events: none; }
    .discover-card.clicking::after { animation: discoverShine 0.8s ease forwards; }
    @keyframes discoverClick { 0% { transform: scale(1); } 35% { transform: scale(1.05); box-shadow: 0 0 60px rgba(251,191,36,0.55); } 100% { transform: scale(1); } }
    @keyframes discoverShine { 0% { left: -80%; opacity: 0; } 30% { opacity: 1; } 100% { left: 130%; opacity: 0; } }
    .discover-card::before { content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 2px; background: conic-gradient(from 210deg, #fbbf24, #8b5cf6, #3b82f6, #ef4444, #fbbf24); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; animation: discoverRotate 7s linear infinite; pointer-events: none; }
    .discover-spark { position: absolute; top: -0.9rem; right: 12%; font-size: 1.7rem; animation: discoverFloat 3.2s ease-in-out infinite; filter: drop-shadow(0 0 8px rgba(251,191,36,0.6)); }
    .discover-title { font-size: 1.2rem; font-weight: 800; letter-spacing: 0.5px; background: linear-gradient(90deg, #fbbf24, #f97316, #8b5cf6, #fbbf24); background-size: 300% 100%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: discoverShimmer 4s linear infinite; }
    .discover-sub { font-size: 0.82rem; color: var(--text-muted); margin-top: 0.2rem; }
    .discover-pills { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.45rem; margin-top: 0.8rem; }
    .discover-pill { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.3px; padding: 0.28rem 0.9rem; border-radius: 2rem; background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.3); color: #93c5fd; transition: transform 0.2s, box-shadow 0.2s; }
    .discover-pill.plan { background: rgba(139,92,246,0.14); border-color: rgba(139,92,246,0.4); color: #c4b5fd; }
    .discover-pill:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(59,130,246,0.25); }
    .discover-chevs { display: flex; justify-content: center; gap: 0.4rem; margin-top: 0.55rem; }
    .discover-chevs span { font-size: 1.5rem; font-weight: 700; color: #fbbf24; animation: discoverBounce 1.6s ease-in-out infinite; }
    .discover-chevs span:nth-child(2) { animation-delay: 0.2s; }
    .discover-chevs span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes discoverRotate { to { filter: hue-rotate(360deg); } }
    @keyframes discoverShimmer { to { background-position: 300% 0; } }
    @keyframes discoverFloat { 0%, 100% { transform: translateY(0) rotate(-10deg); } 50% { transform: translateY(-7px) rotate(10deg); } }
    @keyframes discoverBounce { 0%, 100% { transform: translateY(0); opacity: 0.35; } 50% { transform: translateY(7px); opacity: 1; } }
    @keyframes discoverGlow { 0%, 100% { box-shadow: 0 0 0 rgba(251,191,36,0); } 50% { box-shadow: 0 0 36px rgba(139,92,246,0.32); } }

    /* ── Oferta psicológica de venta (rojo=urgencia, dorado=valor, verde=ahorro) ── */
    .promo-flag { display: inline-block; background: linear-gradient(135deg, #ef4444, #f97316); color: #fff; font-size: 0.72rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; padding: 0.28rem 1rem; border-radius: 2rem; box-shadow: 0 0 18px rgba(239,68,68,0.55); animation: promoPulse 1.5s ease-in-out infinite; }
    .promo-price-wrap { display: flex; align-items: baseline; justify-content: center; gap: 0.6rem; margin: 0.5rem 0 0.2rem; flex-wrap: wrap; }
    .promo-old { font-size: 1.15rem; font-weight: 700; color: #94a3b8; text-decoration: line-through; text-decoration-color: #ef4444; text-decoration-thickness: 2px; }
    .promo-new { font-size: 2.3rem; font-weight: 900; line-height: 1; background: linear-gradient(135deg, #fbbf24, #f97316, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 2px 10px rgba(251,191,36,0.5)); }
    .promo-save { display: inline-block; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-size: 0.75rem; font-weight: 800; padding: 0.2rem 0.75rem; border-radius: 2rem; margin-top: 0.3rem; box-shadow: 0 0 14px rgba(34,197,94,0.45); }
    .promo-urgency { margin-top: 0.5rem; font-size: 0.78rem; font-weight: 700; color: #f87171; animation: promoBlink 1.1s ease-in-out infinite; }
    @keyframes promoPulse { 0%, 100% { transform: scale(1); box-shadow: 0 0 12px rgba(239,68,68,0.4); } 50% { transform: scale(1.07); box-shadow: 0 0 28px rgba(239,68,68,0.8); } }
    @keyframes promoBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

    @media (max-width: 640px) {
        .sorteo-card .fijo-number { font-size: 2rem; }
        .sorteo-card.noche-draw .fijo-number { font-size: 1.8rem; }
        .sorteo-card.media-draw .fijo-number { font-size: 1.8rem; }
        .sorteo-card .card-body { flex-direction: column; gap: 0.5rem; }
        .sorteo-card .corridos-digit { width: 1.7rem; height: 1.7rem; font-size: 0.75rem; }
        .sorteo-list-row { grid-template-columns: 1fr 1.2fr 1.5fr 1.5fr; font-size: 0.7rem; gap: 0.3rem; padding: 0.4rem 0.5rem; }
        .sorteo-card.day-card .draw-card { padding: 0.5rem 0.75rem; }
        .discover-card { padding: 1.2rem 1rem 0.9rem; }
        .discover-title { font-size: 1.05rem; }
    }
</style>
""", unsafe_allow_html=True)

user_tier = (tier_info or {}).get("tier", "free")
if user_tier == "free":
    st.warning("🔒 Tienes el plan **Gratis**. Actualiza a **Pro** ($1/mes) o **De por Vida** ($50) para desbloquear estadísticas avanzadas, matriz charada, y adivinanzas IA.")

st.markdown('<div class="hero"><h1>📅 Sorteos</h1><p>Resultados en vivo • Pick 3 & Pick 4 • Análisis Charada</p></div>', unsafe_allow_html=True)

st.html(
    """
<div class="discover-more">
    <div class="discover-card" id="discover-card">
        <div class="discover-spark">✨</div>
        <div class="discover-title">¡Hay más por descubrir!</div>
        <div class="discover-sub">Sigue bajando — aquí abajo te espera todo lo que hace de SueñaLotto tu mejor aliado.</div>
        <div class="discover-pills">
            <span class="discover-pill plan">🚀 Planes Pro</span>
            <span class="discover-pill">💳 Actualiza tu cuenta</span>
        </div>
        <div class="discover-chevs"><span>⌄</span><span>⌄</span><span>⌄</span></div>
    </div>
</div>
<script>
(function () {
    var card = document.getElementById('discover-card');
    if (!card || card.dataset.bound) return;
    card.dataset.bound = '1';
    card.addEventListener('click', function () {
        var target = document.getElementById('planes-section');
        card.classList.remove('clicking');
        void card.offsetWidth;
        card.classList.add('clicking');
        setTimeout(function () { card.classList.remove('clicking'); }, 750);
        if (target) {
            setTimeout(function () {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 180);
        }
    });
})();
</script>
""",
    unsafe_allow_javascript=True,
)

ultima_fecha = api_get("/api/resultados/ultima-fecha")
if not ultima_fecha:
    st.info("📭 No hay resultados registrados en la base de datos.")
    st.stop()

try:
    latest = datetime.strptime(ultima_fecha["fecha"][:10], "%Y-%m-%d").date()
except:
    latest = date.today()

# ─── Toolbar ────────────────────────────────────────────────────

tool_cols = st.columns([1.2, 0.8, 0.8, 1.2])
with tool_cols[0]:
    sort_order = st.session_state.get("sorteo_sort_asc", False)
    order_label = "⬆️ Ascendente" if sort_order else "⬇️ Descendente"
    if st.button(order_label, key="sort_order_btn"):
        st.session_state["sorteo_sort_asc"] = not sort_order
        st.rerun()

with tool_cols[1]:
    cur_filter = st.session_state.get("sorteo_filter", "all")
    filter_map = {"all": "Todos", "M": "☀️ Mediodía", "E": "🌙 Noche"}
    filter_label = filter_map.get(cur_filter, "Todos")
    if st.button(f"Filtro: {filter_label}", key="filter_btn"):
        opts = ["all", "M", "E"]
        idx = opts.index(cur_filter) if cur_filter in opts else 0
        next_idx = (idx + 1) % len(opts)
        st.session_state["sorteo_filter"] = opts[next_idx]
        st.rerun()

with tool_cols[2]:
    view_mode = st.session_state.get("view_mode", "cards")
    view_icon = "📋" if view_mode == "cards" else "📇"
    view_label = "Lista" if view_mode == "cards" else "Tarjetas"
    if st.button(f"{view_icon} {view_label}", key="toggle_view"):
        st.session_state["view_mode"] = "list" if view_mode == "cards" else "cards"
        st.rerun()

with tool_cols[3]:
    st.markdown(f'<div style="text-align:right;color:var(--text-muted);font-size:0.75rem;padding-top:0.3rem;">Última fecha: {latest.strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)

# ─── Fetch Results ──────────────────────────────────────────────

dias_a_mostrar = [latest - timedelta(days=i) for i in range(3)]

resultados_por_dia = {}
for d in dias_a_mostrar:
    r = api_get("/api/resultados/por-fecha", {"fecha": d.isoformat()})
    if r:
        sorteo_filter = st.session_state.get("sorteo_filter", "all")
        if sorteo_filter != "all":
            r = [x for x in r if x.get("sorteo") == sorteo_filter]
        resultados_por_dia[d] = r

sort_order = st.session_state.get("sorteo_sort_asc", False)
dias_ordenados = sorted(resultados_por_dia.keys(), reverse=not sort_order)

# ─── Render Results ─────────────────────────────────────────────

view_mode = st.session_state.get("view_mode", "cards")

if view_mode == "cards":
    for dia in dias_ordenados:
        items = resultados_por_dia.get(dia, [])
        if not items:
            continue

        dia_str = dia.strftime("%A, %d de %B %Y")
        dia_str = dia_str.replace("Monday", "Lunes").replace("Tuesday", "Martes").replace("Wednesday", "Miércoles")
        dia_str = dia_str.replace("Thursday", "Jueves").replace("Friday", "Viernes").replace("Saturday", "Sábado").replace("Sunday", "Domingo")
        months = {"January":"enero","February":"febrero","March":"marzo","April":"abril","May":"mayo","June":"junio",
                  "July":"julio","August":"agosto","September":"septiembre","October":"octubre","November":"noviembre","December":"diciembre"}
        for eng, esp in months.items():
            dia_str = dia_str.replace(eng, esp)

        draw_labels = {"E": "NOCHE", "M": "MEDIODÍA"}
        draw_icons = {"E": "🌙", "M": "☀️"}
        draw_css = {"E": "noche", "M": "media"}

        st.markdown(
            f'<div class="day-divider"><span class="line"></span>'
            f'<span class="day-label">{dia_str} <small>({len(items)} sorteos)</small></span>'
            f'<span class="line"></span></div>',
            unsafe_allow_html=True,
        )

        for draw in ["M", "E"]:
            draw_items = [it for it in items if it.get("sorteo") == draw]
            if not draw_items:
                continue

            p3 = next((it for it in draw_items if it.get("juego") == "Pick 3"), None)
            p4 = next((it for it in draw_items if it.get("juego") == "Pick 4"), None)

            is_noche = draw == "E"
            card_css = draw_css.get(draw, "noche")
            label = draw_labels.get(draw, draw)
            icon = draw_icons.get(draw, "")
            is_large = is_noche

            if p3:
                fijo_num = f"{p3['n1']}{p3['n2']}{p3['n3']}"
            elif p4:
                fijo_num = f"{p4['n1']}{p4['n2']}{p4['n3']}{p4['n4']}"
            else:
                fijo_num = "---"

            corridos_digits = []
            if p4:
                corridos_digits = [str(p4['n1']), str(p4['n2']), str(p4['n3']), str(p4['n4'])]
                if p4.get('n4') is not None:
                    pass
            elif p3:
                corridos_digits = [str(p3['n1']), str(p3['n2']), str(p3['n3'])]

            fijo_size = "2.8rem" if is_large else "2.2rem"
            badge_size = "0.7rem" if is_large else "0.6rem"

            st.markdown(
                f'<div class="sorteo-card {card_css}">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span class="horario-badge {card_css}">{icon} {label}</span>'
                f'<div style="display:flex;align-items:center;gap:0.5rem;">'
                f'{f"<span style=font-size:0.65rem;color:var(--text-muted);>P3</span>" if p3 else ""}'
                f'{f"<span style=font-size:0.65rem;color:var(--text-muted);>P4</span>" if p4 else ""}'
                f'</div>'
                f'</div>'
                f'<div class="card-body">'
                f'<div class="fijo-section">'
                f'<div class="fijo-number" style="font-size:{fijo_size};">{fijo_num}</div>'
                f'<div class="fijo-label">FIJO</div>'
                f'</div>'
                f'<div class="corridos-section">'
                f'<div class="corridos-label">CORRIDOS</div>'
                f'<div class="corridos-digits">'
                + "".join(f'<span class="corridos-digit {card_css}">{d}</span>' for d in corridos_digits) +
                f'</div></div></div></div>',
                unsafe_allow_html=True,
            )
else:
    st.markdown(
        '<div class="sorteo-list-row header">'
        '<span>Horario</span><span>Fecha</span><span>FIJO</span><span>CORRIDOS</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    for dia in dias_ordenados:
        items = resultados_por_dia.get(dia, [])
        if not items:
            continue

        dia_str = dia.strftime("%d/%m/%Y")

        draw_labels = {"E": "🌙 NOCHE", "M": "☀️ MEDIODÍA"}

        for draw in ["M", "E"]:
            draw_items = [it for it in items if it.get("sorteo") == draw]
            if not draw_items:
                continue

            p3 = next((it for it in draw_items if it.get("juego") == "Pick 3"), None)
            p4 = next((it for it in draw_items if it.get("juego") == "Pick 4"), None)

            if p3:
                fijo_list = f"{p3['n1']}{p3['n2']}{p3['n3']}"
            elif p4:
                fijo_list = f"{p4['n1']}{p4['n2']}{p4['n3']}{p4['n4']}"
            else:
                fijo_list = "---"

            corridos_list = []
            if p4:
                corridos_list = [str(p4['n1']), str(p4['n2']), str(p4['n3']), str(p4['n4'])]
            elif p3:
                corridos_list = [str(p3['n1']), str(p3['n2']), str(p3['n3'])]

            label = draw_labels.get(draw, draw)
            corr_str = "-".join(corridos_list) if corridos_list else "---"

            st.markdown(
                f'<div class="sorteo-list-row">'
                f'<span>{label}</span>'
                f'<span>{dia_str}</span>'
                f'<span class="list-fijo">{fijo_list}</span>'
                f'<span class="list-corridos">{corr_str}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ─── Otros Juegos de Florida Lottery (API oficial) ─────────────

st.markdown("---")
st.markdown('<h2 style="color:var(--text-primary);">🎰 Juegos Oficiales de la Florida Lottery</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:var(--text-secondary);font-size:0.85rem;">Resultados oficiales de floridalottery.com (Powerball, Mega Millions, etc.)</p>', unsafe_allow_html=True)

_BONUS_LABEL = {
    "Powerball": "Powerball",
    "Mega Millions": "Mega Ball",
    "Cash4Life": "Cash Ball",
}


def _render_other_game_card(name, date_str, numbers, extra):
    nums_html = "".join(f"<span>{n}</span>" for n in numbers)
    extra_html = "".join(f'<span class="xb">{n}</span>' for n in extra)
    label = _BONUS_LABEL.get(name, "Fireball")
    extra_label = (
        f'<span class="game-bonus-label">{label}: {" · ".join(extra)}</span>'
        if extra else ""
    )
    st.markdown(
        f'<div class="scraped-game-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">'
        f'<div class="game-name">{name}</div>'
        f'<div class="game-date">{date_str}</div>'
        f'</div>'
        f'<div class="game-numbers">{nums_html}{extra_html}</div>'
        f'{extra_label}</div>',
        unsafe_allow_html=True,
    )


otros_juegos = api_get("/api/resultados/otros-juegos")
if otros_juegos and isinstance(otros_juegos, list):
    for game in otros_juegos:
        name = game.get("name", "")
        date_str = game.get("date", "")
        numbers = game.get("numbers", [])
        extra = game.get("extra", [])
        if not name or not numbers:
            continue
        try:
            d = datetime.strptime(date_str, "%m/%d/%Y")
            date_str = d.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            pass
        _render_other_game_card(name, date_str, numbers, extra)
elif otros_juegos is None:
    st.info("💻 No se pudieron obtener datos de la Florida Lottery en este momento.")

# ─── Statistics Charts ──────────────────────────────────────────

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    st.markdown('<div class="card"><h3>🔥 Charada más Frecuente (90d)</h3>', unsafe_allow_html=True)
    charada_freqs = api_get("/api/estadisticas/charada-frecuencias", {"juego": "Pick 3", "dias": 90})
    if not charada_freqs:
        st.info("⏳ Cargando datos...")
    else:
        top = charada_freqs[:20]
        decenas = set(range(0, 100, 10))
        colors = ["#fbbf24" if f["numero"] in decenas else ("#ef4444" if f["frecuencia"] > top[0]["frecuencia"] * 0.7 else "#3b82f6") for f in top]
        fig = px.bar(
            x=[f"{f['numero']:02d}" for f in top],
            y=[f["frecuencia"] for f in top],
            labels={"x": "", "y": ""},
            color=colors,
            color_discrete_map="identity",
            text=[f"{f['numero']:02d}" for f in top],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", height=280, margin=dict(l=10, r=10, t=10, b=20),
            xaxis=dict(tickmode="linear", dtick=1, showgrid=False),
            yaxis=dict(showgrid=False), showlegend=False,
        )
        fig.update_traces(marker_line_color="#334155", marker_line_width=1, textposition="outside", textfont_color="#94a3b8", hovertemplate="%{x}<br>%{y} veces<extra></extra>")
        st.plotly_chart(fig, width='stretch')
        st.markdown('<div style="display:flex;gap:1rem;font-size:0.7rem;color:#64748b;"><span>🟡 Decenas</span><span>🔴 Muy frecuente</span><span>🔵 Frecuente</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="card"><h3>🎯 Sugeridos</h3>', unsafe_allow_html=True)
    preds = api_get("/api/predicciones", {"juego": "Pick 3"})
    if not preds or not isinstance(preds, dict):
        st.info("⏳ Cargando datos...")
    else:
        top_preds = (preds.get("digitos") or [])[:10]
        if not top_preds:
            st.info("⏳ Cargando datos...")
        else:
            pred_colors = ["#ef4444" if p["probabilidad"] > 0.12 else "#fbbf24" if p["probabilidad"] > 0.08 else "#3b82f6" for p in top_preds]
            fig2 = px.bar(
                x=[f"{p['numero']:02d}" for p in top_preds],
                y=[p["probabilidad"] for p in top_preds],
                labels={"x": "", "y": ""},
                color=pred_colors,
                color_discrete_map="identity",
                text=[f"{p['probabilidad']*100:.1f}%" for p in top_preds],
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8", height=280, margin=dict(l=10, r=10, t=10, b=20),
                xaxis=dict(tickmode="linear", dtick=1, showgrid=False),
                yaxis=dict(showgrid=False), showlegend=False,
            )
            fig2.update_traces(marker_line_color="#334155", marker_line_width=1, textposition="outside", textfont_color="#fbbf24", hovertemplate="%{x}<br>%{y:.1%}<extra></extra>")
            st.plotly_chart(fig2, width='stretch')
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

col5, col6 = st.columns(2)
with col5:
    st.markdown('<div class="card"><h3>📊 Top Charada (30d)</h3>', unsafe_allow_html=True)
    charada_freqs = api_get("/api/estadisticas/charada-frecuencias", {"juego": "Pick 3", "dias": 30})
    if charada_freqs and len(charada_freqs) > 0:
        top10 = charada_freqs[:10]
        st.markdown('<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.3rem;">', unsafe_allow_html=True)
        for f in top10:
            n_color = "#fbbf24" if f["numero"] % 10 == 0 else "#e2e8f0"
            st.markdown(
                f'<div style="background:rgba(51,65,85,0.5);padding:0.3rem 0.8rem;border-radius:0.5rem;display:flex;justify-content:space-between;">'
                f'<span style="color:{n_color};font-weight:700;">{f["numero"]:02d}</span>'
                f'<span style="color:#64748b;">{f["frecuencia"]}× ({f["porcentaje"]}%)</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("⏳ Cargando datos...")
    st.markdown('</div>', unsafe_allow_html=True)

with col6:
    st.markdown('<div class="card"><h3>💡 Consejos</h3>', unsafe_allow_html=True)
    st.markdown("""
    <ul style="color:var(--text-secondary);line-height:1.8;font-size:0.85rem;padding-left:1.2rem;">
        <li>🔍 Busca tus <strong>sueños</strong> para números Charada</li>
        <li>📈 Revisa <strong>estadísticas</strong> por período y sorteo</li>
        <li>🧠 Usa la <strong>IA</strong> para interpretar adivinanzas</li>
        <li>🎲 Combina <span style="color:#ef4444;">calientes</span> y <span style="color:#3b82f6;">atrasados</span></li>
        <li>🔟 Las <span style="color:#fbbf24;">decenas</span> tienen significados especiales</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Plans & Payment ────────────────────────────────────────────
st.markdown('<div id="planes-section"></div>', unsafe_allow_html=True)

if st.session_state.pop("_go_to_planes", False):
    st.html("""
<script>
(function () {
    var target = document.getElementById('planes-section');
    if (!target) return;
    var selectors = ['[data-testid="stMain"]', '[data-testid="stAppViewContainer"]', '[data-testid="stApp"]', '[data-testid="stMainBlockContainer"]'];
    var els = selectors.map(function (s) { return document.querySelector(s); }).filter(Boolean);
    setTimeout(function () {
        var done = false;
        for (var i = 0; i < els.length; i++) {
            if (els[i].scrollTop > 0 || els[i].getBoundingClientRect().height > 0) {
                var top = target.getBoundingClientRect().top + els[i].scrollTop - 90;
                els[i].scrollTo({ top: top, behavior: 'smooth' });
                done = true;
                break;
            }
        }
        if (!done) {
            window.scrollTo({ top: target.offsetTop - 90, behavior: 'smooth' });
        }
    }, 350);
})();
</script>
""", unsafe_allow_javascript=True)

st.markdown("---")
st.markdown('<h2 style="color:var(--text-primary);">🚀 Planes</h2>', unsafe_allow_html=True)

_plan_data = fetch_plans_data()
_plans_api = _plan_data.get("plans", {})
_promo_api = _plan_data.get("promo", {})

_lt = _plans_api.get("lifetime", {})
_lt_price = _lt.get("amount", 99.99)
_lt_full = _promo_api.get("full_price", 99.99)

cols_p = st.columns(3)
plan_info = [
    {"id": "free", "name": "Gratis", "price": "$0/mes", "color": "#94a3b8",
     "features": ["Últimos sorteos", "Búsqueda histórica (3/día)", "Sueños (1/día)"]},
    {"id": "pro", "name": "Pro Mensual", "price": f"${_plans_api.get('pro', {}).get('amount', 1):.2f}/mes", "color": "#fbbf24",
     "features": ["Todo incluido", "Sin límites diarios", "Estadísticas avanzadas",
                   "Matriz Charada", "Adivinanzas IA", "Soporte prioritario"]},
    {"id": "lifetime", "name": "De por Vida", "price": f"${_lt_price:.2f} único", "color": "#8b5cf6",
     "features": ["Todo Pro", "Actualizaciones gratis", "Acceso vitalicio",
                   "Nuevas funciones", "Sin anuncios", "Soporte VIP"]},
]
for i, plan in enumerate(plan_info):
    with cols_p[i]:
        is_current = user_tier == plan["id"]
        border = f"2px solid {plan['color']}" if is_current else "1px solid #334155"
        price_html = f'<div style="font-size:2rem;font-weight:800;color:var(--text-primary);margin:0.5rem 0;">{plan["price"]}</div>'
        if plan["id"] == "lifetime" and _promo_api.get("active"):
            _lt_promo_price = _promo_api["promo_price"]
            _lt_full2 = _promo_api.get("full_price", _lt_price)
            _lt_save2 = max(0, _lt_full2 - _lt_promo_price)
            _lt_pct2 = round(_lt_save2 / _lt_full2 * 100) if _lt_full2 else 0
            price_html = (
                '<div class="promo-flag" style="margin-top:0.3rem;">🔥 Oferta imperdible</div>'
                '<div class="promo-price-wrap">'
                f'<span class="promo-old">${_lt_full2:.2f}</span>'
                f'<span class="promo-new">${_lt_promo_price:.2f}</span>'
                '</div>'
                f'<div class="promo-save">💰 Ahorras ${_lt_save2:.2f} · {_lt_pct2}% OFF</div>'
                f'<div class="promo-urgency">⚠️ ¡Solo quedan {_promo_api["remaining"]} cupos!</div>'
            )
        st.markdown(
            f'<div style="background:#1e293b;border:{border};border-radius:1rem;padding:1.5rem;text-align:center;">'
            f'<h3 style="color:{plan["color"]};">{plan["name"]}</h3>'
            f'{price_html}'
            + "".join(f'<p style="color:#94a3b8;font-size:0.85rem;">✓ {f}</p>' for f in plan["features"])
            + (f'<p style="color:#22c55e;font-size:0.8rem;margin-top:0.5rem;">✅ Plan actual</p>'
               if is_current else "")
            + '</div>', unsafe_allow_html=True)

if user_tier == "free":
    st.markdown("---")
    st.markdown('<h3 style="color:#fbbf24;">🔄 Actualizar Plan</h3>', unsafe_allow_html=True)
    buy_plan = st.radio("Selecciona un plan", ["pro", "lifetime"],
                        format_func=lambda x: _fmt_plan(x, _plans_api, _promo_api),
                        horizontal=True)
    if st.button("💳 Ir a Pago", type="primary", use_container_width=True):
        pay_resp = api_post("/api/payments/create", {"plan": buy_plan})
        if pay_resp and pay_resp.get("payment_url"):
            st.markdown(f'<meta http-equiv="refresh" content="0;url={pay_resp["payment_url"]}">', unsafe_allow_html=True)
            st.success(f"Redirigiendo a Qvapay para completar el pago...")
            st.markdown(f'<a href="{pay_resp["payment_url"]}" target="_blank">Haz clic aquí si no redirige automáticamente</a>', unsafe_allow_html=True)
        else:
            st.warning("El sistema de pagos no está disponible en este momento. Contacta al soporte.")

# ─── Admin Panel (protected) ───────────────────────────────────
is_admin_user = user_tier == "admin"
if is_admin_user:
    st.markdown("---")
    with st.expander("🛠️ Admin Panel", expanded=False):
        adm_user = st.text_input("Usuario", placeholder="nombre de usuario", key="adm_user")
        adm_tier = st.selectbox("Plan", ["free", "pro", "lifetime"], key="adm_tier")
        if st.button("Cambiar Plan", key="adm_btn"):
            res = api_post("/api/admin/set-tier", {"username": adm_user, "tier": adm_tier})
            if res and res.get("status") == "ok":
                st.success(f"✅ {adm_user} → {adm_tier}")
                if st.session_state.get("user", {}).get("username") == adm_user:
                    st.session_state["user"]["tier"] = adm_tier
                    st.rerun()
            else:
                st.error("No se pudo cambiar el plan")

st.markdown("""
<div style="text-align:center;padding:2rem;color:#475569;font-size:0.75rem;">
    <p>© 2026 SueñaLotto · Solo para entretenimiento. Juega con responsabilidad.</p>
</div>
""", unsafe_allow_html=True)
