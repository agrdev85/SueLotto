import streamlit as st
import httpx
import os
import time
import base64
import json
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

TOKEN_REFRESH_MARGIN = 300


def _decode_jwt_payload(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        padded = payload + "=" * (4 - len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return {}


def _is_token_expired(token: str, margin: int = TOKEN_REFRESH_MARGIN) -> bool:
    payload = _decode_jwt_payload(token)
    exp = payload.get("exp")
    if not exp:
        return True
    return time.time() + margin >= exp


def _refresh_token():
    token = st.session_state.get("token")
    if not token:
        return False
    try:
        r = httpx.post(
            f"{API_URL}/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["last_refresh"] = time.time()
            return True
    except Exception:
        pass
    for k in ["token", "user", "login_time", "last_refresh"]:
        st.session_state.pop(k, None)
    st.rerun()
    return False


def _ensure_fresh_token():
    if not st.session_state.get("token"):
        return
    if st.session_state.get("_refreshing"):
        return
    if _is_token_expired(st.session_state["token"]):
        st.session_state["_refreshing"] = True
        try:
            _refresh_token()
        finally:
            st.session_state["_refreshing"] = False


def _make_headers():
    headers = {}
    token = st.session_state.get("token")
    if token:
        _ensure_fresh_token()
        token = st.session_state.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


def api_get(path, params=None):
    headers = _make_headers()
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = _extract_error(e)
        if e.response.status_code == 429:
            st.toast("⏳ Demasiadas solicitudes. Espera un momento.", icon="⚠️")
        elif e.response.status_code == 401:
            st.toast("🔒 Sesión expirada. Vuelve a iniciar sesión.", icon="⚠️")
            for k in ["token", "user", "login_time", "last_refresh"]:
                st.session_state.pop(k, None)
        return None
    except httpx.ConnectError:
        st.toast("🔌 Servidor no disponible. Intenta de nuevo.", icon="⚠️")
        return None
    except:
        return None


def api_post(path, json_data=None, token=None):
    headers = _make_headers()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = httpx.post(f"{API_URL}{path}", json=json_data or {}, headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = _extract_error(e)
        st.session_state["last_api_error"] = detail
        if e.response.status_code == 429:
            st.toast("⏳ Demasiadas solicitudes. Espera un momento.", icon="⚠️")
        elif e.response.status_code == 401:
            st.toast("🔒 Sesión expirada. Vuelve a iniciar sesión.", icon="⚠️")
            for k in ["token", "user", "login_time", "last_refresh"]:
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


SESSION_MAX_SECS = 86400

def init_session_state():
    st.session_state.setdefault("token", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("login_time", None)
    st.session_state.setdefault("last_activity", None)
    st.session_state.setdefault("theme", "dark")
    st.session_state.setdefault("view_mode", "cards")
    st.session_state.setdefault("sorteo_sort_asc", False)
    st.session_state.setdefault("sorteo_filter", "all")
    st.session_state.setdefault("_refreshing", False)

def check_session_expired():
    if not st.session_state.get("user"):
        return
    login_time = st.session_state.get("login_time")
    if login_time and time.time() - login_time > SESSION_MAX_SECS:
        for k in ["token", "user", "login_time", "last_activity", "last_refresh", "theme", "view_mode", "sorteo_sort_asc", "sorteo_filter"]:
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
    .scraped-game-card .game-date { color: #64748b !important; }
    .scraped-game-card .game-numbers span { color: #0f172a !important; }
    .scraped-game-card .game-bonus-label { color: #64748b !important; }
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
            for k in ["token", "user", "login_time", "last_activity", "last_refresh", "theme", "view_mode", "sorteo_sort_asc", "sorteo_filter"]:
                st.session_state.pop(k, None)
            st.rerun()

    render_scroll_to_top_button()


def render_scroll_to_top_button():
    """Botón flotante 'volver arriba' — animado con CSS puro, JS solo para scroll."""
    st.html(
        """
<style>
    #st-top-btn {
        position: fixed; right: 1.1rem; bottom: 5.4rem; z-index: 9999;
        width: 3rem; height: 3rem; border-radius: 50%; border: none; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        background: linear-gradient(160deg, rgba(30,41,59,0.96), rgba(15,23,42,0.96));
        color: #fbbf24; font-size: 1.15rem; line-height: 1;
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        opacity: 0; transform: translateY(26px) scale(0.75);
        pointer-events: none;
        transition: opacity 0.4s ease, transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
        animation: stTopGlow 3.6s ease-in-out infinite;
    }
    #st-top-btn::before {
        content: ""; position: absolute; inset: -2px; border-radius: inherit; padding: 2px;
        background: conic-gradient(from 210deg, #fbbf24, #8b5cf6, #3b82f6, #ef4444, #fbbf24);
        -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
        -webkit-mask-composite: xor; mask-composite: exclude;
        animation: stTopRotate 7s linear infinite; pointer-events: none;
    }
    #st-top-btn.visible { opacity: 1; transform: translateY(0) scale(1); pointer-events: auto; }
    #st-top-btn.leaving { opacity: 0; transform: translateY(26px) scale(0.6); pointer-events: none; }
    #st-top-btn:hover { color: #fff; box-shadow: 0 0 30px rgba(139,92,246,0.5); }
    #st-top-btn.burst { animation: stTopBurst 0.55s ease-out; }
    #st-top-btn .arrow { display: inline-block; transition: transform 0.3s ease; }
    #st-top-btn:hover .arrow { transform: translateY(-3px); }
    @keyframes stTopRotate { to { filter: hue-rotate(360deg); } }
    @keyframes stTopGlow { 0%, 100% { box-shadow: 0 0 0 rgba(251,191,36,0); } 50% { box-shadow: 0 0 30px rgba(251,191,36,0.35); } }
    @keyframes stTopBurst {
        0% { transform: scale(1); }
        35% { transform: scale(1.35) rotate(8deg); box-shadow: 0 0 60px rgba(251,191,36,0.7); }
        100% { transform: scale(1); }
    }
</style>
<button id="st-top-btn" aria-label="Volver arriba" title="Volver arriba"><span class="arrow">↑</span></button>
<script>
(function () {
    var btn = document.getElementById('st-top-btn');
    if (!btn || btn.dataset.bound) return;
    btn.dataset.bound = '1';
    var selectors = ['[data-testid="stMain"]', '[data-testid="stAppViewContainer"]', '[data-testid="stApp"]', '[data-testid="stMainBlockContainer"]'];
    var els = selectors.map(function (s) { return document.querySelector(s); }).filter(Boolean);
    function currentTop() {
        var top = window.pageYOffset || document.documentElement.scrollTop || 0;
        for (var i = 0; i < els.length; i++) { if (els[i].scrollTop > top) top = els[i].scrollTop; }
        return top;
    }
    function scrollToTop() {
        var done = false;
        for (var i = 0; i < els.length; i++) {
            if (els[i].scrollTop > 0) { els[i].scrollTo({ top: 0, behavior: 'smooth' }); done = true; }
        }
        if (!done) { window.scrollTo({ top: 0, behavior: 'smooth' }); }
    }
    var ticking = false;
    function onScroll() {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
            if (currentTop() > 250) { btn.classList.add('visible'); btn.classList.remove('leaving'); }
            else { btn.classList.remove('visible'); }
            ticking = false;
        });
    }
    els.forEach(function (el) { el.addEventListener('scroll', onScroll, { passive: true }); });
    window.addEventListener('scroll', onScroll, { passive: true });
    if (currentTop() > 250) btn.classList.add('visible');
    btn.addEventListener('click', function () {
        btn.classList.add('burst');
        btn.classList.add('leaving');
        setTimeout(function () { btn.classList.remove('burst'); }, 600);
        scrollToTop();
        setTimeout(function () { btn.classList.remove('leaving'); }, 900);
    });
})();
</script>
""",
        unsafe_allow_javascript=True,
    )


def go_to_planes():
    """Redirige a la página principal (Sorteos) y baja hasta la sección de
    planes/pago. Usa st.switch_page (mantiene la sesión iniciada)."""
    st.session_state["_go_to_planes"] = True
    st.switch_page("dashboard.py")


def render_pro_card(
    description_html: str,
    plan_features_html: str,
    cta_key: str,
    bg: str = "linear-gradient(135deg, #1e3a5f, #2d1b4e)",
    border_color: str = "#4a3f6b",
):
    """Tarjeta 'Contenido Exclusivo Pro' con el botón de upgrade DENTRO de la
    tarjeta. Al pulsarlo redirige a la sección de planes de la página principal
    manteniendo la sesión iniciada."""
    st.markdown(f"""
    <style>
        .st-key-pro_card {{
            background: {bg};
            border: 1px solid {border_color};
            border-radius: 1rem;
            padding: 2.2rem 1.8rem 1.8rem;
            max-width: 520px;
            margin: 3rem auto;
            text-align: center;
            box-shadow: 0 12px 40px rgba(0,0,0,0.35);
        }}
        .st-key-pro_card [data-testid="stElementContainer"] {{
            padding-bottom: 0.35rem;
        }}
        .st-key-pro_card .stButton > button {{
            width: 100% !important;
            background: linear-gradient(135deg,#fbbf24,#f59e0b) !important;
            color: #0f172a !important;
            font-weight: 800 !important;
            border: none !important;
            border-radius: 0.6rem !important;
            padding: 0.6rem 1rem !important;
            font-size: 1rem !important;
            cursor: pointer !important;
        }}
        .st-key-pro_card .stButton > button:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 16px rgba(251,191,36,0.4) !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="pro_card"):
        st.markdown('<div style="font-size:3rem;line-height:1;">🔒</div>', unsafe_allow_html=True)
        st.markdown(
            '<h2 style="color:#fbbf24;margin:0.5rem 0 0;">Contenido Exclusivo Pro</h2>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="color:#94a3b8;margin:0.5rem 0;">{description_html}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);'
            'border-radius:0.75rem;padding:0.75rem;margin:0.6rem 0;">'
            '<p style="color:#fbbf24;font-size:1.1rem;font-weight:700;margin:0;">🚀 Plan Pro — $1/mes</p>'
            f'<p style="color:#94a3b8;font-size:0.85rem;margin:0.25rem 0 0;">{plan_features_html}</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("🚀 Actualizar mi plan e ir a pagar", key=cta_key, use_container_width=True):
            go_to_planes()
