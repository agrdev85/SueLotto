import streamlit as st
import httpx
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime
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
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #1a1040 30%, #0f172a 60%, #1a1040 100%); }
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
    .btn-login { background: linear-gradient(135deg, #fbbf24, #f59e0b); border: none; color: #0f172a; font-weight: 700; font-size: 0.75rem; padding: 0.35rem 1rem; border-radius: 2rem; cursor: pointer; }
    .card { background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9)); border: 1px solid rgba(51, 65, 85, 0.8); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; backdrop-filter: blur(8px); }
    .card h3 { color: #f1f5f9; margin-bottom: 0.5rem; font-weight: 700; }
    .result-number { display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; font-weight: 800; font-size: 1.3rem; width: 2.6rem; height: 2.6rem; border-radius: 0.5rem; margin: 0 0.2rem; box-shadow: 0 2px 8px rgba(59,130,246,0.3); }
    .result-number-pick4 { width: 2.2rem; height: 2.2rem; font-size: 1.1rem; }
    .glow-text { text-shadow: 0 0 20px rgba(251,191,36,0.3); }
    .hero { text-align: center; padding: 0.5rem 0 1rem; }
    .hero h1 { font-size: 2.8rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #ef4444, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; letter-spacing: -1px; }
    .hero p { color: #64748b; font-size: 0.9rem; max-width: 600px; margin: 0 auto; }
    .sparkle { background: radial-gradient(circle at 50% 0%, rgba(251,191,36,0.08), transparent 70%); }
    .auth-container { max-width: 420px; margin: 2rem auto; }
    .auth-container .card { padding: 2rem; }
    .tier-card { background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.9)); border: 1px solid rgba(51,65,85,0.8); border-radius: 1rem; padding: 1.5rem; text-align: center; height: 100%; }
    .tier-card.pro { border-color: #fbbf24; box-shadow: 0 0 20px rgba(251,191,36,0.1); }
    .tier-card.lifetime { border-color: #8b5cf6; box-shadow: 0 0 20px rgba(139,92,246,0.1); }
    .tier-price { font-size: 2.5rem; font-weight: 900; color: #fbbf24; }
    .tier-price span { font-size: 1rem; color: #64748b; }
    .feature-yes { color: #22c55e; }
    .feature-no { color: #64748b; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; background: rgba(30,41,59,0.5); border-radius: 0.75rem; padding: 0.25rem; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 0.5rem; padding: 0.4rem 1.2rem; color: #94a3b8; font-size: 0.85rem; border: none; }
    .stTabs [aria-selected="true"] { background: #334155; color: #fbbf24; font-weight: 600; }
    div[data-testid="stForm"] { border: none; padding: 0; }
    .stTextInput>div>div>input { background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 0.5rem !important; }
    .stTextInput>div>div>input:focus { border-color: #fbbf24 !important; box-shadow: 0 0 0 2px rgba(251,191,36,0.2) !important; }
    .bet-row { display: grid; grid-template-columns: 1fr 1.5fr 1fr 1fr 1fr 1fr 1fr 1fr auto; gap: 0.3rem; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid #1e293b; font-size: 0.8rem; }
    .bet-header { color: #64748b; font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .bet-value { color: #e2e8f0; }
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
    except:
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
    except:
        return None

st.session_state.setdefault("token", None)
st.session_state.setdefault("user", None)
st.session_state.setdefault("login_time", None)
st.session_state.setdefault("page", "sorteos")
st.session_state.setdefault("show_auth", False)

# ─── Header ────────────────────────────────────────────────────────

def render_header():
    user = st.session_state.get("user")
    cols = st.columns([1, 2, 1])
    with cols[0]:
        st.markdown("")
    with cols[1]:
        st.markdown(
            '<div class="app-header-center">'
            '<h1>SueñaLotto</h1>'
            '<span>Florida Lottery • Pick 3 & Pick 4</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    with cols[2]:
        if user:
            elapsed = ""
            if st.session_state.get("login_time"):
                secs = int(time.time() - st.session_state["login_time"])
                if secs < 60:
                    elapsed = f"{secs}s"
                elif secs < 3600:
                    elapsed = f"{secs//60}m"
                else:
                    elapsed = f"{secs//3600}h {(secs%3600)//60}m"
            initial = user["username"][0].upper() if user["username"] else "?"
            c1, c2 = st.columns([1, 0.3])
            with c1:
                st.markdown(
                    f'<div class="app-header-right">'
                    f'<div class="user-badge">'
                    f'<div class="user-avatar">{initial}</div>'
                    f'<div class="user-info">'
                    f'<div class="user-name">{user["username"]}</div>'
                    f'<div class="user-time">{elapsed}</div>'
                    f'</div></div></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("🚪", key="logout_btn"):
                    for k in ["token", "user", "login_time", "show_auth"]:
                        st.session_state.pop(k, None)
                    st.rerun()
        else:
            if st.button("🔑 Entrar", key="header_login"):
                st.session_state["show_auth"] = True
                st.rerun()

render_header()

# ─── Auth Page ──────────────────────────────────────────────────────

if st.session_state.get("show_auth") and not st.session_state.get("user"):
    st.markdown('<div class="hero sparkle"><h1>🌟 SueñaLotto</h1><p>Tu guía inteligente para la lotería de Florida. Análisis, estadísticas y la sabiduría de la Charada Cubana.</p></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1.5])
    with col_a:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
        with tab_login:
            with st.form("login_form"):
                u = st.text_input("Usuario", placeholder="Tu nombre de usuario", key="login_user")
                p = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass")
                if st.form_submit_button("Iniciar Sesión", type="primary", use_container_width=True):
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
                if st.form_submit_button("Crear Cuenta Gratis", type="primary", use_container_width=True):
                    res = api_post("/api/auth/register", {"username": ru, "email": re, "password": rp})
                    if res and "access_token" in res:
                        st.session_state["token"] = res["access_token"]
                        st.session_state["user"] = res["user"]
                        st.session_state["login_time"] = time.time()
                        st.session_state["show_auth"] = False
                        st.rerun()
                    else:
                        detail = "Error al registrar. Intenta con otros datos."
                        st.error(detail)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="card"><h3 style="text-align:center;">🚀 Planes</h3>', unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.markdown(
                '<div class="tier-card"><h4 style="color:#94a3b8;">Gratis</h4>'
                '<div class="tier-price">$0<span>/mes</span></div>'
                '<div style="text-align:left;margin-top:1rem;font-size:0.85rem;">'
                '<p><span class="feature-yes">✅</span> Sorteos completos</p>'
                '<p><span class="feature-no">❌</span> Búsqueda Histórica</p>'
                '<p><span class="feature-no">❌</span> Charada Enriquecida</p>'
                '<p><span class="feature-no">❌</span> Adivinanzas IA</p>'
                '<p><span class="feature-no">❌</span> Búsqueda Sueños</p>'
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
                '<p><span class="feature-yes">✅</span> IA + Sueños</p>'
                '<p><span class="feature-yes">✅</span> Historial completo</p>'
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

# ─── Main App (authenticated) ─────────────────────────────────────

user = st.session_state.get("user")
is_pro = user and user.get("tier") in ("pro", "lifetime")

st.markdown('<div class="hero sparkle"><h1>🎱 Sorteos</h1><p>Resultados en vivo • Análisis Charada • Predicciones inteligentes</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="card"><h3>📊 Pick 3</h3>', unsafe_allow_html=True)
    data_p3 = api_get("/api/resultados/ultimos", {"juego": "Pick 3", "limit": 5})
    if data_p3:
        for r in data_p3:
            sorteo_emoji = "🌙" if r["sorteo"] == "E" else "☀️"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.4rem 0;border-bottom:1px solid #1e293b;">'
                f'<span style="color:#64748b;min-width:4.5rem;font-size:0.8rem;">{r["fecha"]}</span>'
                f'<span style="min-width:1.2rem;">{sorteo_emoji}</span>'
                f'<span class="result-number">{r["n1"]}</span>'
                f'<span class="result-number">{r["n2"]}</span>'
                f'<span class="result-number">{r["n3"]}</span>'
                f'<span style="color:#64748b;font-size:0.7rem;margin-left:auto;">{r["n2"]}{r["n3"]}</span>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.info("⏳ Cargando datos...")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card"><h3>📊 Pick 4</h3>', unsafe_allow_html=True)
    data_p4 = api_get("/api/resultados/ultimos", {"juego": "Pick 4", "limit": 5})
    if data_p4:
        for r in data_p4:
            sorteo_emoji = "🌙" if r["sorteo"] == "E" else "☀️"
            nums_html = "".join(f'<span class="result-number result-number-pick4">{r[f"n{i}"]}</span>' for i in [1,2,3,4])
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.4rem 0;border-bottom:1px solid #1e293b;">'
                f'<span style="color:#64748b;min-width:4.5rem;font-size:0.8rem;">{r["fecha"]}</span>'
                f'<span style="min-width:1.2rem;">{sorteo_emoji}</span>'
                f'{nums_html}'
                f'<span style="color:#64748b;font-size:0.7rem;margin-left:auto;">{r["n1"]}{r["n2"]}|{r["n3"]}{r["n4"]}</span>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.info("⏳ Cargando datos...")
    st.markdown('</div>', unsafe_allow_html=True)

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
            yaxis=dict(showgrid=False),
            showlegend=False,
        )
        fig.update_traces(marker_line_color="#334155", marker_line_width=1, textposition="outside", textfont_color="#94a3b8", hovertemplate="%{x}<br>%{y} veces<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)
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
        st.plotly_chart(fig2, use_container_width=True)
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
    <ul style="color:#94a3b8;line-height:1.8;font-size:0.85rem;padding-left:1.2rem;">
        <li>🔍 Busca tus <strong>sueños</strong> para números Charada</li>
        <li>📈 Revisa <strong>estadísticas</strong> por período y sorteo</li>
        <li>🧠 Usa la <strong>IA</strong> para interpretar adivinanzas</li>
        <li>🎲 Combina <span style="color:#ef4444;">calientes</span> y <span style="color:#3b82f6;">atrasados</span></li>
        <li>🔟 Las <span style="color:#fbbf24;">decenas</span> tienen significados especiales</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Bet Tracking (logged-in users) ────────────────────────────────
if user:
    st.markdown("---")
    st.markdown('<div class="card"><h3>🎫 Mis Jugadas</h3>', unsafe_allow_html=True)

    with st.expander("➕ Nueva jugada", expanded=False):
        with st.form("bet_form"):
            bc1, bc2 = st.columns(2)
            with bc1:
                b_fecha = st.date_input("Fecha", value=date.today())
                b_juego = st.selectbox("Juego", ["Pick 3", "Pick 4"])
                b_turno = st.selectbox("Turno", ["Mañana", "Mediodía", "Tarde"])
            with bc2:
                b_numeros = st.text_input("Números", placeholder="Ej: 1-2-3 o 5-2-1-8")
                b_precio = st.number_input("Precio ($)", min_value=0.0, step=0.5, format="%.2f")
                b_desc = st.text_input("Descripción (opcional)", placeholder="Ej: Jugada de la suerte")

            bc3 = st.columns(4)
            with bc3[0]:
                b_fijo = st.text_input("Fijo", placeholder="Ej: 3")
            with bc3[1]:
                b_corrido = st.text_input("Corrido", placeholder="Ej: 21")
            with bc3[2]:
                b_parle = st.text_input("Parle", placeholder="Ej: 3-21")
            with bc3[3]:
                b_candado = st.text_input("Candado", placeholder="Ej: 3-2-1")

            if st.form_submit_button("💾 Guardar Jugada", type="primary", use_container_width=True):
                api_post("/api/bets", {
                    "fecha": b_fecha.isoformat(),
                    "turno": b_turno,
                    "juego": b_juego,
                    "numeros": b_numeros,
                    "fijo": b_fijo,
                    "corrido": b_corrido,
                    "parle": b_parle,
                    "candado": b_candado,
                    "precio": b_precio,
                    "descripcion": b_desc,
                })
                st.success("Jugada guardada")
                st.rerun()

    bets = api_get("/api/bets")
    if bets:
        b_header = ['Fecha', 'Juego', 'Números', 'Fijo', 'Corrido', 'Parle', 'Candado', '$', '']
        cols = st.columns([1, 1, 1.5, 1, 1, 1, 1, 0.8, 0.5])
        for i, h in enumerate(b_header):
            cols[i].markdown(f'<div class="bet-header">{h}</div>', unsafe_allow_html=True)
        for b in bets:
            cols = st.columns([1, 1, 1.5, 1, 1, 1, 1, 0.8, 0.5])
            cols[0].markdown(f'<div class="bet-value">{b["fecha"][:10]}</div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div class="bet-value">{b["juego"]}</div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div class="bet-value" style="font-weight:700;color:#fbbf24;">{b["numeros"]}</div>', unsafe_allow_html=True)
            cols[3].markdown(f'<div class="bet-value">{b.get("fijo") or "-"}</div>', unsafe_allow_html=True)
            cols[4].markdown(f'<div class="bet-value">{b.get("corrido") or "-"}</div>', unsafe_allow_html=True)
            cols[5].markdown(f'<div class="bet-value">{b.get("parle") or "-"}</div>', unsafe_allow_html=True)
            cols[6].markdown(f'<div class="bet-value">{b.get("candado") or "-"}</div>', unsafe_allow_html=True)
            cols[7].markdown(f'<div class="bet-value">${b.get("precio", 0):.0f}</div>', unsafe_allow_html=True)
            if cols[8].button("✕", key=f"del_{b['id']}"):
                api_post(f"/api/bets/{b['id']}/delete", json_data={})
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:2rem;color:#475569;font-size:0.75rem;">
    <p>© 2026 SueñaLotto · Solo para entretenimiento. Juega con responsabilidad.</p>
</div>
""", unsafe_allow_html=True)
