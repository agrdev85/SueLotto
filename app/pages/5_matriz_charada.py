import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Matriz & Charada", page_icon="🔢", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; }
    .card h3 { color: #f1f5f9; margin-bottom: 0.5rem; }
    .result-number { display: inline-block; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; font-weight: bold;
                     font-size: 1.2rem; width: 2.5rem; height: 2.5rem; text-align: center; line-height: 2.5rem; border-radius: 0.5rem; margin: 0 0.15rem; }
    .grid-cell { display: inline-flex; align-items: center; justify-content: center; width: 2.5rem; height: 2.5rem;
                 background: #1e293b; border: 1px solid #334155; border-radius: 0.3rem; margin: 0.1rem;
                 font-size: 0.85rem; color: #94a3b8; cursor: pointer; transition: all 0.2s; }
    .grid-cell:hover { background: #334155; border-color: #3b82f6; }
    .grid-cell-active { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; border-color: #8b5cf6; }
    .grid-cell-wall { background: #0f172a; border-color: #1e293b; color: #334155; cursor: default; }
    .grid-cell-zero { background: #0f172a; border-color: #1e293b; color: #475569; }
    .highlight-hot { background: #ef4444; color: white; border-color: #ef4444; }
    .highlight-cold { background: #3b82f6; color: white; border-color: #3b82f6; }
    .highlight-both { background: #fbbf24; color: #0f172a; border-color: #fbbf24; }
    .highlight-disc { background: #22c55e; color: white; border-color: #22c55e; }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] { background: #1e293b; border-radius: 0.5rem 0.5rem 0 0; padding: 0.5rem 1.5rem; color: #94a3b8; }
    .stTabs [aria-selected="true"] { background: #334155; color: #fbbf24; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align:center;color:#fbbf24;">🔢 Matriz & Charada</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#94a3b8;">Análisis matricial de números • Comparación con calientes y posibles</p>', unsafe_allow_html=True)


@st.cache_data(ttl=60)
def api_get(path: str, params: dict = None):
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error API: {e}")
        return None


def api_post(path: str, data: dict):
    try:
        r = httpx.post(f"{API_URL}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error API: {e}")
        return None


col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    tipo_matriz = st.selectbox("Tipo de Matriz", ["nueva", "vieja"],
                               format_func=lambda x: "Nueva (10x10)" if x == "nueva" else "Vieja (11x11)")

rango_num = (0, 100) if tipo_matriz == "vieja" else (1, 100)

with col2:
    num1 = st.number_input("Número 1", min_value=rango_num[0], max_value=rango_num[1], value=5 if tipo_matriz == "nueva" else 0)

with col3:
    num2 = st.number_input("Número 2", min_value=rango_num[0], max_value=rango_num[1], value=12)

num3 = st.number_input("Número 3 (opcional)", min_value=rango_num[0], max_value=rango_num[1], value=34)

tabs = st.tabs(["📊 Matriz Visual", "🔍 Alrededor", "📈 Comparar & Reducir", "📖 Charada Enriquecida"])

secuencia = [n for n in [num1, num2, num3] if n >= rango_num[0]]

with tabs[0]:
    st.markdown(f'<div class="card"><h3>📊 Matriz {tipo_matriz.title()} {"(10x10)" if tipo_matriz == "nueva" else "(11x11)"}</h3>', unsafe_allow_html=True)

    calientes_data = api_get("/api/estadisticas/calientes", {"juego": "Pick 3", "limite": 10, "sorteo": "E"})
    posibles_data = api_get("/api/estadisticas/posibles-salir", {"juego": "Pick 3", "sorteo": "E"})

    set_calientes = set(calientes_data.get("numeros", [])) if calientes_data else set()
    set_posibles = set(posibles_data.get("numeros", [])) if posibles_data else set()
    set_ambos = set_calientes & set_posibles

    matriz = []
    if tipo_matriz == "nueva":
        matriz = [[r * 10 + c + 1 for c in range(10)] for r in range(10)]
    else:
        matriz = [[r * 11 + c for c in range(11)] for r in range(9)]
        matriz.append([99, 100] + [0] * 9)
        matriz.append([0] * 11)

    for fila_idx, fila in enumerate(matriz):
        cols = st.columns(len(fila))
        for col_idx, valor in enumerate(fila):
            with cols[col_idx]:
                if valor == 0 and tipo_matriz == "vieja":
                    st.markdown(f'<div class="grid-cell grid-cell-wall">⬛</div>', unsafe_allow_html=True)
                else:
                    cls = "grid-cell"
                    if valor in secuencia:
                        cls += " grid-cell-active"
                    elif valor in set_ambos and valor in secuencia:
                        cls += " highlight-both"
                    if valor in secuencia:
                        pass
                    elif valor in set_ambos:
                        cls += " highlight-both"
                    elif valor in set_calientes:
                        cls += " highlight-hot"
                    elif valor in set_posibles:
                        cls += " highlight-cold"

                    st.markdown(f'<div class="{cls}">{valor}</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;gap:1.5rem;margin-top:1rem;flex-wrap:wrap;">
        <div><span style="display:inline-block;width:1rem;height:1rem;background:linear-gradient(135deg,#3b82f6,#8b5cf6);border-radius:0.25rem;margin-right:0.3rem;"></span> Seleccionado</div>
        <div><span style="display:inline-block;width:1rem;height:1rem;background:#ef4444;border-radius:0.25rem;margin-right:0.3rem;"></span> Caliente</div>
        <div><span style="display:inline-block;width:1rem;height:1rem;background:#3b82f6;border-radius:0.25rem;margin-right:0.3rem;"></span> Posible</div>
        <div><span style="display:inline-block;width:1rem;height:1rem;background:#fbbf24;border-radius:0.25rem;margin-right:0.3rem;"></span> Caliente + Posible</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    st.markdown(f'<div class="card"><h3>🔍 Números Alrededor</h3>', unsafe_allow_html=True)

    if st.button("🔍 Obtener Alrededor", type="primary", use_container_width=True):
        for n in secuencia:
            resp = api_post("/api/matriz/alrededor", {"numero": n, "tipo_matriz": tipo_matriz})
            if resp:
                st.markdown(f'<p style="color:#fbbf24;font-weight:bold;">Alrededor de <strong>{n}</strong> ({resp["total"]} números):</p>', unsafe_allow_html=True)
                numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["numeros"])
                st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)

        resp_seq = api_post("/api/matriz/secuencia", {"secuencia": secuencia, "tipo_matriz": tipo_matriz})
        if resp_seq:
            st.markdown(f'<p style="color:#22c55e;font-weight:bold;margin-top:1rem;">Combinación única ({resp_seq["total"]} números):</p>', unsafe_allow_html=True)
            numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp_seq["numeros"])
            st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown(f'<div class="card"><h3>📈 Comparar & Reducir</h3>', unsafe_allow_html=True)

    with st.expander("⚙️ Opciones de calientes y posibles", expanded=True):
        col_game, col_sorteo = st.columns(2)
        with col_game:
            juego_cal = st.selectbox("Juego", ["Pick 3", "Pick 4"], key="juego_comp")
        with col_sorteo:
            sorteo_cal = st.selectbox("Sorteo", ["E", "M"], key="sorteo_comp")

    if st.button("📊 Comparar y Reducir", type="primary", use_container_width=True):
        calientes_resp = api_get("/api/estadisticas/calientes", {"juego": juego_cal, "sorteo": sorteo_cal, "limite": 20, "dias": 30})
        posibles_resp = api_get("/api/estadisticas/posibles-salir", {"juego": juego_cal, "sorteo": sorteo_cal})
        calientes = calientes_resp.get("numeros", []) if calientes_resp else []
        posibles = posibles_resp.get("numeros", []) if posibles_resp else []

        resp = api_post("/api/matriz/comparar", {
            "secuencia": secuencia,
            "tipo_matriz": tipo_matriz,
            "calientes": calientes,
            "posibles": posibles,
        })
        if resp:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Alrededor", resp["total_alrededor"])
            with m2:
                st.metric("Intersección Calientes", resp["total_interseccion_calientes"])
            with m3:
                st.metric("Intersección Posibles", resp["total_interseccion_posibles"])
            with m4:
                st.metric("Discriminante", resp["total_discriminante"])

            st.markdown(f'<div class="card" style="margin-top:1rem;"><h4>🔴 Intersección con Calientes ({resp["total_interseccion_calientes"]})</h4>', unsafe_allow_html=True)
            if resp["interseccion_calientes"]:
                numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_calientes"])
                st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f'<div class="card"><h4>🔵 Intersección con Posibles ({resp["total_interseccion_posibles"]})</h4>', unsafe_allow_html=True)
            if resp["interseccion_posibles"]:
                numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_posibles"])
                st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f'<div class="card"><h4>🟡 Intersección con Ambos (Caliente + Posible) ({resp["total_interseccion_ambos"]})</h4>', unsafe_allow_html=True)
            if resp["interseccion_ambos"]:
                numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_ambos"])
                st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
            else:
                st.info("No hay números que sean calientes y posibles a la vez.")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f'<div class="card"><h4>🟢 Discriminante (Alrededor - Calientes - Posibles) ({resp["total_discriminante"]})</h4>', unsafe_allow_html=True)
            if resp["discriminante"]:
                numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["discriminante"])
                st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#22c55e;font-size:0.85rem;">💡 Recomendación: Estos números están en la matriz pero NO son calientes ni posibles. Podrían ser su mejor oportunidad.</p>', unsafe_allow_html=True)
            else:
                st.info("No hay números discriminantes.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[3]:
    st.markdown(f'<div class="card"><h3>📖 Charada Enriquecida</h3>', unsafe_allow_html=True)

    num_buscar = st.number_input("Buscar por número (0-99)", min_value=0, max_value=99, value=1, key="charada_search")
    if st.button("🔍 Buscar", type="primary"):
        charada = api_get("/api/charada/enriquecida", {"numero": num_buscar})
        if charada and len(charada) > 0:
            entry = charada[0]
            st.markdown(f'<h2 style="color:#fbbf24;font-size:2.5rem;text-align:center;">{entry["numero"]}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p style="text-align:center;color:#94a3b8;font-size:1.1rem;">Categoría: <strong style="color:#22c55e;">{entry["categoria"].title()}</strong></p>', unsafe_allow_html=True)

            st.markdown('<h4 style="color:#f1f5f9;">Significados:</h4>', unsafe_allow_html=True)
            for sig in entry["significados"]:
                st.markdown(f'<p style="color:#94a3b8;padding-left:1rem;">• {sig}</p>', unsafe_allow_html=True)

            st.markdown(f'<h4 style="color:#f1f5f9;">Palabras Clave:</h4>', unsafe_allow_html=True)
            cols = st.columns(6)
            for i, kw in enumerate(entry["palabras_clave"]):
                with cols[i % 6]:
                    st.markdown(f'<span class="result-number" style="font-size:0.85rem;width:auto;padding:0.2rem 0.6rem;">{kw}</span>', unsafe_allow_html=True)
        else:
            st.warning(f"No se encontró el número {num_buscar} en la Charada.")

    st.markdown("---")
    st.markdown('<h4 style="color:#f1f5f9;">📋 Todas las Categorías</h4>', unsafe_allow_html=True)

    todas = api_get("/api/charada/enriquecida")
    if todas:
        cats = {}
        for e in todas:
            cat = e["categoria"]
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(e["numero"])

        for cat_name, nums in sorted(cats.items()):
            with st.expander(f"{cat_name.title()} ({len(nums)} números)"):
                numeros_html = "".join(f'<span class="result-number">{n}</span>' for n in nums)
                st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
