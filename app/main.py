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
        return f"De por Vida — ${amt:.2f} único 🔥"
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
            _lt = _plans_api.get("lifetime", {})
            _lt_price = _lt.get("amount", 99.99)
            _lt_full = _promo_api.get("full_price", 99.99)
            _lt_promo_html = ""
            if _promo_api.get("active"):
                _lt_promo_html = (
                    f'<div style="background:linear-gradient(135deg,#fbbf24,#ef4444);color:#0f172a;'
                    f'font-size:0.7rem;font-weight:700;padding:0.2rem 0.6rem;border-radius:1rem;'
                    f'display:inline-block;margin-bottom:0.3rem;">'
                    f'🔥 ${_promo_api["promo_price"]:.2f} — quedan {_promo_api["remaining"]} cupos</div>'
                    f'<div style="text-decoration:line-through;color:#64748b;font-size:0.85rem;">'
                    f'${_lt_full:.2f}</div>'
                )
            st.markdown(
                f'<div class="tier-card lifetime"><h4 style="color:#8b5cf6;">De por Vida</h4>'
                f'<div class="tier-price">${_lt_price:.2f}<span> único</span></div>'
                f'{_lt_promo_html}'
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

    @media (max-width: 640px) {
        .sorteo-card .fijo-number { font-size: 2rem; }
        .sorteo-card.noche-draw .fijo-number { font-size: 1.8rem; }
        .sorteo-card.media-draw .fijo-number { font-size: 1.8rem; }
        .sorteo-card .card-body { flex-direction: column; gap: 0.5rem; }
        .sorteo-card .corridos-digit { width: 1.7rem; height: 1.7rem; font-size: 0.75rem; }
        .sorteo-list-row { grid-template-columns: 1fr 1.2fr 1.5fr 1.5fr; font-size: 0.7rem; gap: 0.3rem; padding: 0.4rem 0.5rem; }
        .sorteo-card.day-card .draw-card { padding: 0.5rem 0.75rem; }
    }
</style>
""", unsafe_allow_html=True)

user_tier = (tier_info or {}).get("tier", "free")
if user_tier == "free":
    st.warning("🔒 Tienes el plan **Gratis**. Actualiza a **Pro** ($1/mes) o **De por Vida** ($50) para desbloquear estadísticas avanzadas, matriz charada, y adivinanzas IA.")

st.markdown('<div class="hero"><h1>📅 Sorteos</h1><p>Resultados en vivo • Pick 3 & Pick 4 • Análisis Charada</p></div>', unsafe_allow_html=True)

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

# ─── Other Florida Lottery Games (Web Scraped) ──────────────────

st.markdown("---")
st.markdown('<h2 style="color:var(--text-primary);">🎰 Otros Juegos de Florida Lottery</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:var(--text-secondary);font-size:0.85rem;">Resultados obtenidos desde flalottery.com</p>', unsafe_allow_html=True)

otros_juegos = api_get("/api/resultados/otros-juegos")
if otros_juegos and isinstance(otros_juegos, list):
    for game in otros_juegos:
        name = game.get("name", "")
        date_str = game.get("date", "")
        numbers = game.get("numbers", [])
        extra = game.get("extra", [])

        nums_html = "".join(f"<span>{n}</span>" for n in numbers) + "".join(f'<span class="xb">{n}</span>' for n in extra)
        st.markdown(
            f'<div class="scraped-game-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">'
            f'<div class="game-name">{name}</div>'
            f'<div class="game-date">{date_str}</div>'
            f'</div>'
            f'<div class="game-numbers">{nums_html}</div></div>',
            unsafe_allow_html=True,
        )
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
        promo_badge = ""
        if plan["id"] == "lifetime" and _promo_api.get("active"):
            promo_badge = (
                f'<div style="background:linear-gradient(135deg,#fbbf24,#ef4444);color:#0f172a;'
                f'font-size:0.65rem;font-weight:700;padding:0.15rem 0.5rem;border-radius:1rem;'
                f'display:inline-block;">🔥 ${_promo_api["promo_price"]:.2f} — quedan {_promo_api["remaining"]} cupos</div>'
            )
        st.markdown(
            f'<div style="background:#1e293b;border:{border};border-radius:1rem;padding:1.5rem;text-align:center;">'
            f'<h3 style="color:{plan["color"]};">{plan["name"]}</h3>'
            f'{promo_badge}'
            f'<div style="font-size:2rem;font-weight:800;color:var(--text-primary);margin:0.5rem 0;">{plan["price"]}</div>'
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
