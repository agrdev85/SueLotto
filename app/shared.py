import streamlit as st
import httpx
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")


def api_get(path, params=None):
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = _extract_error(e)
        if e.response.status_code == 429:
            st.toast("⏳ Demasiadas solicitudes. Espera un momento.", icon="⚠️")
        elif e.response.status_code == 401:
            st.toast("🔒 Sesión expirada. Vuelve a iniciar sesión.", icon="⚠️")
            for k in ["token", "user", "login_time"]:
                st.session_state.pop(k, None)
        return None
    except httpx.ConnectError:
        st.toast("🔌 Servidor no disponible. Intenta de nuevo.", icon="⚠️")
        return None
    except:
        return None


def api_post(path, json_data=None):
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = httpx.post(f"{API_URL}{path}", json=json_data or {}, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = _extract_error(e)
        if e.response.status_code == 429:
            st.toast("⏳ Demasiadas solicitudes. Espera un momento.", icon="⚠️")
        elif e.response.status_code == 401:
            st.toast("🔒 Sesión expirada. Vuelve a iniciar sesión.", icon="⚠️")
            for k in ["token", "user", "login_time"]:
                st.session_state.pop(k, None)
        return None
    except httpx.ConnectError:
        st.toast("🔌 Servidor no disponible. Intenta de nuevo.", icon="⚠️")
        return None
    except:
        return None


def _extract_error(e):
    try:
        return e.response.json().get("detail", str(e))
    except:
        return str(e)


SESSION_MAX_SECS = 86400  # 24h absolute

def init_session_state():
    st.session_state.setdefault("token", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("login_time", None)
    st.session_state.setdefault("last_activity", None)
    st.session_state.setdefault("theme", "dark")
    st.session_state.setdefault("view_mode", "cards")
    st.session_state.setdefault("sorteo_sort_asc", False)
    st.session_state.setdefault("sorteo_filter", "all")

def check_session_expired():
    if not st.session_state.get("user"):
        return
    login_time = st.session_state.get("login_time")
    if login_time and time.time() - login_time > SESSION_MAX_SECS:
        for k in ["token", "user", "login_time", "last_activity", "theme", "view_mode", "sorteo_sort_asc", "sorteo_filter"]:
            st.session_state.pop(k, None)
        st.rerun()
    st.session_state["last_activity"] = time.time()


def get_theme_css():
    is_light = st.session_state.get("theme") == "light"
    if is_light:
        return """
<style>
    .stApp { background: #f8fafc !important; }
    header[data-testid="stHeader"] { background: rgba(255,255,255,0.95) !important; border-bottom: 1px solid rgba(203,213,225,0.5) !important; }
    .card { background: rgba(255,255,255,0.95) !important; border-color: rgba(203,213,225,0.8) !important; }
    .card h3 { color: #0f172a !important; }
    h1, h2, h3, h4, h5, h6 { color: #0f172a !important; }
    p, li, .stMarkdown, .element-container { color: #475569 !important; }
    .st-emotion-cache-1avcm0n, .st-emotion-cache-1qpr6sv { color: #0f172a !important; }
    .sorteo-card { background: rgba(255,255,255,0.95) !important; border-color: rgba(203,213,225,0.8) !important; }
    .sorteo-card .fijo-number { color: #0f172a !important; }
    .sorteo-card .horario-badge.noche { background: rgba(100,116,139,0.1) !important; color: #475569 !important; border-color: rgba(100,116,139,0.3) !important; }
    .sorteo-card .corridos-digit.noche { background: #e2e8f0 !important; color: #475569 !important; border: 1px solid #cbd5e1 !important; }
    .sorteo-list-row { color: #0f172a !important; }
    .sorteo-list-row.header { color: #64748b !important; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input { background: white !important; border-color: #cbd5e1 !important; color: #0f172a !important; }
    .bet-stat-card { background: rgba(255,255,255,0.95) !important; border-color: rgba(203,213,225,0.8) !important; }
    .tier-card { background: rgba(255,255,255,0.95) !important; border-color: rgba(203,213,225,0.8) !important; }
    .tier-card h4 { color: #0f172a !important; }
    ul li { color: #475569 !important; }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; }
    .stTabs [aria-selected="true"] { background: #e2e8f0 !important; color: #f59e0b !important; }
    div[data-testid="stForm"] input { background: white !important; border-color: #cbd5e1 !important; color: #0f172a !important; }
    .info-box { background: rgba(59,130,246,0.08) !important; border-color: rgba(59,130,246,0.3) !important; }
    .scraped-game-card { background: rgba(255,255,255,0.95) !important; border-color: rgba(203,213,225,0.8) !important; }
    .scraped-game-card .game-name { color: #0f172a !important; }
    .scraped-game-card .game-numbers span { color: #0f172a !important; }
    .day-divider .day-label { color: #0f172a !important; }
    .day-divider .day-label small { color: #64748b !important; }
    .sorteo-card .fecha-text { color: #64748b !important; }
    .sorteo-card .fijo-number { color: #0f172a !important; }
    .sorteo-card.media .fijo-number { color: #0f172a !important; }
    .sorteo-card.noche .fijo-number { color: #0f172a !important; }
    .sorteo-card .horario-badge.media { background: rgba(249,115,22,0.12) !important; color: #c2410c !important; }
    .sorteo-card .horario-badge.noche { background: rgba(100,116,139,0.12) !important; color: #475569 !important; }
    .sorteo-card .corridos-digit.media { background: linear-gradient(135deg, #f97316, #ea580c) !important; color: white !important; }
    .sorteo-card .corridos-digit.noche { background: #e2e8f0 !important; color: #334155 !important; border: 1px solid #cbd5e1 !important; }
    .num-card { background: white !important; border-color: #e2e8f0 !important; }
    .num-card .num-title { color: #d97706 !important; }
    .num-card.candado { border-color: #22c55e !important; background: rgba(34,197,94,0.03) !important; }
    .pay-row { background: rgba(0,0,0,0.02) !important; }
    .bet-stat-card { background: white !important; border-color: #e2e8f0 !important; }
</style>"""
    return ""


def render_global_header():
    init_session_state()
    check_session_expired()

    user_data = st.session_state.get("user")
    if not user_data:
        return

    theme_css = get_theme_css()

    st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}

    :root {{
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
    }}

    .stAppDeployButton, .stMainMenu, #MainMenu, footer {{ display: none !important; visibility: hidden !important; }}
    header[data-testid="stHeader"] {{ background: rgba(15, 23, 42, 0.98) !important; backdrop-filter: blur(12px); border-bottom: 1px solid rgba(251, 191, 36, 0.15) !important; padding: 0.2rem 0.5rem !important; }}
    .stApp {{ background: var(--bg-primary); }}

    .st-emotion-cache-1mi7n4l {{ gap: 0.25rem !important; }}
    div[data-testid="column"]:has(button[kind="secondary"]) {{ flex: 0 0 auto !important; }}
    button[kind="secondary"] {{ font-size: 0.7rem !important; padding: 0.1rem 0.4rem !important; min-height: unset !important; line-height: 1.5 !important; border-radius: 2rem !important; background: rgba(51,65,85,0.6) !important; border: 1px solid #475569 !important; color: #94a3b8 !important; }}
    button[kind="secondary"]:hover {{ background: #475569 !important; color: #f1f5f9 !important; border-color: #64748b !important; }}
    button[kind="secondary"][data-testid="baseButton-secondary"] {{  }}

    .card {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; backdrop-filter: blur(8px); box-shadow: var(--card-shadow); }}
    .card h3 {{ color: var(--text-primary); margin-bottom: 0.5rem; font-weight: 700; }}
    .hero {{ text-align: center; padding: 0.5rem 0 1rem; }}
    .hero h1 {{ font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #ef4444, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; letter-spacing: -1px; }}
    .hero p {{ color: var(--text-secondary); font-size: 0.85rem; max-width: 600px; margin: 0 auto; }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 0.3rem; background: rgba(30,41,59,0.5); border-radius: 0.75rem; padding: 0.25rem; }}
    .stTabs [data-baseweb="tab"] {{ background: transparent; border-radius: 0.5rem; padding: 0.3rem 1rem; color: #94a3b8; font-size: 0.8rem; border: none; transition: all 0.2s; }}
    .stTabs [aria-selected="true"] {{ background: #334155; color: #fbbf24; font-weight: 600; }}

    div[data-testid="stForm"] {{ border: none; padding: 0; }}
    .stTextInput>div>div>input {{ background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }}
    .stTextInput>div>div>input:focus {{ border-color: #fbbf24 !important; box-shadow: 0 0 0 2px rgba(251,191,36,0.2) !important; }}
    .stNumberInput>div>div>input {{ background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }}
    .stSelectbox>div>div>div {{ background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }}
    .stDateInput>div>div>input {{ background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }}

    .toggle-group {{ display: flex; gap: 0.2rem; background: rgba(30,41,59,0.5); border-radius: 0.5rem; padding: 0.15rem; width: fit-content; flex-wrap: wrap; }}
    .toggle-btn {{ background: transparent; border: none; color: var(--text-muted); font-size: 0.75rem; padding: 0.3rem 0.6rem; border-radius: 0.4rem; cursor: pointer; transition: all 0.2s; white-space: nowrap; }}
    .toggle-btn.active {{ background: #334155; color: var(--accent); font-weight: 600; }}

    @keyframes fadeSlideIn {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    .info-box {{ background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.25); border-radius: 0.75rem; padding: 0.75rem 1rem; margin: 0.5rem 0; font-size: 0.85rem; color: var(--text-secondary); }}

    @media (max-width: 640px) {{
        .global-header {{ gap: 0.25rem; }}
        .global-header-left .logo {{ font-size: 0.9rem; }}
        .global-header-center {{ font-size: 0.6rem; }}
        .user-name {{ font-size: 0.6rem; }}
        .theme-btn, .logout-btn {{ font-size: 0.65rem; padding: 0.15rem 0.4rem; }}
        .user-avatar {{ width: 1.2rem; height: 1.2rem; font-size: 0.55rem; }}
        .hero h1 {{ font-size: 1.8rem; }}
    }}
</style>
{theme_css}
""", unsafe_allow_html=True)

    elapsed = ""
    if st.session_state.get("login_time"):
        secs = int(time.time() - st.session_state["login_time"])
        if secs < 60: elapsed = f"{secs}s"
        elif secs < 3600: elapsed = f"{secs//60}m"
        else: elapsed = f"{secs//3600}h {(secs%3600)//60}m"

    initial = user_data["username"][0].upper() if user_data["username"] else "?"
    cur_theme = st.session_state.get("theme", "dark")

    theme_icon = "☀️" if cur_theme == "dark" else "🌙"
    theme_label = "Claro" if cur_theme == "dark" else "Oscuro"

    hc = st.columns([1.2, 1.6, 0.7, 0.7, 0.6])
    with hc[0]:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:0.3rem;">'
            '<span style="font-size:1rem;font-weight:800;background:linear-gradient(135deg,#fbbf24,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🌟 SueñaLotto</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    with hc[1]:
        st.markdown(
            '<div style="font-size:0.7rem;color:#64748b;">Florida Lottery • Pick 3 & Pick 4</div>',
            unsafe_allow_html=True,
        )
    with hc[2]:
        if st.button(f"{theme_icon} {theme_label}", key="global_theme_btn", use_container_width=True):
            st.session_state["theme"] = "light" if cur_theme == "dark" else "dark"
            st.rerun()
    with hc[3]:
        st.markdown(
            f'<div class="user-badge" style="display:flex;align-items:center;gap:0.3rem;background:linear-gradient(135deg,#334155,#1e293b);border:1px solid #475569;border-radius:2rem;padding:0.1rem 0.4rem 0.1rem 0.1rem;">'
            f'<div style="width:1.3rem;height:1.3rem;border-radius:50%;background:linear-gradient(135deg,#fbbf24,#f59e0b);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.6rem;color:#0f172a;flex-shrink:0;">{initial}</div>'
            f'<div style="line-height:1;"><div style="color:#f1f5f9;font-size:0.65rem;font-weight:600;">{user_data["username"]}</div><div style="color:#64748b;font-size:0.5rem;">{elapsed}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hc[4]:
        if st.button("🚪", key="global_logout_btn", use_container_width=True):
            for k in ["token", "user", "login_time", "last_activity", "theme", "view_mode", "sorteo_sort_asc", "sorteo_filter"]:
                st.session_state.pop(k, None)
            st.rerun()
