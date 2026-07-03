import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Búsqueda Histórica - SueñaLotto", page_icon="🔎", layout="wide")

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
if not _t or _t.get("tier") not in ("free", "trial", "pro", "lifetime"):
    st.stop()

tier_name = _t.get("tier", "free")
historica_today = _t.get("historica_today", 0)
historica_limit = _t.get("historica_limit", 3)
is_free = tier_name in ("free", "trial")

st.markdown("""
<style>
    .stAppDeployButton, .stMainMenu, #MainMenu, footer { display: none !important; visibility: hidden !important; }
    header[data-testid="stHeader"] { background: rgba(15, 23, 42, 0.95) !important; backdrop-filter: blur(12px); border-bottom: 1px solid rgba(251, 191, 36, 0.15); }
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; }
    .card h3 { color: #f1f5f9; }
    .result-number-sm { display: inline-block; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; font-weight: bold; 
                        font-size: 1rem; width: 2rem; height: 2rem; text-align: center; line-height: 2rem; border-radius: 0.3rem; margin: 0 0.1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="color:#fbbf24;text-align:center;">🔍 Buscador Histórico Inteligente</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#94a3b8;text-align:center;">Busca resultados históricos con filtros combinados</p>', unsafe_allow_html=True)

if is_free and historica_limit < 999:
    remaining = historica_limit - historica_today
    if remaining <= 0:
        st.error("🚫 Has alcanzado el límite diario de 3 búsquedas históricas. Actualiza a **Pro** para búsquedas ilimitadas.")
    else:
        st.info(f"💡 Te quedan **{remaining}** de **{historica_limit}** búsquedas históricas hoy. Actualiza a Pro para búsquedas ilimitadas.")

@st.cache_data(ttl=60)
def api_get(path, params=None):
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, headers=headers, timeout=30)
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
        r = httpx.post(f"{API_URL}{path}", json=json_data, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None

with st.container():
    st.markdown('<div class="card"><h3>🔧 Filtros de Búsqueda</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        juego = st.selectbox("Juego", ["Todos", "Pick 3", "Pick 4"], key="hist_juego")
        juego_param = juego if juego != "Todos" else None
    
    with col2:
        sorteo = st.selectbox("Sorteo", ["Todos", "E (Evening)", "M (Midday)"], key="hist_sorteo")
        sorteo_param = sorteo[0] if sorteo != "Todos" else None
    
    with col3:
        contienen = st.text_input("Contiene dígitos", placeholder="Ej: 1,7", key="hist_digitos")
        contienen_param = contienen if contienen.strip() else None
    
    min_year = 2008 if is_free else 1988
    col4, col5 = st.columns(2)
    with col4:
        fecha_inicio = st.date_input("Desde", value=date(min_year, 1, 1),
                                     min_value=date(min_year, 1, 1),
                                     max_value=date.today(), key="hist_fecha_ini")
    with col5:
        fecha_fin = st.date_input("Hasta", value=date.today(),
                                  min_value=date(min_year, 1, 1),
                                  max_value=date.today(), key="hist_fecha_fin")
    
    st.session_state.setdefault("hist_page", 1)
    st.session_state.setdefault("hist_page_size", 100)

    col_page_opts = st.columns([1, 1])
    with col_page_opts[0]:
        page_size_opt = st.selectbox("Registros por página", [25, 50, 100, 200, 500], index=2, key="hist_page_size_sel")
        st.session_state["hist_page_size"] = page_size_opt
    with col_page_opts[1]:
        st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)

    buscar = st.button("🔍 Buscar", type="primary", width='stretch')
    st.markdown('</div>', unsafe_allow_html=True)

PAGE_SIZE_DEFAULT = 100

def load_page(page):
    sz = st.session_state.get("hist_page_size", PAGE_SIZE_DEFAULT)
    params = {
        "juego": juego_param,
        "sorteo": sorteo_param,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "contienen_digitos": contienen_param,
        "page": page,
        "size": sz,
    }
    params = {k: v for k, v in params.items() if v is not None}
    return api_get("/api/resultados/historicos", params)

if buscar or "hist_resultados" in st.session_state:
    if buscar:
        if is_free and historica_today >= historica_limit:
            st.error("🚫 Límite diario de búsquedas históricas alcanzado (3/día). Actualiza a Pro para ilimitadas.")
        else:
            st.session_state["hist_page"] = 1
            with st.spinner("Buscando resultados..."):
                result = load_page(1)
                if is_free:
                    api_post("/api/usage/historica", {})
                st.session_state["hist_resultados"] = result

    result = st.session_state.get("hist_resultados")
    page = st.session_state.get("hist_page", 1)

    if result and result.get("data"):
        data = result["data"]
        total = result["total"]

        st.markdown(
            f'<div class="card"><h3>📋 Resultados: {total} encontrados (página {page})</h3>',
            unsafe_allow_html=True,
        )

        rows = []
        for r in data:
            nums = f"{r['n1']}-{r['n2']}-{r['n3']}"
            if r.get("n4") is not None:
                nums += f"-{r['n4']}"
            sorteo_str = "Evening 🌙" if r["sorteo"] == "E" else "Midday ☀️"
            rows.append({
                "Fecha": r["fecha"],
                "Juego": r["juego"],
                "Sorteo": sorteo_str,
                "Números": nums,
            })

        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            width='stretch',
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha", format="YYYY-MM-DD"),
                "Números": st.column_config.TextColumn("Números", width="medium"),
            },
        )

        sz = st.session_state.get("hist_page_size", PAGE_SIZE_DEFAULT)
        total_pages = max(1, (total + sz - 1) // sz)

        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        with col_nav1:
            if page > 1 and st.button("⬅ Anterior", key="btn_prev", width='stretch'):
                st.session_state["hist_page"] = page - 1
                if "hist_goto" in st.session_state:
                    del st.session_state["hist_goto"]
                new_result = load_page(page - 1)
                if new_result:
                    st.session_state["hist_resultados"] = new_result
                st.rerun()
        with col_nav2:
            st.markdown(f'<p style="text-align:center;color:#94a3b8;margin-top:0.5rem;">Página <strong style="color:#f1f5f9;">{page}</strong> de {total_pages}</p>', unsafe_allow_html=True)
            goto_page = st.number_input("Ir a página", min_value=1, max_value=total_pages, value=page, key="hist_goto", label_visibility="collapsed")
            if goto_page != page:
                st.session_state["hist_page"] = goto_page
                new_result = load_page(goto_page)
                if new_result:
                    st.session_state["hist_resultados"] = new_result
                st.rerun()
        with col_nav3:
            if page < total_pages and st.button("Siguiente ➡", key="btn_next", width='stretch'):
                st.session_state["hist_page"] = page + 1
                if "hist_goto" in st.session_state:
                    del st.session_state["hist_goto"]
                new_result = load_page(page + 1)
                if new_result:
                    st.session_state["hist_resultados"] = new_result
                st.rerun()

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Exportar CSV",
            csv,
            f"resultados_{fecha_inicio}_{fecha_fin}.csv",
            "text/csv",
            key="download-csv",
        )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><h3>📊 Resumen Rápido</h3>', unsafe_allow_html=True)
        col_s1, col_s2, col_s3 = st.columns(3)

        pair_counter = {}
        for r in data:
            par = r["n2"] * 10 + r["n3"]
            pair_counter[par] = pair_counter.get(par, 0) + 1
            if r.get("n4") is not None:
                par2 = r["n3"] * 10 + r["n4"]
                pair_counter[par2] = pair_counter.get(par2, 0) + 1

        with col_s1:
            st.metric("Total sorteos", len(data))
        with col_s2:
            if pair_counter:
                top_pair, top_count = max(pair_counter.items(), key=lambda x: x[1])
                st.metric("Par más frecuente", f"{top_pair:02d}", f"{top_count} veces")
        with col_s3:
            if pair_counter:
                st.metric("Pares distintos", len(pair_counter))

        st.markdown('<h4 style="color:#94a3b8;">Distribución de pares (corridos) en este período</h4>', unsafe_allow_html=True)

        top_pairs = sorted(pair_counter.items(), key=lambda x: x[1], reverse=True)[:20]
        if top_pairs:
            pair_cols = st.columns(min(10, len(top_pairs)))
            for i, (par, count) in enumerate(top_pairs[:10]):
                max_count = top_pairs[0][1] if top_pairs else 1
                height = max(20, (count / max_count) * 100)
                is_decena = par % 10 == 0
                color = "#fbbf24" if is_decena else ("#ef4444" if count > max_count * 0.7 else "#3b82f6")
                with pair_cols[i]:
                    st.markdown(
                        f'<div style="text-align:center;">'
                        f'<div style="background:{color};height:{height}px;width:100%;border-radius:0.3rem;min-height:20px;"></div>'
                        f'<div style="color:#f1f5f9;font-weight:bold;margin-top:0.3rem;">{par:02d}</div>'
                        f'<div style="color:#94a3b8;font-size:0.8rem;">{count}</div>'
                        f'</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="color:#64748b;font-size:0.8rem;">Mostrando top 10 de {len(top_pairs)} pares distintos. 🟡 Decenas completas · 🔴 Muy frecuente · 🔵 Frecuente</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No se encontraron resultados con los filtros seleccionados.")
