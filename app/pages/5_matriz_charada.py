import streamlit as st
import httpx
import os
import re as re_mod
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Matriz & Charada", page_icon="🔢", layout="wide")

# Inline tier check
def _check_tier():
    token = st.session_state.get("token")
    if not token:
        st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">Acceso Restringido</h2><p style="color:#94a3b8;">Necesitas iniciar sesión.</p><p style="color:#64748b;font-size:0.85rem;">💎 Suscríbete a <strong style="color:#fbbf24;">Pro</strong> para acceder.</p></div>', unsafe_allow_html=True)
        st.stop()
        return {}
    try:
        r = httpx.get(f"{API_URL}/api/auth/tier", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if r.status_code != 200:
            st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">Error de autenticación</h2><p style="color:#94a3b8;">Vuelve a iniciar sesión.</p></div>', unsafe_allow_html=True)
            st.stop()
            return {}
        return r.json()
    except Exception:
        st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">No se pudo verificar suscripción</h2><p style="color:#94a3b8;">¿Está el backend encendido?</p></div>', unsafe_allow_html=True)
        st.stop()
        return {}

_t = _check_tier()
if _t.get("tier") not in ("pro", "lifetime"):
    st.stop()

st.markdown("""
<style>
    .stAppDeployButton, .stMainMenu, #MainMenu, footer { display: none !important; visibility: hidden !important; }
    header[data-testid="stHeader"] { background: rgba(15, 23, 42, 0.95) !important; backdrop-filter: blur(12px); border-bottom: 1px solid rgba(251, 191, 36, 0.15); }
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
    .sig-flex { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .sig-flex > span { background: #334155; border: 1px solid #475569; border-radius: 0.4rem; padding: 0.3rem 0.7rem; color: #e2e8f0; font-size: 0.85rem; white-space: nowrap; }
    .grid-num { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .grid-num > a { text-decoration: none; }
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
    cols_labels = [chr(ord('a') + i) for i in range(len(matriz_actual[0]))]

    # Build self-contained matrix component using st.components.v1.html
    # so clicks update the Alrededor card inline without page reload
    import json as _json

    _sel = st.session_state.get("matriz_sel")

    _rows_html = ""
    _rows_html += '<tr><td style="width:1.2rem;"></td>'
    for c_label in cols_labels:
        _rows_html += f'<td style="text-align:center;color:#64748b;font-size:0.7rem;padding:2px 1px;">{c_label.upper()}</td>'
    _rows_html += '</tr>'

    for i, row in enumerate(matriz_actual):
        _rows_html += f'<tr><td style="text-align:center;color:#64748b;font-size:0.65rem;">{i+1}</td>'
        for j, val in enumerate(row):
            if val == 0:
                _rows_html += '<td style="background:#0f172a;color:#475569;padding:6px 2px;text-align:center;border-radius:4px;font-size:0.85rem;"></td>'
            else:
                _cls = "mc-cell"
                if val == _sel:
                    _cls += " mc-sel"
                if val in set_ambos:
                    _cls += " mc-ambos"
                elif val in set_calientes:
                    _cls += " mc-caliente"
                elif val in set_posibles:
                    _cls += " mc-posible"
                _rows_html += f'<td class="{_cls}" data-r="{i}" data-c="{j}" data-val="{val}">{val}</td>'
        _rows_html += '</tr>'

    _matriz_json = _json.dumps(matriz_actual)
    _calientes_json = _json.dumps(list(set_calientes))
    _posibles_json = _json.dumps(list(set_posibles))
    _api_url_json = _json.dumps(API_URL)

    matrix_html = f"""<div style="overflow-x:auto;">
<style>
  #mc-app {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
  #mc-app table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
  #mc-app td {{ width: 9%; aspect-ratio: 1 / 1; text-align: center; border-radius: 6px; font-weight: bold; font-size: clamp(0.65rem, 2vw, 0.95rem); cursor: default; vertical-align: middle; }}
  #mc-app tr td:first-child {{ width: 1.5rem; aspect-ratio: auto; font-size: 0.6rem; color: #64748b; background: transparent !important; }}
  .mc-cell {{ background: #1e293b; color: white; cursor: pointer !important; transition: opacity 0.15s, transform 0.1s; }}
  .mc-cell:hover {{ opacity: 0.8; transform: scale(1.06); }}
  .mc-sel {{ background: linear-gradient(135deg,#3b82f6,#8b5cf6) !important; box-shadow: 0 0 8px rgba(59,130,246,0.5); }}
  .mc-caliente {{ background: #ef4444 !important; }}
  .mc-posible {{ background: #3b82f6 !important; }}
  .mc-ambos {{ background: #fbbf24 !important; color: #0f172a !important; }}
  .mc-empty {{ background: #0f172a; color: #475569; }}
  #mc-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; display: none; }}
  #mc-card .mc-num {{ display: inline-flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg,#3b82f6,#8b5cf6); color: white; font-weight: bold;
    font-size: clamp(0.8rem, 1.5vw, 0.95rem); width: 2.2rem; height: 2.2rem; border-radius: 0.4rem; margin: 0.15rem; }}
  #mc-card .mc-row {{ display: flex; gap: 0.3rem; margin-bottom: 0.3rem; flex-wrap: wrap; }}
  .mc-spinner {{ display: inline-block; width: 1rem; height: 1rem; border: 2px solid #334155; border-top-color: #fbbf24; border-radius: 50%; animation: mc-spin 0.6s linear infinite; }}
  @keyframes mc-spin {{ to {{ transform: rotate(360deg); }} }}
</style>
<div id="mc-app">
<table>{_rows_html}</table>
<div id="mc-card">
  <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;">
    <span id="mc-card-num" style="font-size:2rem;font-weight:bold;color:#fbbf24;"></span>
    <span id="mc-card-label" style="color:#94a3b8;font-size:0.95rem;"></span>
  </div>
  <div id="mc-card-body"></div>
</div>
<div id="mc-error" style="color:#ef4444;margin-top:0.5rem;display:none;"></div>
</div>
<script>
(function() {{
  const MATRIZ = {_matriz_json};
  const CALIENTES = new Set({_calientes_json});
  const POSIBLES = new Set({_posibles_json});
  const API = {_api_url_json};
  const selVal = {_json.dumps(_sel)};

  function highlightCell(el) {{
    document.querySelectorAll('.mc-sel').forEach(c => c.classList.remove('mc-sel'));
    if (el) el.classList.add('mc-sel');
  }}

  function showError(msg) {{
    const err = document.getElementById('mc-error');
    err.textContent = msg;
    err.style.display = 'block';
  }}

  function showCard(num, total, numeros) {{
    const card = document.getElementById('mc-card');
    document.getElementById('mc-card-num').textContent = num;
    document.getElementById('mc-card-label').innerHTML = 'Números alrededor · <strong style="color:#f1f5f9;">' + total + '</strong>';
    const body = document.getElementById('mc-card-body');
    body.innerHTML = '';
    for (let i = 0; i < numeros.length; i += 10) {{
      const row = document.createElement('div');
      row.className = 'mc-row';
      const chunk = numeros.slice(i, i + 10);
      chunk.forEach(n => {{
        const span = document.createElement('span');
        span.className = 'mc-num';
        span.textContent = n;
        row.appendChild(span);
      }});
      body.appendChild(row);
    }}
    card.style.display = 'block';
    document.getElementById('mc-error').style.display = 'none';
  }}

  function clickCell(el) {{
    const r = parseInt(el.dataset.r);
    const c = parseInt(el.dataset.c);
    const val = parseInt(el.dataset.val);
    if (!val) return;
    highlightCell(el);
    const card = document.getElementById('mc-card');
    card.style.display = 'none';
    document.getElementById('mc-error').style.display = 'none';
    const body = document.getElementById('mc-card-body');
    body.innerHTML = '<div class="mc-spinner"></div> <span style="color:#94a3b8;margin-left:0.5rem;">Cargando...</span>';
    card.style.display = 'block';
    try {{
      Streamlit.setComponentValue(JSON.stringify({{selected: val}}));
    }} catch(e) {{}}
    fetch(API + '/api/matriz/alrededor', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{numero: val, tipo_matriz: '{tipo_matriz}'}})
    }})
    .then(r => {{
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }})
    .then(data => showCard(val, data.total, data.numeros))
    .catch(err => {{
      body.innerHTML = '';
      showError('Error al cargar: ' + err.message);
    }});
  }}

  document.querySelectorAll('.mc-cell').forEach(el => {{
    el.addEventListener('click', function() {{ clickCell(this); }});
  }});

  if (selVal) {{
    const el = document.querySelector('.mc-cell[data-val="' + selVal + '"]');
    if (el) {{
      highlightCell(el);
      fetch(API + '/api/matriz/alrededor', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{numero: selVal, tipo_matriz: '{tipo_matriz}'}})
      }})
      .then(r => r.json())
      .then(data => showCard(selVal, data.total, data.numeros))
      .catch(err => showError('Error: ' + err.message));
    }}
  }}
}})();
</script>
</div>"""

    comp_val = st.components.v1.html(matrix_html, height=620, scrolling=True)
    if comp_val:
        try:
            parsed = _json.loads(comp_val)
            if "selected" in parsed:
                st.session_state.matriz_sel = parsed["selected"]
        except (ValueError, TypeError):
            pass

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

            st.markdown(f'<div class="card"><h4>🟢 Discriminante ({resp["total_discriminante"]}) · <span style="color:#94a3b8;font-size:0.85rem;">Alrededor − Calientes − Posibles</span></h4>', unsafe_allow_html=True)
            if resp["discriminante"]:
                numeros_html = "".join(f'<span class="result-number">{x}</span>' for x in resp["discriminante"])
                st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)

                scored = resp.get("discriminante_scored", [])
                if scored:
                    st.markdown(f'<h4 style="color:#fbbf24;margin-top:1rem;">🏆 Top {len(scored)} — Score Estadístico</h4>', unsafe_allow_html=True)
                    st.markdown(
                        '<p style="color:#94a3b8;font-size:0.85rem;">'
                        'Combinando frecuencia (90 días), atraso y probabilidad ML. '
                        'Se eliminan números sin frecuencia y >365 días sin salir.</p>',
                        unsafe_allow_html=True,
                    )
                    for i, s in enumerate(scored):
                        bar_w = max(int(s["score"] * 100), 5)
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.3rem 0;border-bottom:1px solid #334155;">'
                            f'<span style="color:#64748b;min-width:1.5rem;">#{i+1}</span>'
                            f'<span style="background:#fbbf24;color:#0f172a;font-weight:bold;border-radius:0.3rem;padding:0.1rem 0.5rem;min-width:2.5rem;text-align:center;">{s["numero"]:02d}</span>'
                            f'<div style="flex:1;background:#334155;height:0.5rem;border-radius:0.25rem;">'
                            f'<div style="background:linear-gradient(90deg,#22c55e,#fbbf24);width:{bar_w}%;height:100%;border-radius:0.25rem;"></div></div>'
                            f'<span style="color:#94a3b8;font-size:0.8rem;min-width:3rem;">{s["frecuencia"]}×</span>'
                            f'<span style="color:#94a3b8;font-size:0.8rem;min-width:3rem;">{s["dias_sin_salir"]}d</span>'
                            f'<span style="color:#22c55e;font-size:0.8rem;min-width:2.5rem;">{s["probabilidad_ml"]:.1%}</span>'
                            f'</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p style="color:#22c55e;font-size:0.85rem;margin-top:0.5rem;">💡 Recomendación: Estos números están en la matriz pero NO son calientes ni posibles. Podrían ser su mejor oportunidad.</p>', unsafe_allow_html=True)
            else:
                st.info("No hay números discriminantes.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Tab 3: Charada Enriquecida ──────────────────────────────────
with tabs[3]:
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
