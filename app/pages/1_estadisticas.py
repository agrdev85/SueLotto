import streamlit as st
import httpx
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Estadísticas - SueñaLotto", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; }
    .card h3 { color: #f1f5f9; }
    .stat-value { font-size: 2rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="color:#fbbf24;text-align:center;">📊 Estadísticas Detalladas</h1>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def api_get(path, params=None):
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return None

col_filtros1, col_filtros2, col_filtros3 = st.columns(3)
with col_filtros1:
    juego = st.selectbox("Juego", ["Pick 3", "Pick 4"], key="est_juego")
with col_filtros2:
    sorteo = st.selectbox("Sorteo", ["Todos", "E (Evening)", "M (Midday)"])
    sorteo_param = sorteo[0] if sorteo != "Todos" else None
with col_filtros3:
    dias = st.selectbox("Período", [7, 15, 30, 90, 180, 365], index=2, key="est_dias")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card"><h3>🔥 Frecuencia de Números</h3>', unsafe_allow_html=True)
    freqs = api_get("/api/estadisticas/frecuencias", {"juego": juego, "sorteo": sorteo_param, "dias": dias})
    if freqs:
        fig = px.bar(
            x=[f["numero"] for f in freqs],
            y=[f["frecuencia"] for f in freqs],
            labels={"x": "Número", "y": "Frecuencia"},
            color=[f["frecuencia"] for f in freqs],
            color_continuous_scale="Viridis",
            text=[f["frecuencia"] for f in freqs],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", height=400,
            xaxis=dict(tickmode="linear", dtick=1),
        )
        fig.update_traces(marker_line_color="#334155", marker_line_width=1,
                          textposition="outside", textfont_color="#94a3b8")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para este período.")

    st.markdown('<h4 style="color:#94a3b8;margin-top:1rem;">Top 10 Números más Frecuentes</h4>', unsafe_allow_html=True)
    if freqs:
        for i, f in enumerate(freqs[:10]):
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #334155;">'
                f'<span style="color:#f1f5f9;">{i+1}. Número <strong>{f["numero"]}</strong></span>'
                f'<span style="color:#22c55e;">{f["frecuencia"]} veces ({f["porcentaje"]}%)</span>'
                f'</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card"><h3>❄️ Números más Atrasados</h3>', unsafe_allow_html=True)
    atrasados = api_get("/api/estadisticas/atrasados", {"juego": juego, "sorteo": sorteo_param})
    if atrasados:
        fig2 = px.bar(
            x=[a["numero"] for a in atrasados],
            y=[a["dias_sin_salir"] for a in atrasados],
            labels={"x": "Número", "y": "Días sin salir"},
            color=[a["dias_sin_salir"] for a in atrasados],
            color_continuous_scale="Plasma",
            text=[a["dias_sin_salir"] for a in atrasados if a["dias_sin_salir"] < 900],
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", height=400,
            xaxis=dict(tickmode="linear", dtick=1),
        )
        fig2.update_traces(marker_line_color="#334155", marker_line_width=1,
                           textposition="outside", textfont_color="#94a3b8")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No hay datos suficientes.")

    if atrasados:
        max_dias = max(a["dias_sin_salir"] for a in atrasados if a["dias_sin_salir"] < 900)
        st.markdown(f'<h4 style="color:#94a3b8;margin-top:1rem;">Número más atrasado: <span style="color:#ef4444;font-size:1.2rem;">{atrasados[0]["numero"]}</span> ({atrasados[0]["dias_sin_salir"]} días)</h4>', unsafe_allow_html=True)
        st.markdown(f'<h4 style="color:#94a3b8;">Número menos atrasado: <span style="color:#22c55e;">{atrasados[-1]["numero"]}</span> ({atrasados[-1]["dias_sin_salir"]} días)</h4>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

st.markdown('<div class="card"><h3>🤖 Predicciones ML</h3>', unsafe_allow_html=True)
preds = api_get("/api/predicciones", {"juego": juego, "sorteo": sorteo_param})
if preds:
    top_preds = preds[:10]
    fig3 = px.bar(
        x=[p["numero"] for p in top_preds],
        y=[p["probabilidad"] for p in top_preds],
        labels={"x": "Número", "y": "Probabilidad"},
        color=[p["probabilidad"] for p in top_preds],
        color_continuous_scale="RdYlGn",
        text=[f"{p['probabilidad']*100:.1f}%" for p in top_preds],
    )
    fig3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#94a3b8", height=400,
        xaxis=dict(tickmode="linear", dtick=1),
    )
    fig3.update_traces(marker_line_color="#334155", marker_line_width=1,
                       textposition="outside", textfont_color="#fbbf24")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<h4 style="color:#94a3b8;">Top 5 Predicciones</h4>', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, p in enumerate(top_preds[:5]):
        with cols[i]:
            st.markdown(
                f'<div style="text-align:center;background:#334155;border-radius:0.5rem;padding:1rem;">'
                f'<div style="font-size:2rem;font-weight:800;color:#fbbf24;">{p["numero"]}</div>'
                f'<div style="color:#22c55e;font-weight:600;">{p["probabilidad"]*100:.1f}%</div>'
                f'</div>', unsafe_allow_html=True)
else:
    st.info("No hay suficientes datos para generar predicciones ML. Se usarán heurísticas cuando haya datos.")
st.markdown('</div>', unsafe_allow_html=True)
