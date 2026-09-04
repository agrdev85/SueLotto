import streamlit as st
import re as re_mod
import os, sys
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Matriz & Charada", page_icon="🔢", layout="wide")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.shared import render_global_header, api_get, api_post, init_session_state, render_pro_card

init_session_state()

if not st.session_state.get("user"):
    st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">Acceso Restringido</h2><p style="color:#94a3b8;">Necesitas iniciar sesión.</p></div>', unsafe_allow_html=True)
    st.stop()

render_global_header()

tier_info = api_get("/api/auth/tier")
if not tier_info or tier_info.get("tier") not in ("pro", "lifetime", "admin"):
    render_pro_card(
        description_html=(
            'La Matriz Charada es una funcionalidad exclusiva para usuarios '
            '<strong style="color:#fbbf24;">Pro</strong> y '
            '<strong style="color:#8b5cf6;">De por Vida</strong>.'
        ),
        plan_features_html=(
            "✓ Sin límites diarios · ✓ IA + Adivinanzas · ✓ Matriz Charada · "
            "✓ Soporte prioritario"
        ),
        cta_key="upgrade_cta_matriz",
        bg="linear-gradient(135deg, #1e293b, #1e3a5f)",
        border_color="#334155",
    )
    st.stop()

st.markdown("""
<style>
    .result-number { display: inline-block; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; font-weight: bold;
                     font-size: 1.2rem; width: 2.5rem; height: 2.5rem; text-align: center; line-height: 2.5rem; border-radius: 0.5rem; margin: 0 0.15rem; }
    .charada-scroll { max-height: 400px; overflow-y: auto; padding-right: 0.5rem; margin-top: 0.5rem; }
    .charada-scroll::-webkit-scrollbar { width: 6px; }
    .charada-scroll::-webkit-scrollbar-track { background: #1e293b; border-radius: 3px; }
    .charada-scroll::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
    .matrix-cell { padding: 6px 2px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 0.85rem; cursor: pointer; transition: opacity 0.2s; }
    .matrix-cell:hover { opacity: 0.8; }
    .sig-flex { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .sig-flex > span { background: #334155; border: 1px solid #475569; border-radius: 0.4rem; padding: 0.3rem 0.7rem; color: #e2e8f0; font-size: 0.85rem; white-space: nowrap; }
    .grid-num { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .grid-num > a { text-decoration: none; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align:center;color:#fbbf24;">🔢 Matriz & Charada</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:var(--text-secondary);">Análisis matricial de números • Comparación con calientes y posibles</p>', unsafe_allow_html=True)

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


tipo_matriz = st.selectbox("Tipo de Matriz", ["nueva", "vieja"],
                           format_func=lambda x: "Nueva (10x10)" if x == "nueva" else "Vieja (11x11)")

tabs = st.tabs(["📊 Matriz Visual", "🔍 Alrededor", "📈 Comparar & Reducir", "📊 Análisis Completo", "📖 Charada Enriquecida"])

# ─── Tab 0: Matriz Visual ────────────────────────────────────────
with tabs[0]:

    matriz_actual = MATRIZ_NUEVA if tipo_matriz == "nueva" else MATRIZ_VIEJA
    cols_labels = [chr(ord("a") + i) for i in range(len(matriz_actual[0]))]

    freq_data = api_get("/api/estadisticas/frecuencias", {"juego": "Pick 3", "sorteo": "E", "dias": 90}) or []
    calientes_data = api_get("/api/estadisticas/calientes", {"juego": "Pick 3", "sorteo": "E", "limite": 15, "dias": 30}) or {}
    posibles_data = api_get("/api/estadisticas/posibles-salir", {"juego": "Pick 3", "sorteo": "E"}) or {}

    set_calientes = set(calientes_data.get("numeros", []))
    set_posibles = set(posibles_data.get("numeros", []))
    set_ambos = set_calientes & set_posibles

    freq_map = {f.get("numero"): f.get("frecuencia", 0) for f in freq_data}
    if len(freq_map) >= 20 and set_calientes:
        sorted_nums = sorted(freq_map, key=lambda n: freq_map[n])
        set_frios = set(sorted_nums[:15])
    else:
        set_frios = set()

    CAT_EMOJI = {
        "ambos": "🟠",
        "caliente": "🔴",
        "posible": "🔵",
        "frio": "🟣",
        "normal": "⚪",
    }

    def _cat(_v):
        if _v in set_ambos:
            return "ambos"
        if _v in set_calientes:
            return "caliente"
        if _v in set_posibles:
            return "posible"
        if _v in set_frios:
            return "frio"
        return "normal"

    st.markdown(f'<div class="card"><h3>📊 Matriz {tipo_matriz.title()} {"(10x10)" if tipo_matriz == "nueva" else "(11x11)"}</h3>', unsafe_allow_html=True)

    st.markdown('<p style="color:#94a3b8;font-size:0.85rem;margin-bottom:0.4rem;">💡 Haz clic en una celda de la matriz: se marca como activo y abajo se muestran sus números alrededor.</p>', unsafe_allow_html=True)

    st.markdown("""
    <style>
      div[data-testid="stVerticalBlockBorderWrapper"] div.stButton > button { min-height: 36px; line-height: 1; }
    </style>
    """, unsafe_allow_html=True)

    @st.fragment
    def _matriz_fragment():
        _sel = st.session_state.get("matriz_sel")

        # Header de columnas
        _hcols = st.columns([0.4] + [1.0] * len(cols_labels))
        with _hcols[0]:
            st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)
        for _ci, _cl in enumerate(cols_labels):
            with _hcols[_ci + 1]:
                st.markdown(f'<div style="text-align:center;color:#fbbf24;font-weight:bold;font-size:0.75rem;line-height:30px;">{_cl.upper()}</div>', unsafe_allow_html=True)

        # Cada fila: etiqueta + botones nativos por celda
        for _ri, row in enumerate(matriz_actual):
            _cols = st.columns([0.4] + [1.0] * len(cols_labels))
            with _cols[0]:
                st.markdown(f'<div style="text-align:center;color:#fbbf24;font-weight:bold;font-size:0.75rem;line-height:36px;">{_ri+1}</div>', unsafe_allow_html=True)
            for _ci, _val in enumerate(row):
                with _cols[_ci + 1]:
                    if _val == 0:
                        st.markdown('<div style="height:36px;"></div>', unsafe_allow_html=True)
                    else:
                        _activo = (st.session_state.get("matriz_sel") == _val)
                        _emo = CAT_EMOJI[_cat(_val)]
                        if st.button(
                            f"{_emo} {_val:02d}",
                            key=f"mc_{tipo_matriz}_{_val}",
                            use_container_width=True,
                            type="primary" if _activo else "secondary",
                        ):
                            st.session_state.matriz_sel = _val
                            st.rerun(scope="fragment")

        st.markdown('<div style="height:0.25rem;"></div>', unsafe_allow_html=True)

        _sel = st.session_state.get("matriz_sel")
        if _sel is not None:
            _alr = api_post("/api/matriz/alrededor", {"numero": int(_sel), "tipo_matriz": tipo_matriz})
            if _alr:
                st.markdown(
                    f'<div style="background:#1e293b;border:1px solid #334155;border-radius:0.75rem;padding:0.8rem 1rem;margin-top:0.5rem;margin-bottom:0.5rem;">'
                    f'<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem;">'
                    f'<span style="font-size:1.8rem;font-weight:bold;color:#fbbf24;">{_sel}</span>'
                    f'<span style="color:#94a3b8;font-size:0.9rem;">Número activo · {CAT_EMOJI[_cat(_sel)]} {_cat(_sel).title()} · Alrededor <strong style="color:#f1f5f9;">{_alr["total"]}</strong></span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                nums_html = "".join(
                    f'<span class="result-number">{x}</span>' for x in _alr["numeros"]
                )
                st.markdown(f'<div>{nums_html}</div>', unsafe_allow_html=True)

    _matriz_fragment()

    st.markdown("""
    <div style="display:flex;gap:1.2rem;margin-top:0.5rem;flex-wrap:wrap;">
        <div><span>🟠</span> Caliente + Posible</div>
        <div><span>🔴</span> Caliente</div>
        <div><span>🔵</span> Posible</div>
        <div><span>🟣</span> Frío</div>
        <div><span>⚪</span> Normal</div>
        <div><span style="display:inline-block;width:0.95rem;height:0.95rem;background:linear-gradient(135deg,#7c3aed,#4f46e5);border-radius:0.25rem;margin-right:0.3rem;"></span> Activo</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

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

    if st.button("🔍 Obtener Alrededor", type="primary", width='stretch'):
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
        col_game, col_sorteo, col_lim = st.columns([1, 1, 1])
        with col_game:
            juego_cal = st.selectbox("Juego", ["Pick 3", "Pick 4"], key="juego_comp")
        with col_sorteo:
            sorteo_cal = st.selectbox("Sorteo", ["E", "M"], key="sorteo_comp")
        with col_lim:
            limite_top = st.slider("Top N del score", min_value=3, max_value=50, value=15, step=1, key="limite_score")

    if st.button("📊 Comparar y Reducir", type="primary", width='stretch'):
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
            "juego": juego_cal,
            "sorteo": sorteo_cal,
            "limite": limite_top,
        })
        if resp:
            scored = resp.get("scored_final", [])

            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.metric("Alrededor", resp["total_alrededor"])
            with m2:
                st.metric("🔴 Calientes", resp["total_interseccion_calientes"])
            with m3:
                st.metric("🔵 Posibles", resp["total_interseccion_posibles"])
            with m4:
                st.metric("🟡 Ambos", resp["total_interseccion_ambos"])
            with m5:
                st.metric("🏆 Score Final", len(scored))

            _cat_colors = {
                "ambos": "#fbbf24",
                "caliente": "#ef4444",
                "posible": "#3b82f6",
                "discriminante": "#22c55e",
            }
            _cat_labels = {
                "ambos": "🔥 Cal+Pos",
                "caliente": "🔴 Caliente",
                "posible": "🔵 Posible",
                "discriminante": "🟢 Discriminante",
            }

            if scored:
                st.markdown(
                    f'<div class="card" style="margin-top:1rem;">'
                    f'<h3 style="color:#fbbf24;">🏆 Top {len(scored)} — Score Estadístico Final</h3>'
                    f'<p style="color:#94a3b8;font-size:0.85rem;">'
f'Clasificación de TODOS los números alrededor por score compuesto '
f'(frecuencia 25% + atraso 35% + ML 40%). '
f'Categoría asignada: 🔴caliente, 🔵posible, 🟡ambos, 🟢discriminante.</p>'
                    f'<div style="display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap;">'
                    f'<span><span style="display:inline-block;width:0.8rem;height:0.8rem;background:#ef4444;border-radius:0.2rem;"></span> Caliente</span>'
                    f'<span><span style="display:inline-block;width:0.8rem;height:0.8rem;background:#3b82f6;border-radius:0.2rem;"></span> Posible</span>'
                    f'<span><span style="display:inline-block;width:0.8rem;height:0.8rem;background:#fbbf24;border-radius:0.2rem;"></span> Caliente+Posible</span>'
                    f'<span><span style="display:inline-block;width:0.8rem;height:0.8rem;background:#22c55e;border-radius:0.2rem;"></span> Discriminante</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                for i, s in enumerate(scored):
                    cat = s.get("categoria", "discriminante")
                    cat_color = _cat_colors.get(cat, "#22c55e")
                    cat_label = _cat_labels.get(cat, "🟢 Disc.")
                    bar_w = max(int(s["score"] * 100), 3)
                    freq_7d = s.get("frecuencia_7d", 0)
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0;border-bottom:1px solid #1e293b;">'
                        f'<span style="color:#64748b;min-width:1.5rem;font-size:0.8rem;">#{i+1}</span>'
                        f'<span style="background:{cat_color};color:#0f172a;font-weight:bold;border-radius:0.3rem;padding:0.1rem 0.5rem;min-width:2.5rem;text-align:center;">{s["numero"]:02d}</span>'
                        f'<span style="color:{cat_color};font-size:0.65rem;min-width:4.5rem;font-weight:600;">{cat_label}</span>'
                        f'<div style="flex:1;background:#1e293b;height:0.6rem;border-radius:0.3rem;">'
                        f'<div style="background:linear-gradient(90deg,{cat_color},#fbbf24);width:{bar_w}%;height:100%;border-radius:0.3rem;"></div></div>'
                        f'<span style="color:#94a3b8;font-size:0.7rem;min-width:1.8rem;text-align:right;" title="Frecuencia 90d">{s["frecuencia"]}×</span>'
                        f'<span style="color:#fbbf24;font-size:0.7rem;min-width:1.8rem;text-align:right;" title="Frecuencia últimos 7 días">{"🔥" + str(freq_7d) + "×" if freq_7d else ""}</span>'
                        f'<span style="color:#94a3b8;font-size:0.7rem;min-width:1.5rem;text-align:right;" title="Días sin salir">{s["dias_sin_salir"]}d</span>'
                        f'<span style="color:#22c55e;font-size:0.7rem;min-width:2rem;text-align:right;" title="Probabilidad ML">{s.get("probabilidad_ml", 0):.1%}</span>'
                    f'<span style="color:#a78bfa;font-size:0.65rem;min-width:1.8rem;text-align:right;" title="Tendencia (últimos 15d vs 15d ant)">{("📈" + str(round(s["tendencia"] * 100)) + "%") if s.get("tendencia", 0) > 0 else ("📉" + str(round(abs(s["tendencia"]) * 100)) + "%") if s.get("tendencia", 0) < 0 else ""}</span>'
                    f'<span style="color:#f59e0b;font-size:0.65rem;min-width:1.5rem;text-align:right;" title="Score dígitos (0-9) del par">{str(round(s.get("digito_score", 0) * 100)) + "%" if s.get("digito_score", 0) else ""}</span>'
                        f'</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="card" style="margin-top:1rem;">'
                    f'<h4 style="color:#94a3b8;">⏳ No hay suficientes datos para calcular el score</h4>'
                    f'<p style="color:#64748b;font-size:0.85rem;">Asegúrate de tener resultados históricos importados.</p>'
                    f'</div>', unsafe_allow_html=True
                )

            with st.expander("📊 Desglose por categorías", expanded=False):
                st.markdown(
                    f'<div class="card">'
                    f'<h4>🔴 Calientes en Alrededor ({resp["total_interseccion_calientes"]})</h4>',
                    unsafe_allow_html=True,
                )
                if resp["interseccion_calientes"]:
                    numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_calientes"])
                    st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(
                    f'<div class="card">'
                    f'<h4>🔵 Posibles en Alrededor ({resp["total_interseccion_posibles"]})</h4>',
                    unsafe_allow_html=True,
                )
                if resp["interseccion_posibles"]:
                    numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_posibles"])
                    st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(
                    f'<div class="card">'
                    f'<h4>🟡 Caliente + Posible ({resp["total_interseccion_ambos"]})</h4>',
                    unsafe_allow_html=True,
                )
                if resp["interseccion_ambos"]:
                    numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_ambos"])
                    st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No hay números que sean calientes y posibles a la vez.")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(
                    f'<div class="card">'
                    f'<h4>🟢 Discriminante ({resp["total_discriminante"]}) · '
                    f'<span style="color:#94a3b8;font-size:0.85rem;">Alrededor − Calientes − Posibles</span></h4>',
                    unsafe_allow_html=True,
                )
                if resp["discriminante"]:
                    numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["discriminante"])
                    st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No hay números discriminantes.")
                st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Tab 3: Análisis Completo ────────────────────────────────────
with tabs[3]:
    st.markdown(f'<div class="card"><h3>📊 Análisis Estadístico Completo</h3>'
                f'<p style="color:#94a3b8;font-size:0.85rem;">'
                f'Todos los números «alrededor» clasificados por score — incluye calientes, posibles y discriminantes.</p>',
                unsafe_allow_html=True)

    with st.expander("⚙️ Opciones de análisis", expanded=True):
        col_game, col_sorteo, col_lim = st.columns([1, 1, 1])
        with col_game:
            juego_completo = st.selectbox("Juego", ["Pick 3", "Pick 4"], key="juego_completo")
        with col_sorteo:
            sorteo_completo = st.selectbox("Sorteo", ["E", "M"], key="sorteo_completo")
        with col_lim:
            top_n = st.slider("Top N del score completo", min_value=3, max_value=70, value=15, step=1, key="top_n_completo")

    if st.button("📊 Analizar Todo", type="primary", width='stretch'):
        secuencia_comp = [n for n in [num1, num2, num3] if n >= 1]

        calientes_resp = api_get("/api/estadisticas/calientes", {"juego": juego_completo, "sorteo": sorteo_completo, "limite": 20, "dias": 30})
        posibles_resp = api_get("/api/estadisticas/posibles-salir", {"juego": juego_completo, "sorteo": sorteo_completo})
        calientes = calientes_resp.get("numeros", []) if calientes_resp else []
        posibles = posibles_resp.get("numeros", []) if posibles_resp else []

        resp = api_post("/api/matriz/comparar", {
            "secuencia": secuencia_comp,
            "tipo_matriz": tipo_matriz,
            "calientes": calientes,
            "posibles": posibles,
            "juego": juego_completo,
            "sorteo": sorteo_completo,
            "limite": top_n,
            "modo": "completo",
        })
        if resp:
            scored = resp.get("scored_completo", [])

            _cat_colors = {
                "ambos": "#fbbf24",
                "caliente": "#ef4444",
                "posible": "#3b82f6",
                "discriminante": "#22c55e",
            }
            _cat_labels = {
                "ambos": "🔥 Cal+Pos",
                "caliente": "🔴 Caliente",
                "posible": "🔵 Posible",
                "discriminante": "🟢 Discriminante",
            }

            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.metric("Alrededor", resp["total_alrededor"])
            with m2:
                st.metric("🔴 Calientes", resp["total_interseccion_calientes"])
            with m3:
                st.metric("🔵 Posibles", resp["total_interseccion_posibles"])
            with m4:
                st.metric("🟡 Ambos", resp["total_interseccion_ambos"])
            with m5:
                st.metric("🏆 Score Completo", len(scored))

            if scored:
                st.markdown(
                    f'<div class="card" style="margin-top:1rem;">'
                    f'<h3 style="color:#fbbf24;">🏆 Top {len(scored)} — Score Completo</h3>'
                    f'<p style="color:#94a3b8;font-size:0.85rem;">'
                    f'Clasificación de TODOS los números alrededor por score compuesto '
                    f'(frecuencia 25% + atraso 35% + ML 40%). '
                    f'Categoría asignada: 🔴caliente, 🔵posible, 🟡ambos, 🟢discriminante.</p>'
                    f'<div style="display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap;">'
                    f'<span><span style="display:inline-block;width:0.8rem;height:0.8rem;background:#ef4444;border-radius:0.2rem;"></span> Caliente</span>'
                    f'<span><span style="display:inline-block;width:0.8rem;height:0.8rem;background:#3b82f6;border-radius:0.2rem;"></span> Posible</span>'
                    f'<span><span style="display:inline-block;width:0.8rem;height:0.8rem;background:#fbbf24;border-radius:0.2rem;"></span> Caliente+Posible</span>'
                    f'<span><span style="display:inline-block;width:0.8rem;height:0.8rem;background:#22c55e;border-radius:0.2rem;"></span> Discriminante</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                for i, s in enumerate(scored):
                    cat = s.get("categoria", "discriminante")
                    cat_color = _cat_colors.get(cat, "#22c55e")
                    cat_label = _cat_labels.get(cat, "🟢 Disc.")
                    bar_w = max(int(s["score"] * 100), 3)
                    freq_7d = s.get("frecuencia_7d", 0)
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0;border-bottom:1px solid #1e293b;">'
                        f'<span style="color:#64748b;min-width:1.5rem;font-size:0.8rem;">#{i+1}</span>'
                        f'<span style="background:{cat_color};color:#0f172a;font-weight:bold;border-radius:0.3rem;padding:0.1rem 0.5rem;min-width:2.5rem;text-align:center;">{s["numero"]:02d}</span>'
                        f'<span style="color:{cat_color};font-size:0.65rem;min-width:4.5rem;font-weight:600;">{cat_label}</span>'
                        f'<div style="flex:1;background:#1e293b;height:0.6rem;border-radius:0.3rem;">'
                        f'<div style="background:linear-gradient(90deg,{cat_color},#fbbf24);width:{bar_w}%;height:100%;border-radius:0.3rem;"></div></div>'
                        f'<span style="color:#94a3b8;font-size:0.7rem;min-width:1.8rem;text-align:right;" title="Frecuencia 90d">{s["frecuencia"]}×</span>'
                        f'<span style="color:#fbbf24;font-size:0.7rem;min-width:1.8rem;text-align:right;" title="Frecuencia últimos 7 días">{"🔥" + str(freq_7d) + "×" if freq_7d else ""}</span>'
                        f'<span style="color:#94a3b8;font-size:0.7rem;min-width:1.5rem;text-align:right;" title="Días sin salir">{s["dias_sin_salir"]}d</span>'
                        f'<span style="color:#22c55e;font-size:0.7rem;min-width:2rem;text-align:right;" title="Probabilidad ML">{s.get("probabilidad_ml", 0):.1%}</span>'
                    f'<span style="color:#a78bfa;font-size:0.65rem;min-width:1.8rem;text-align:right;" title="Tendencia (últimos 15d vs 15d ant)">{("📈" + str(round(s["tendencia"] * 100)) + "%") if s.get("tendencia", 0) > 0 else ("📉" + str(round(abs(s["tendencia"]) * 100)) + "%") if s.get("tendencia", 0) < 0 else ""}</span>'
                    f'<span style="color:#f59e0b;font-size:0.65rem;min-width:1.5rem;text-align:right;" title="Score dígitos (0-9) del par">{str(round(s.get("digito_score", 0) * 100)) + "%" if s.get("digito_score", 0) else ""}</span>'
                        f'</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="card" style="margin-top:1rem;">'
                    f'<h4 style="color:#94a3b8;">⏳ No hay suficientes datos para calcular el score completo</h4>'
                    f'<p style="color:#64748b;font-size:0.85rem;">Asegúrate de tener resultados históricos importados.</p>'
                    f'</div>', unsafe_allow_html=True
                )

            with st.expander("📊 Distribución por categoría", expanded=False):
                st.markdown(
                    f'<div class="card">'
                    f'<h4>🔴 Calientes en Alrededor ({resp["total_interseccion_calientes"]})</h4>',
                    unsafe_allow_html=True,
                )
                if resp["interseccion_calientes"]:
                    numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_calientes"])
                    st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(
                    f'<div class="card">'
                    f'<h4>🔵 Posibles en Alrededor ({resp["total_interseccion_posibles"]})</h4>',
                    unsafe_allow_html=True,
                )
                if resp["interseccion_posibles"]:
                    numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_posibles"])
                    st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(
                    f'<div class="card">'
                    f'<h4>🟡 Caliente + Posible ({resp["total_interseccion_ambos"]})</h4>',
                    unsafe_allow_html=True,
                )
                if resp["interseccion_ambos"]:
                    numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["interseccion_ambos"])
                    st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No hay números que sean calientes y posibles a la vez.")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(
                    f'<div class="card">'
                    f'<h4>🟢 Discriminante ({resp["total_discriminante"]}) · '
                    f'<span style="color:#94a3b8;font-size:0.85rem;">Alrededor − Calientes − Posibles</span></h4>',
                    unsafe_allow_html=True,
                )
                if resp["discriminante"]:
                    numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["discriminante"])
                    st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("No hay números discriminantes.")
                st.markdown('</div>', unsafe_allow_html=True)

            if scored:
                st.markdown(
                    f'<div class="card" style="margin-top:0.5rem;">'
                    f'<h4 style="color:#f1f5f9;">📈 Resumen por categoría en el Top {len(scored)}</h4>',
                    unsafe_allow_html=True,
                )
                for cat_name, cat_color in [("caliente", "#ef4444"), ("posible", "#3b82f6"), ("ambos", "#fbbf24"), ("discriminante", "#22c55e")]:
                    count = sum(1 for s in scored if s.get("categoria") == cat_name)
                    if count:
                        pct = count / len(scored) * 100
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0.25rem 0;">'
                            f'<span style="width:0.8rem;height:0.8rem;background:{cat_color};border-radius:0.2rem;display:inline-block;"></span>'
                            f'<span style="color:#e2e8f0;min-width:6rem;">{_cat_labels.get(cat_name, cat_name.title())}</span>'
                            f'<div style="flex:1;background:#1e293b;height:0.5rem;border-radius:0.3rem;">'
                            f'<div style="background:{cat_color};width:{pct}%;height:100%;border-radius:0.3rem;"></div></div>'
                            f'<span style="color:#94a3b8;min-width:3rem;text-align:right;">{count} ({pct:.0f}%)</span>'
                            f'</div>', unsafe_allow_html=True,
                        )
                st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Tab 4: Charada Enriquecida ──────────────────────────────────
with tabs[4]:
    st.markdown(f'<div class="card"><h3>📖 Charada Enriquecida</h3>', unsafe_allow_html=True)

    query = st.text_input("🔍 Buscar por número (1-100) o palabra clave", placeholder="Ej: 15, perro, serpiente, río...", key="charada_unico")

    todas = api_get("/api/charada/enriquecida")

    q = query.strip()
    es_numero = q.isdigit() and 1 <= int(q) <= 100

    if es_numero:
        n = int(q)
        entry = next((e for e in (todas or []) if e["numero"] == n), None)
        if entry:
            st.markdown(f'<h2 style="color:#fbbf24;font-size:2.5rem;text-align:center;">{entry["numero"]:02d}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p style="text-align:center;color:#94a3b8;font-size:1.1rem;">Categoría: <strong style="color:#22c55e;">{entry["categoria"].title()}</strong></p>', unsafe_allow_html=True)
            st.markdown(f'<p style="text-align:center;color:#94a3b8;font-size:0.9rem;">Palabras clave: {", ".join(entry["palabras_clave"])}</p>', unsafe_allow_html=True)
            st.markdown('<h4 style="color:#f1f5f9;">Significados <span style="color:#94a3b8;font-weight:normal;font-size:0.9rem;">(' + str(len(entry["significados"])) + ')</span></h4>', unsafe_allow_html=True)
            sigs_html = '<div class="sig-flex">'
            for sig in entry["significados"]:
                sigs_html += f'<span>{sig}</span>'
            sigs_html += '</div>'
            st.markdown(sigs_html, unsafe_allow_html=True)
    elif q:
        q_lower = q.lower()
        filtered = [e for e in (todas or []) if q_lower in " ".join(e["significados"]).lower() or q_lower in str(e["numero"])]
        if filtered:
            st.markdown(f'<p style="color:#94a3b8;margin-bottom:0.5rem;">{len(filtered)} números encontrados con "<strong style="color:#fbbf24;">{q}</strong>"</p>', unsafe_allow_html=True)
            nums_html = '<div class="grid-num">'
            for e in filtered:
                nums_html += f'<a href="?charada_unico={e["numero"]}" style="text-decoration:none;"><span class="result-number" title="{e["significados"][0]}">{e["numero"]:02d}</span></a>'
            nums_html += '</div>'
            st.markdown(nums_html, unsafe_allow_html=True)
            with st.expander("📖 Ver detalles por número"):
                for e in filtered[:20]:
                    st.markdown(f'<div style="background:#334155;padding:0.5rem 1rem;border-radius:0.5rem;margin:0.25rem 0;border-left:3px solid #fbbf24;">'
                               f'<strong style="color:#fbbf24;font-size:1.1rem;">{e["numero"]:02d}</strong> → '
                               f'<span style="color:#e2e8f0;">{e["significados"][0]}</span>'
                               f' <span style="color:#64748b;font-size:0.85rem;">({e["categoria"]})</span></div>', unsafe_allow_html=True)
        else:
            st.warning(f"No se encontraron números con la palabra '{q}'.")
    else:
        if todas:
            st.info("Escribe un número (1-100) o una palabra para buscar en la Charada.")

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
