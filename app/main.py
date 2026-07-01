import streamlit as st
import httpx
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Sorteos",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    .main-header { text-align: center; padding: 1rem 0; }
    .main-header h1 { font-size: 2.5rem; color: #fbbf24; font-weight: 800; }
    .main-header p { color: #94a3b8; font-size: 1rem; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; }
    .card h3 { color: #f1f5f9; margin-bottom: 0.5rem; }
    .result-number { display: inline-block; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; font-weight: bold; 
                     font-size: 1.5rem; width: 3rem; height: 3rem; text-align: center; line-height: 3rem; border-radius: 0.5rem; margin: 0 0.25rem; }
    .result-number-pick4 { width: 2.5rem; height: 2.5rem; font-size: 1.2rem; line-height: 2.5rem; }
    .hot-badge { background: #ef4444; color: white; font-size: 0.7rem; padding: 0.1rem 0.4rem; border-radius: 0.25rem; }
    .cold-badge { background: #3b82f6; color: white; font-size: 0.7rem; padding: 0.1rem 0.4rem; border-radius: 0.25rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] { background: #1e293b; border-radius: 0.5rem 0.5rem 0 0; padding: 0.5rem 1.5rem; color: #94a3b8; }
    .stTabs [aria-selected="true"] { background: #334155; color: #fbbf24; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎱 Sorteos</h1><p>Análisis inteligente de la Florida Lottery • Pick 3 & Pick 4 • La Charada</p></div>', unsafe_allow_html=True)


@st.cache_data(ttl=300)
def api_get(path: str, params: dict = None):
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return None


col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card"><h3>📊 Pick 3 - Últimos Resultados</h3>', unsafe_allow_html=True)
    data_p3 = api_get("/api/resultados/ultimos", {"juego": "Pick 3", "limit": 5})
    if data_p3:
        for r in data_p3:
            nums = f'{r["n1"]}  {r["n2"]}  {r["n3"]}'
            sorteo_emoji = "🌙" if r["sorteo"] == "E" else "☀️"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:1rem;padding:0.3rem 0;border-bottom:1px solid #334155;">'
                f'<span style="color:#94a3b8;min-width:5rem;font-size:0.85rem;">{r["fecha"]}</span>'
                f'<span style="color:#fbbf24;min-width:1.5rem;">{sorteo_emoji}</span>'
                f'<span class="result-number">{r["n1"]}</span>'
                f'<span class="result-number">{r["n2"]}</span>'
                f'<span class="result-number">{r["n3"]}</span>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.info("⏳ Cargando datos...")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card"><h3>📊 Pick 4 - Últimos Resultados</h3>', unsafe_allow_html=True)
    data_p4 = api_get("/api/resultados/ultimos", {"juego": "Pick 4", "limit": 5})
    if data_p4:
        for r in data_p4:
            sorteo_emoji = "🌙" if r["sorteo"] == "E" else "☀️"
            nums_html = "".join(
                f'<span class="result-number result-number-pick4">{r[f"n{i}"]}</span>'
                for i in [1, 2, 3, 4]
            )
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:1rem;padding:0.3rem 0;border-bottom:1px solid #334155;">'
                f'<span style="color:#94a3b8;min-width:5rem;font-size:0.85rem;">{r["fecha"]}</span>'
                f'<span style="color:#fbbf24;min-width:1.5rem;">{sorteo_emoji}</span>'
                f'{nums_html}'
                f'</div>', unsafe_allow_html=True)
    else:
        st.info("⏳ Cargando datos...")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="card"><h3>🔥 Números Charada más Frecuentes (90 días)</h3>', unsafe_allow_html=True)
    charada_freqs = api_get("/api/estadisticas/charada-frecuencias", {"juego": "Pick 3", "dias": 90})
    if not charada_freqs:
        st.info("⏳ Cargando datos...")
    else:
        top = charada_freqs[:20]
        decenas = [n for n in range(0, 100, 10)]
        colors = []
        for f in top:
            if f["numero"] in decenas:
                colors.append("#fbbf24")
            elif f["frecuencia"] > top[0]["frecuencia"] * 0.7:
                colors.append("#ef4444")
            else:
                colors.append("#3b82f6")
        fig = px.bar(
            x=[f["numero"] for f in top],
            y=[f["frecuencia"] for f in top],
            labels={"x": "Número Charada", "y": "Frecuencia"},
            color=colors,
            color_discrete_map="identity",
            text=[f["numero"] for f in top],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            xaxis=dict(tickmode="linear", dtick=1),
            height=300,
            margin=dict(l=20, r=20, t=10, b=20),
            showlegend=False,
        )
        fig.update_traces(
            marker_line_color="#334155", marker_line_width=1,
            hovertemplate="Número %{x}<br>Frecuencia: %{y}<extra></extra>",
            textposition="outside",
            textfont_color="#94a3b8",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        <div style="display:flex;gap:1rem;margin-top:0.5rem;flex-wrap:wrap;font-size:0.75rem;">
            <span><span style="display:inline-block;width:0.7rem;height:0.7rem;background:#fbbf24;border-radius:0.15rem;"></span> Decena completa</span>
            <span><span style="display:inline-block;width:0.7rem;height:0.7rem;background:#ef4444;border-radius:0.15rem;"></span> Muy frecuente</span>
            <span><span style="display:inline-block;width:0.7rem;height:0.7rem;background:#3b82f6;border-radius:0.15rem;"></span> Frecuente</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="card"><h3>🎯 Top 10 Números Sugeridos</h3>', unsafe_allow_html=True)
    preds = api_get("/api/predicciones", {"juego": "Pick 3"})
    if not preds:
        st.info("⏳ Cargando datos...")
    else:
        top_preds = preds[:10]
        pred_colors = ["#ef4444" if p["probabilidad"] > 0.12 else "#fbbf24" if p["probabilidad"] > 0.08 else "#3b82f6" for p in top_preds]
        fig2 = px.bar(
            x=[p["numero"] for p in top_preds],
            y=[p["probabilidad"] for p in top_preds],
            labels={"x": "Dígito", "y": "Probabilidad"},
            color=pred_colors,
            color_discrete_map="identity",
            text=[f"{p['probabilidad']*100:.1f}%" for p in top_preds],
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            xaxis=dict(tickmode="linear", dtick=1),
            height=300,
            margin=dict(l=20, r=20, t=10, b=20),
            showlegend=False,
        )
        fig2.update_traces(
            marker_line_color="#334155", marker_line_width=1,
            textposition="outside",
            textfont_color="#fbbf24",
            hovertemplate="Dígito %{x}<br>Prob: %{y:.1%}<extra></extra>",
        )
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

col5, col6 = st.columns(2)

with col5:
    st.markdown('<div class="card"><h3>📊 Últimos Resultados - Top Charada</h3>', unsafe_allow_html=True)
    charada_freqs = api_get("/api/estadisticas/charada-frecuencias", {"juego": "Pick 3", "dias": 30})
    if charada_freqs and len(charada_freqs) > 0:
        top10 = charada_freqs[:10]
        st.markdown('<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.25rem;">', unsafe_allow_html=True)
        for f in top10:
            n_color = "#fbbf24" if f["numero"] % 10 == 0 else "#e2e8f0"
            st.markdown(
                f'<div style="background:#334155;padding:0.3rem 0.8rem;border-radius:0.3rem;'
                f'display:flex;justify-content:space-between;">'
                f'<span style="color:{n_color};font-weight:bold;">{f["numero"]:02d}</span>'
                f'<span style="color:#94a3b8;">{f["frecuencia"]}× ({f["porcentaje"]}%)</span>'
                f'</div>', unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("⏳ Cargando datos...")
    st.markdown('</div>', unsafe_allow_html=True)

with col6:
    st.markdown('<div class="card"><h3>🎯 Consejos Rápidos</h3>', unsafe_allow_html=True)
    st.markdown("""
    <ul style="color: #94a3b8; line-height: 1.8;">
        <li>🔍 <strong>Busca tus sueños</strong> para encontrar números Charada asociados</li>
        <li>📈 Revisa las <strong>estadísticas detalladas</strong> por período y sorteo</li>
        <li>🧠 Usa la <strong>IA</strong> para interpretar adivinanzas</li>
        <li>🎲 Combina números <span style="color:#ef4444;">calientes</span> (alta frecuencia) y <span style="color:#3b82f6;">atrasados</span></li>
        <li>🔟 Las <strong style="color:#fbbf24;">decenas completas</strong> (10, 20, 30...) tienen significados especiales en la Charada</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; padding: 2rem; color: #475569; font-size: 0.8rem;">
    <p>© 2026 SueñaLotto · Esta aplicación es solo para fines de entretenimiento. Juega con responsabilidad.</p>
</div>
""", unsafe_allow_html=True)
