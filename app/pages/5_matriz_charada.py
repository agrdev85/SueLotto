import streamlit as st
import httpx
import os
import re as re_mod
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
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] { background: #1e293b; border-radius: 0.5rem 0.5rem 0 0; padding: 0.5rem 1.5rem; color: #94a3b8; }
    .stTabs [aria-selected="true"] { background: #334155; color: #fbbf24; }
    .charada-scroll { max-height: 400px; overflow-y: auto; padding-right: 0.5rem; margin-top: 0.5rem; }
    .charada-scroll::-webkit-scrollbar { width: 6px; }
    .charada-scroll::-webkit-scrollbar-track { background: #1e293b; border-radius: 3px; }
    .charada-scroll::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
    .matrix-cell { padding: 6px 2px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 0.85rem; cursor: pointer; transition: opacity 0.2s; }
    .matrix-cell:hover { opacity: 0.8; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align:center;color:#fbbf24;">🔢 Matriz & Charada</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#94a3b8;">Análisis matricial de números • Comparación con calientes y posibles</p>', unsafe_allow_html=True)

MATRIZ_NUEVA = [
    [1, 100, 2, 99, 3, 98, 4, 97, 5, 96],
    [6, 95, 7, 94, 8, 93, 9, 92, 10, 91],
    [11, 90, 12, 89, 13, 88, 14, 87, 15, 86],
    [16, 85, 17, 84, 18, 83, 19, 82, 20, 81],
    [21, 80, 22, 79, 23, 78, 24, 77, 25, 76],
    [26, 75, 27, 74, 28, 73, 29, 72, 30, 71],
    [31, 70, 32, 69, 33, 68, 34, 67, 35, 66],
    [36, 65, 37, 64, 38, 63, 39, 62, 40, 61],
    [41, 60, 42, 59, 43, 58, 44, 57, 45, 56],
    [46, 55, 47, 54, 48, 53, 49, 52, 50, 51],
]

MATRIZ_VIEJA = [
    [14, 46, 69, 1, 0, 62, 89, 28, 0, 57, 97],
    [66, 37, 99, 13, 79, 78, 0, 17, 90, 70, 0],
    [33, 60, 12, 98, 61, 0, 71, 80, 10, 0, 27],
    [100, 21, 2, 32, 91, 72, 0, 77, 96, 54, 81],
    [47, 82, 53, 31, 56, 0, 9, 0, 35, 92, 4],
    [25, 58, 0, 36, 87, 49, 83, 16, 0, 59, 0],
    [74, 0, 40, 0, 64, 11, 3, 45, 41, 84, 75],
    [0, 76, 24, 68, 93, 20, 73, 15, 85, 8, 0],
    [19, 7, 48, 50, 38, 0, 30, 51, 63, 0, 39],
    [29, 42, 0, 34, 52, 43, 94, 0, 5, 55, 86],
    [95, 65, 44, 88, 6, 22, 67, 0, 18, 23, 26],
]


@st.cache_data(ttl=60)
def api_get(path: str, params: dict = None):
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return None


def api_post(path: str, data: dict):
    try:
        r = httpx.post(f"{API_URL}{path}", json=data, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


tipo_matriz = st.selectbox("Tipo de Matriz", ["nueva", "vieja"],
                           format_func=lambda x: "Nueva (10x10)" if x == "nueva" else "Vieja (11x11)")

tabs = st.tabs(["📊 Matriz Visual", "🔍 Alrededor", "📈 Comparar & Reducir", "📖 Charada Enriquecida"])

# ─── Tab 0: Matriz Visual ────────────────────────────────────────
with tabs[0]:
    st.markdown(f'<div class="card"><h3>📊 Matriz {tipo_matriz.title()} {"(10x10)" if tipo_matriz == "nueva" else "(11x11)"}</h3>', unsafe_allow_html=True)

    calientes_data = api_get("/api/estadisticas/calientes", {"juego": "Pick 3", "limite": 10, "sorteo": "E"})
    posibles_data = api_get("/api/estadisticas/posibles-salir", {"juego": "Pick 3", "sorteo": "E"})

    set_calientes = set(calientes_data.get("numeros", [])) if calientes_data else set()
    set_posibles = set(posibles_data.get("numeros", [])) if posibles_data else set()
    set_ambos = set_calientes & set_posibles

    st.session_state.setdefault("matriz_sel", None)
    st.session_state.setdefault("matriz_tipo", tipo_matriz)
    if st.session_state.matriz_tipo != tipo_matriz:
        st.session_state.matriz_tipo = tipo_matriz
        st.session_state.matriz_sel = None

    matriz_actual = MATRIZ_NUEVA if tipo_matriz == "nueva" else MATRIZ_VIEJA

    # Read matrix click from query params (set by JavaScript, no page reload)
    mr = st.query_params.get("mr")
    mc = st.query_params.get("mc")
    if mr is not None and mc is not None:
        try:
            val = matriz_actual[int(mr)][int(mc)]
            if val != 0:
                st.session_state.matriz_sel = int(val)
        except (ValueError, IndexError):
            pass

    cols_labels = [chr(ord('a') + i) for i in range(len(matriz_actual[0]))]

    def cell_color(val):
        if val == 0: return '#0f172a'
        if val == st.session_state.get("matriz_sel"): return 'linear-gradient(135deg,#3b82f6,#8b5cf6)'
        if val in set_ambos: return '#fbbf24'
        if val in set_calientes: return '#ef4444'
        if val in set_posibles: return '#3b82f6'
        return '#1e293b'

    def cell_text(val):
        if val == 0: return '#475569'
        if val in set_ambos: return '#0f172a'
        return 'white'

    html = '<div style="overflow-x:auto;"><table style="border-collapse:collapse;width:100%;">'
    html += '<tr><td style="width:1.2rem;"></td>'
    for c_label in cols_labels:
        html += f'<td style="text-align:center;color:#64748b;font-size:0.7rem;padding:2px 1px;">{c_label.upper()}</td>'
    html += '</tr>'
    for i, row in enumerate(matriz_actual):
        html += f'<tr><td style="text-align:center;color:#64748b;font-size:0.65rem;">{i+1}</td>'
        for j, val in enumerate(row):
            bg = cell_color(val)
            tc = cell_text(val)
            label = str(val) if val != 0 else ''
            if val != 0:
                html += (f'<td class="matrix-cell" style="background:{bg};color:{tc};" '
                         f'onclick="var u=new URL(window.location);u.searchParams.set(\'mr\',{i});u.searchParams.set(\'mc\',{j});window.history.pushState({{}},\'\',u);window.dispatchEvent(new Event(\'popstate\'))">{label}</td>')
            else:
                html += f'<td style="background:{bg};color:{tc};padding:6px 2px;text-align:center;border-radius:4px;font-size:0.85rem;"></td>'
        html += '</tr>'
    html += '</table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # Alrededor card below the matrix
    sel_num = st.session_state.matriz_sel
    if sel_num is not None:
        resp = api_post("/api/matriz/alrededor", {"numero": sel_num, "tipo_matriz": tipo_matriz})
        if resp:
            numeros = resp["numeros"]
            chunks = [numeros[i:i+10] for i in range(0, len(numeros), 10)]
            rows_html = ""
            for chunk in chunks:
                nums = "".join(
                    f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                    f'background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:white;font-weight:bold;'
                    f'font-size:0.95rem;width:2.2rem;height:2.2rem;border-radius:0.4rem;'
                    f'margin:0.15rem;">{n}</span>' for n in chunk
                )
                rows_html += f'<div style="display:flex;gap:0.3rem;margin-bottom:0.3rem;">{nums}</div>'
            st.markdown(f'''
            <div style="background:#1e293b;border:1px solid #334155;border-radius:0.75rem;padding:1rem;margin-top:1rem;">
                <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;">
                    <span style="font-size:2rem;font-weight:bold;color:#fbbf24;">{sel_num}</span>
                    <span style="color:#94a3b8;font-size:0.95rem;">Números alrededor · <strong style="color:#f1f5f9;">{len(numeros)}</strong></span>
                </div>
                {rows_html}
            </div>
            ''', unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;gap:1.5rem;margin-top:1rem;flex-wrap:wrap;">
        <div><span style="display:inline-block;width:1rem;height:1rem;background:linear-gradient(135deg,#3b82f6,#8b5cf6);border-radius:0.25rem;margin-right:0.3rem;"></span> Seleccionado</div>
        <div><span style="display:inline-block;width:1rem;height:1rem;background:#ef4444;border-radius:0.25rem;margin-right:0.3rem;"></span> Caliente</div>
        <div><span style="display:inline-block;width:1rem;height:1rem;background:#3b82f6;border-radius:0.25rem;margin-right:0.3rem;"></span> Posible</div>
        <div><span style="display:inline-block;width:1rem;height:1rem;background:#fbbf24;border-radius:0.25rem;margin-right:0.3rem;"></span> Caliente + Posible</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Tab 1: Alrededor ────────────────────────────────────────────
with tabs[1]:
    st.markdown(f'<div class="card"><h3>🔍 Números Alrededor</h3>', unsafe_allow_html=True)

    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        num1 = st.number_input("Número 1", min_value=1, max_value=100, value=5)
    with col_a2:
        num2 = st.number_input("Número 2", min_value=1, max_value=100, value=12)
    with col_a3:
        num3 = st.number_input("Número 3 (opcional)", min_value=1, max_value=100, value=34)

    secuencia = [n for n in [num1, num2, num3] if n >= 1]

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

# ─── Tab 2: Comparar & Reducir ───────────────────────────────────
with tabs[2]:
    st.markdown(f'<div class="card"><h3>📈 Comparar & Reducir</h3>', unsafe_allow_html=True)

    with st.expander("⚙️ Opciones de calientes y posibles", expanded=True):
        col_game, col_sorteo = st.columns(2)
        with col_game:
            juego_cal = st.selectbox("Juego", ["Pick 3", "Pick 4"], key="juego_comp")
        with col_sorteo:
            sorteo_cal = st.selectbox("Sorteo", ["E", "M"], key="sorteo_comp")

    if st.button("📊 Comparar y Reducir", type="primary", use_container_width=True):
        secuencia_comp = [n for n in [num1, num2, num3] if n >= 1]

        calientes_resp = api_get("/api/estadisticas/calientes", {"juego": juego_cal, "sorteo": sorteo_cal, "limite": 20, "dias": 30})
        posibles_resp = api_get("/api/estadisticas/posibles-salir", {"juego": juego_cal, "sorteo": sorteo_cal})
        calientes = calientes_resp.get("numeros", []) if calientes_resp else []
        posibles = posibles_resp.get("numeros", []) if posibles_resp else []

        resp = api_post("/api/matriz/comparar", {
            "secuencia": secuencia_comp,
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

# ─── Tab 3: Charada Enriquecida ──────────────────────────────────
with tabs[3]:
    st.markdown(f'<div class="card"><h3>📖 Charada Enriquecida</h3>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        num_buscar = st.number_input("Buscar por número (1-100)", min_value=1, max_value=100, value=1, key="charada_search")
    with col_c2:
        texto_buscar = st.text_input("Buscar por palabra o significado", placeholder="Ej: perro, amor, río... (Enter para buscar)", key="charada_text")

    todas = api_get("/api/charada/enriquecida")

    texto_lower = texto_buscar.strip().lower() if texto_buscar.strip() else ""

    if texto_lower:
        filtered = []
        if todas:
            for e in todas:
                sigs_text = " ".join(e["significados"]).lower()
                if texto_lower in sigs_text or texto_lower in str(e["numero"]):
                    filtered.append(e)
        charada_data = filtered
    elif num_buscar and todas:
        charada_data = [e for e in todas if e["numero"] == num_buscar]
    else:
        charada_data = todas

    if charada_data and len(charada_data) > 0:
        entry = charada_data[0]
        st.markdown(f'<h2 style="color:#fbbf24;font-size:2.5rem;text-align:center;">{entry["numero"]:02d}</h2>', unsafe_allow_html=True)
        st.markdown(f'<p style="text-align:center;color:#94a3b8;font-size:1.1rem;">Categoría: <strong style="color:#22c55e;">{entry["categoria"].title()}</strong></p>', unsafe_allow_html=True)
        st.markdown(f'<p style="text-align:center;color:#94a3b8;font-size:0.9rem;">Palabras clave: {", ".join(entry["palabras_clave"])}</p>', unsafe_allow_html=True)

        st.markdown('<h4 style="color:#f1f5f9;">Significados:</h4><div class="charada-scroll">', unsafe_allow_html=True)
        for sig in entry["significados"]:
            highlighted = sig
            if texto_lower:
                highlighted = re_mod.sub(f'(?i)({re_mod.escape(texto_lower)})', r'<mark style="background:#fbbf24;color:#0f172a;padding:0.1rem 0.3rem;border-radius:0.2rem;">\1</mark>', sig)
            st.markdown(f'<p style="color:#94a3b8;padding-left:1rem;">• {highlighted}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if len(charada_data) > 1:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<h4 style="color:#f1f5f9;">Más resultados:</h4>', unsafe_allow_html=True)
            for e in charada_data[1:6]:
                st.markdown(f'<div style="background:#334155;padding:0.5rem 1rem;border-radius:0.5rem;margin:0.25rem 0;">'
                           f'<span style="color:#fbbf24;font-weight:bold;font-size:1.2rem;">{e["numero"]:02d}</span>'
                           f' → <span style="color:#f1f5f9;">{e["significados"][0]}</span>'
                           f' <span style="color:#64748b;font-size:0.85rem;">({e["categoria"]})</span></div>', unsafe_allow_html=True)
    else:
        if texto_buscar.strip() or num_buscar:
            st.warning(f"No se encontraron resultados.")
        elif todas:
            st.info("Selecciona un número o escribe una palabra para buscar.")

    st.markdown("---")
    st.markdown('<h4 style="color:#f1f5f9;">📋 Todas las Categorías</h4>', unsafe_allow_html=True)

    if todas:
        cats = {}
        for e in todas:
            cat = e["categoria"]
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(e["numero"])

        for cat_name, nums in sorted(cats.items()):
            with st.expander(f"{cat_name.title()} ({len(nums)} números)"):
                numeros_html = "".join(f'<span class="result-number">{n:02d}</span>' for n in nums)
                st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
