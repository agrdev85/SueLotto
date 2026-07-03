import streamlit as st
import httpx
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(
    page_title="SueñaLotto",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }

    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #0f172a;
        --bg-card: rgba(30, 41, 59, 0.9);
        --bg-card-hover: rgba(30, 41, 59, 0.95);
        --border-color: rgba(51, 65, 85, 0.8);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent: #fbbf24;
        --accent-secondary: #f59e0b;
        --danger: #ef4444;
        --success: #22c55e;
        --info: #3b82f6;
        --purple: #8b5cf6;
        --card-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    .light-mode {
        --bg-primary: #f8fafc;
        --bg-secondary: #e2e8f0;
        --bg-card: rgba(255, 255, 255, 0.95);
        --bg-card-hover: rgba(255, 255, 255, 1);
        --border-color: rgba(203, 213, 225, 0.8);
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --card-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }

    .stApp { background: var(--bg-primary); }
    .light-mode .stApp { background: var(--bg-primary); }
    .stAppDeployButton, .stMainMenu, #MainMenu, footer { display: none !important; visibility: hidden !important; }
    header[data-testid="stHeader"] { background: rgba(15, 23, 42, 0.95) !important; backdrop-filter: blur(12px); border-bottom: 1px solid rgba(251, 191, 36, 0.15); padding: 0.3rem 1rem !important; }
    .app-header { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 0.25rem 0; }
    .app-header-center { flex: 1; text-align: center; }
    .app-header-center h1 { margin: 0; font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 1px; }
    .app-header-center span { color: #64748b; font-size: 0.7rem; display: block; margin-top: -2px; }
    .app-header-right { display: flex; align-items: center; gap: 0.75rem; min-width: 180px; justify-content: flex-end; }
    .user-badge { background: linear-gradient(135deg, #334155, #1e293b); border: 1px solid #475569; border-radius: 2rem; padding: 0.25rem 0.75rem 0.25rem 0.25rem; display: flex; align-items: center; gap: 0.5rem; }
    .user-avatar { width: 1.6rem; height: 1.6rem; border-radius: 50%; background: linear-gradient(135deg, #fbbf24, #f59e0b); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.7rem; color: #0f172a; }
    .user-info { line-height: 1.2; }
    .user-name { color: #f1f5f9; font-size: 0.75rem; font-weight: 600; }
    .user-time { color: #64748b; font-size: 0.6rem; }
    .card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; backdrop-filter: blur(8px); box-shadow: var(--card-shadow); }
    .card h3 { color: var(--text-primary); margin-bottom: 0.5rem; font-weight: 700; }
    .hero { text-align: center; padding: 0.5rem 0 1rem; }
    .hero h1 { font-size: 2.8rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #ef4444, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; letter-spacing: -1px; }
    .hero p { color: var(--text-secondary); font-size: 0.9rem; max-width: 600px; margin: 0 auto; }
    .sparkle { background: radial-gradient(circle at 50% 0%, rgba(251,191,36,0.08), transparent 70%); }
    .auth-container { max-width: 420px; margin: 2rem auto; }
    .tier-card { background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.9)); border: 1px solid rgba(51,65,85,0.8); border-radius: 1rem; padding: 1.5rem; text-align: center; height: 100%; }
    .tier-card.pro { border-color: #fbbf24; box-shadow: 0 0 20px rgba(251,191,36,0.1); }
    .tier-card.lifetime { border-color: #8b5cf6; box-shadow: 0 0 20px rgba(139,92,246,0.1); }
    .tier-price { font-size: 2.5rem; font-weight: 900; color: #fbbf24; }
    .tier-price span { font-size: 1rem; color: #64748b; }
    .feature-yes { color: #22c55e; }
    .feature-no { color: #64748b; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; background: rgba(30,41,59,0.5); border-radius: 0.75rem; padding: 0.25rem; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 0.5rem; padding: 0.4rem 1.2rem; color: #94a3b8; font-size: 0.85rem; border: none; transition: all 0.2s; }
    .stTabs [aria-selected="true"] { background: #334155; color: #fbbf24; font-weight: 600; }
    div[data-testid="stForm"] { border: none; padding: 0; }
    .stTextInput>div>div>input { background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }
    .stTextInput>div>div>input:focus { border-color: #fbbf24 !important; box-shadow: 0 0 0 2px rgba(251,191,36,0.2) !important; }
    .stNumberInput>div>div>input { background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }
    .stSelectbox>div>div>div { background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }
    .stDateInput>div>div>input { background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }

    /* ─── Sorteo Cards ─── */
    .sorteo-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; box-shadow: var(--card-shadow); transition: transform 0.2s, box-shadow 0.2s; animation: fadeSlideIn 0.5s ease-out both; }
    .sorteo-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.4); }
    .sorteo-card.media { border-left: 4px solid #f97316; }
    .sorteo-card.tarde { border-left: 4px solid #3b82f6; }
    .sorteo-card.noche { border-left: 4px solid #475569; }
    .sorteo-card .horario-badge { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.2rem 0.75rem; border-radius: 2rem; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .sorteo-card .horario-badge.media { background: rgba(249,115,22,0.15); color: #f97316; border: 1px solid rgba(249,115,22,0.3); }
    .sorteo-card .horario-badge.noche { background: rgba(100,116,139,0.15); color: #cbd5e1; border: 1px solid rgba(100,116,139,0.3); }
    .sorteo-card .fecha-text { color: var(--text-muted); font-size: 0.75rem; }
    .sorteo-card .fijo-number { font-size: 3rem; font-weight: 900; text-align: center; padding: 0.25rem 0; color: var(--text-primary); letter-spacing: 4px; line-height: 1; }
    .sorteo-card .corridos-label { color: var(--text-muted); font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 0.4rem; }
    .sorteo-card .corridos-digits { display: flex; justify-content: center; gap: 0.5rem; }
    .sorteo-card .corridos-digit { display: inline-flex; align-items: center; justify-content: center; width: 2.2rem; height: 2.2rem; font-weight: 800; font-size: 1rem; border-radius: 50%; }
    .sorteo-card .corridos-digit.media { background: linear-gradient(135deg, #f97316, #ea580c); color: white; }
    .sorteo-card .corridos-digit.noche { background: linear-gradient(135deg, #475569, #334155); color: white; border: 1px solid #64748b; }
    .sorteo-card .social-bar { display: flex; gap: 0.75rem; margin-top: 0.75rem; padding-top: 0.65rem; border-top: 1px solid var(--border-color); }
    .sorteo-card .social-btn { background: none; border: 1px solid var(--border-color); color: var(--text-muted); font-size: 0.7rem; padding: 0.25rem 0.65rem; border-radius: 2rem; cursor: pointer; transition: all 0.2s; }
    .sorteo-card .social-btn:hover { background: var(--bg-card-hover); color: var(--text-primary); }

    /* ─── List View ─── */
    .sorteo-list-row { display: grid; grid-template-columns: 1fr 1.5fr 0.8fr 2fr 0.8fr; gap: 0.5rem; align-items: center; padding: 0.6rem 1rem; border-bottom: 1px solid var(--border-color); font-size: 0.85rem; color: var(--text-primary); transition: background 0.2s; }
    .sorteo-list-row:hover { background: rgba(59,130,246,0.05); }
    .sorteo-list-row.header { color: var(--text-muted); font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid var(--border-color); }
    .sorteo-list-row .list-fijo { font-weight: 800; font-size: 1.1rem; color: var(--accent); }

    /* ─── Fade animation ─── */
    @keyframes fadeSlideIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

    /* ─── Toggle buttons ─── */
    .toggle-group { display: flex; gap: 0.3rem; background: rgba(30,41,59,0.5); border-radius: 0.5rem; padding: 0.2rem; width: fit-content; }
    .toggle-btn { background: transparent; border: none; color: var(--text-muted); font-size: 0.8rem; padding: 0.35rem 0.8rem; border-radius: 0.4rem; cursor: pointer; transition: all 0.2s; }
    .toggle-btn.active { background: #334155; color: var(--accent); font-weight: 600; }

    /* ─── Bet cards ─── */
    .bet-stat-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 0.75rem; padding: 1rem; text-align: center; }
    .bet-stat-card .stat-value { font-size: 1.6rem; font-weight: 800; color: var(--text-primary); }
    .bet-stat-card .stat-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.2rem; }
    .bet-stat-card .stat-value.positive { color: var(--success); }
    .bet-stat-card .stat-value.negative { color: var(--danger); }
    .bet-stat-card .stat-value.accent { color: var(--accent); }
    .bet-stat-card .stat-value.info { color: var(--info); }
</style>
""", unsafe_allow_html=True)

API = API_URL

def api_get(path, params=None):
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = httpx.get(f"{API}{path}", params=params, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:300] if e.response.text else str(e)
        st.caption(f"⚠️ {detail}")
        return None
    except Exception as e:
        st.caption(f"⚠️ {path}: {e}")
        return None

def api_post(path, json_data=None):
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = httpx.post(f"{API}{path}", json=json_data or {}, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:300] if e.response.text else str(e)
        st.caption(f"⚠️ {detail}")
        return None
    except Exception as e:
        st.caption(f"⚠️ {path}: {e}")
        return None

st.session_state.setdefault("token", None)
st.session_state.setdefault("user", None)
st.session_state.setdefault("login_time", None)
st.session_state.setdefault("page", "sorteos")
st.session_state.setdefault("show_auth", False)
st.session_state.setdefault("view_mode", "cards")
st.session_state.setdefault("theme", "dark")

# ─── Auth Gate (must be first) ──────────────────────────────────

if not st.session_state.get("user"):
    st.markdown("""
<style>
    .stAppDeployButton, .stMainMenu, #MainMenu, footer { display: none !important; visibility: hidden !important; }
    header[data-testid="stHeader"], header { display: none !important; }
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
                        st.session_state["show_auth"] = False
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
        with tab_register:
            with st.form("register_form"):
                ru = st.text_input("Usuario", placeholder="Elige un nombre", key="reg_user")
                re = st.text_input("Email", placeholder="tu@email.com", key="reg_email")
                rp = st.text_input("Contraseña", type="password", placeholder="Mínimo 4 caracteres", key="reg_pass")
                plan_opts = {"free": "Gratis", "pro": "Pro Mensual — $1/mes", "lifetime": "De por Vida — $50 único"}
                plan_sel = st.radio("Elige tu plan", options=list(plan_opts.keys()), format_func=lambda x: plan_opts[x], index=0)
                if st.form_submit_button("Crear Cuenta", type="primary", width='stretch'):
                    res = api_post("/api/auth/register", {"username": ru, "email": re, "password": rp, "tier": plan_sel})
                    if res and "access_token" in res:
                        st.session_state["token"] = res["access_token"]
                        st.session_state["user"] = res["user"]
                        st.session_state["login_time"] = time.time()
                        st.session_state["show_auth"] = False
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
                '<div class="tier-card pro"><h4 style="color:#fbbf24;">Pro Mensual</h4>'
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
            st.markdown(
                '<div class="tier-card lifetime"><h4 style="color:#8b5cf6;">De por Vida</h4>'
                '<div class="tier-price">$50<span> único</span></div>'
                '<div style="text-align:left;margin-top:1rem;font-size:0.85rem;">'
                '<p><span class="feature-yes">✅</span> Todo Pro</p>'
                '<p><span class="feature-yes">✅</span> Actualizaciones gratis</p>'
                '<p><span class="feature-yes">✅</span> Acceso vitalicio</p>'
                '<p><span class="feature-yes">✅</span> Nuevas funciones</p>'
                '<p><span class="feature-yes">✅</span> Sin ads</p>'
                '<p><span class="feature-yes">✅</span> Soporte VIP</p></div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ─── Header (logged in only) ─────────────────────────────────────

user_data = st.session_state.get("user")
user_cols = st.columns([1, 2, 1])
with user_cols[1]:
    st.markdown(
        '<div class="app-header-center">'
        '<h1>SueñaLotto</h1>'
        '<span>Florida Lottery • Pick 3 & Pick 4</span>'
        '</div>',
        unsafe_allow_html=True,
    )
with user_cols[2]:
    elapsed = ""
    if st.session_state.get("login_time"):
        secs = int(time.time() - st.session_state["login_time"])
        if secs < 60: elapsed = f"{secs}s"
        elif secs < 3600: elapsed = f"{secs//60}m"
        else: elapsed = f"{secs//3600}h {(secs%3600)//60}m"
    initial = user_data["username"][0].upper() if user_data["username"] else "?"
    uc1, uc2 = st.columns([1, 0.3])
    with uc1:
        st.markdown(
            f'<div class="app-header-right">'
            f'<div class="user-badge">'
            f'<div class="user-avatar">{initial}</div>'
            f'<div class="user-info">'
            f'<div class="user-name">{user_data["username"]}</div>'
            f'<div class="user-time">{elapsed}</div>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )
    with uc2:
        if st.button("🚪", key="logout_btn"):
            for k in ["token", "user", "login_time", "show_auth", "view_mode", "theme"]:
                st.session_state.pop(k, None)
            st.rerun()

# ─── Theme toggle ──────────────────────────────────────────────────

if st.session_state.get("theme") == "light":
    st.markdown("""
<style>
    .stApp { background: #f8fafc !important; }
    .card { background: rgba(255,255,255,0.95) !important; border-color: rgba(203,213,225,0.8) !important; }
    .hero p, .app-header-center span { color: #475569 !important; }
    .card h3 { color: #0f172a !important; }
    .sorteo-card { background: rgba(255,255,255,0.95) !important; border-color: rgba(203,213,225,0.8) !important; }
    .sorteo-card .fijo-number { color: #0f172a !important; }
    .sorteo-card .horario-badge.media { background: rgba(249,115,22,0.1) !important; }
    .sorteo-card .horario-badge.noche { background: rgba(100,116,139,0.1) !important; color: #475569 !important; border-color: rgba(100,116,139,0.3) !important; }
    .sorteo-card .corridos-digit.media { background: linear-gradient(135deg, #f97316, #ea580c) !important; }
    .sorteo-card .corridos-digit.noche { background: #e2e8f0 !important; color: #475569 !important; border: 1px solid #cbd5e1 !important; }
    .sorteo-list-row { color: #0f172a !important; }
    .sorteo-list-row.header { color: #64748b !important; }
    .tier-card { background: rgba(255,255,255,0.95) !important; border-color: rgba(203,213,225,0.8) !important; }
    .tier-card h4 { color: #0f172a !important; }
    ul li { color: #475569 !important; }
    div[data-testid="stForm"] input, .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input { background: white !important; border-color: #cbd5e1 !important; color: #0f172a !important; }
    h1, h2, h3, h4, h5 { color: #0f172a !important; }
</style>
""", unsafe_allow_html=True)

tier_info = api_get("/api/auth/tier")
if not tier_info:
    tier_info = {"tier": "free", "can_use_historica": False, "can_use_suenos": False, "can_use_adivinanzas": False, "can_use_matriz": False, "suenos_today": 0, "suenos_limit": 1, "historica_today": 0, "historica_limit": 3}

st.markdown(f'<div class="hero sparkle"><h1>📅 Sorteos</h1><p>Resultados en vivo • Análisis Charada • Predicciones inteligentes</p></div>', unsafe_allow_html=True)

# ─── Toolbar: view toggle, theme toggle ──────────────────────────

tool_cols = st.columns([1.5, 1, 1.5])
with tool_cols[0]:
    st.markdown('<div style="padding:0.3rem 0;color:#94a3b8;font-size:0.85rem;">📅 Últimos 3 días</div>', unsafe_allow_html=True)
with tool_cols[1]:
    view_mode = st.session_state.get("view_mode", "cards")
    if st.button("📋 Lista" if view_mode == "cards" else "📇 Tarjetas", key="toggle_view"):
        st.session_state["view_mode"] = "list" if view_mode == "cards" else "cards"
        st.rerun()
with tool_cols[2]:
    cur_theme = st.session_state.get("theme", "dark")
    theme_btn = "☀️ Claro" if cur_theme == "dark" else "🌙 Oscuro"
    if st.button(theme_btn, key="toggle_theme"):
        st.session_state["theme"] = "light" if cur_theme == "dark" else "dark"
        st.rerun()

# ─── Fetch results (last 3 days) ─────────────────────────────────

resultados = []
for i in range(3):
    d = date.today() - timedelta(days=i)
    r = api_get("/api/resultados/por-fecha", {"fecha": d.isoformat()})
    if r:
        resultados.extend(r)

if not resultados:
    st.info("📭 No hay sorteos registrados para este período.")
else:
    pick3 = [r for r in resultados if r.get("juego") == "Pick 3"]
    pick4 = [r for r in resultados if r.get("juego") == "Pick 4"]

    for label, items in [("Pick 3", pick3), ("Pick 4", pick4)]:
        if not items:
            continue
        is_p3 = label == "Pick 3"
        st.markdown(f'<h3 style="color:var(--text-primary);margin:0.5rem 0;">{label}</h3>', unsafe_allow_html=True)
        sorted_items = sorted(items, key=lambda x: x.get("sorteo", ""))

        if st.session_state.get("view_mode") == "list":
            cols_header = ["Horario", "Fecha", "FIJO" if is_p3 else "CORRIDOS", "Juego"]
            st.markdown(
                f'<div class="sorteo-list-row header">'
                f'<span>{cols_header[0]}</span><span>{cols_header[1]}</span><span>{cols_header[2]}</span><span>{cols_header[3]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for r in sorted_items:
                sorteo_label = {"E": "NOCHE", "M": "MEDIODIA"}.get(r.get("sorteo", ""), r.get("sorteo", ""))
                if is_p3:
                    display_val = f"{r['n1']}{r['n2']}{r['n3']}"
                else:
                    display_val = f"{r['n1']} {r['n2']} {r['n3']} {r['n4']}"
                fecha_str = r.get("fecha", "")
                if isinstance(fecha_str, str) and len(fecha_str) >= 10:
                    try:
                        d = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                        meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
                        fecha_str = f"{d.day} de {meses[d.month-1]} {d.year}"
                    except:
                        pass
                st.markdown(
                    f'<div class="sorteo-list-row">'
                    f'<span>{sorteo_label}</span>'
                    f'<span>{fecha_str}</span>'
                    f'<span class="list-fijo">{display_val}</span>'
                    f'<span>{label}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            cards_container = st.container()
            card_cols = st.columns(2)
            for i, r in enumerate(sorted_items):
                sorteo_label = {"E": "NOCHE", "M": "MEDIODIA"}.get(r.get("sorteo", ""), r.get("sorteo", ""))
                sorteo_css_class = {"E": "noche", "M": "media"}.get(r.get("sorteo", ""), "")
                sorteo_icon = {"E": "🌙", "M": "☀️"}.get(r.get("sorteo", ""), "")
                fecha_str = r.get("fecha", "")
                if isinstance(fecha_str, str) and len(fecha_str) >= 10:
                    try:
                        d = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                        meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
                        fecha_str = f"{d.day} de {meses[d.month-1]} {d.year}"
                    except:
                        pass

                card_col_idx = i % 2
                with card_cols[card_col_idx]:
                    if is_p3:
                        fijo = f"{r['n1']}{r['n2']}{r['n3']}"
                        st.markdown(
                            f'<div class="sorteo-card {sorteo_css_class}" style="animation-delay:{i*0.1}s;">'
                            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">'
                            f'<span class="horario-badge {sorteo_css_class}">{sorteo_icon} {sorteo_label}</span>'
                            f'<span class="fecha-text">{fecha_str}</span>'
                            f'</div>'
                            f'<div class="fijo-number">{fijo}</div>'
                            f'<div style="text-align:center;margin:0.5rem 0;font-size:0.7rem;color:var(--text-muted);font-weight:600;letter-spacing:1px;">FIJO</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        corridos_digits = [str(r['n1']), str(r['n2']), str(r['n3']), str(r['n4'])]
                        corridos_html = "".join(
                            f'<span class="corridos-digit {sorteo_css_class}">{d}</span>'
                            for d in corridos_digits
                        )
                        st.markdown(
                            f'<div class="sorteo-card {sorteo_css_class}" style="animation-delay:{i*0.1}s;">'
                            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">'
                            f'<span class="horario-badge {sorteo_css_class}">{sorteo_icon} {sorteo_label}</span>'
                            f'<span class="fecha-text">{fecha_str}</span>'
                            f'</div>'
                            f'<div style="text-align:center;margin:0.75rem 0;">'
                            f'<span class="corridos-label">CORRIDOS</span>'
                            f'<div class="corridos-digits">{corridos_html}</div>'
                            f'</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

st.markdown("---")

# ─── Statistics Charts ─────────────────────────────────────────────

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
            yaxis=dict(showgrid=False),
            showlegend=False,
        )
        fig.update_traces(marker_line_color="#334155", marker_line_width=1, textposition="outside", textfont_color="#94a3b8", hovertemplate="%{x}<br>%{y} veces<extra></extra>")
        st.plotly_chart(fig, width='stretch')
        st.markdown('<div style="display:flex;gap:1rem;font-size:0.7rem;color:#64748b;"><span>🟡 Decenas</span><span>🔴 Muy frecuente</span><span>🔵 Frecuente</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="card"><h3>🎯 Sugeridos</h3>', unsafe_allow_html=True)
    preds = api_get("/api/predicciones", {"juego": "Pick 3"})
    if not preds:
        st.info("⏳ Cargando datos...")
    else:
        top_preds = preds[:10]
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
            yaxis=dict(showgrid=False),
            showlegend=False,
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



# ─── Dev Admin Panel (always visible in dev mode) ─────────────────
st.markdown("---")
with st.expander("🛠️ Admin / Dev (solo pruebas)", expanded=False):
    adm_user = st.text_input("Usuario para cambiar plan", placeholder="nombre de usuario", key="adm_user")
    adm_tier = st.selectbox("Nuevo plan", ["free", "pro", "lifetime"], key="adm_tier")
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
