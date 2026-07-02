import streamlit as st
import httpx
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Adivinanzas - SueñaLotto", page_icon="🧠", layout="wide")

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
    .card h3 { color: #f1f5f9; }
    .riddle-box { background: linear-gradient(135deg, #1e3a5f, #2d1b4e); border: 1px solid #4a3f6b; border-radius: 0.75rem; padding: 1.5rem; margin: 1rem 0; text-align: center; }
    .riddle-text { font-size: 1.3rem; color: #fbbf24; font-style: italic; line-height: 1.6; }
    .ia-number { display: inline-block; background: linear-gradient(135deg, #22c55e, #16a34a); color: white; font-weight: bold;
                  font-size: 1.8rem; width: 3.5rem; height: 3.5rem; text-align: center; line-height: 3.5rem; border-radius: 0.5rem; margin: 0.25rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="color:#fbbf24;text-align:center;">🧠 Adivinanzas con IA</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#94a3b8;text-align:center;">Interpreta la adivinanza del día con ayuda de inteligencia artificial</p>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def api_get(path, params=None):
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return None

def api_post_json(path, json_data=None):
    try:
        r = httpx.post(f"{API_URL}{path}", json=json_data if json_data else {}, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return None


adivinanza_hoy = api_get("/api/adivinanza/hoy")

with st.container():
    st.markdown('<div class="card"><h3>📜 Adivinanza del Día</h3>', unsafe_allow_html=True)

    if adivinanza_hoy and adivinanza_hoy.get("texto") and "no hay adivinanza" not in adivinanza_hoy["texto"].lower():
        st.markdown(
            f'<div class="riddle-box">'
            f'<p style="color:#94a3b8;font-size:0.9rem;">{adivinanza_hoy["fecha"]}</p>'
            f'<p class="riddle-text">"{adivinanza_hoy["texto"]}"</p>'
            f'</div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="riddle-box">'
            '<p style="color:#94a3b8;">Hoy no hay adivinanza disponible en la base de datos.</p>'
            '<p style="color:#64748b;font-size:0.9rem;margin-top:0.5rem;">'
            "Pero puedes escribir tu propia adivinanza o la que hayas escuchado hoy.</p>"
            '</div>', unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)


st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<h3>💭 Interpretación</h3>', unsafe_allow_html=True)

adivinanza_input = st.text_area(
    "Adivinanza (si no está cargada arriba, escríbela aquí):",
    value=adivinanza_hoy.get("texto", "") if adivinanza_hoy and "no hay adivinanza" not in adivinanza_hoy.get("texto", "").lower() else "",
    height=80,
    placeholder="Ej: Agua que no has de beber, déjala correr. ¿Qué número soy?",
    key="adiv_texto",
)

interpretacion = st.text_area(
    "¿Qué crees que significa? Escribe tu interpretación:",
    height=100,
    placeholder="Ej: El agua siempre se asocia con el 7 en la charada, pero también podría ser el río que es 21...",
    key="adiv_interp",
)

col_btn, col_note = st.columns([1, 3])
with col_btn:
    analizar = st.button("🤖 Analizar con IA", type="primary", width='stretch')
with col_note:
    ia_status = api_get("/api/ia/status")
    if ia_status:
        gemini_ok = ia_status.get("gemini_disponible", False)
        if gemini_ok:
            badge = '<span style="background:#22c55e;color:white;padding:0.1rem 0.5rem;border-radius:0.25rem;font-size:0.7rem;">Gemini activo</span>'
        else:
            badge = '<span style="background:#f59e0b;color:white;padding:0.1rem 0.5rem;border-radius:0.25rem;font-size:0.7rem;">Análisis local</span>'
    else:
        badge = '<span style="background:#ef4444;color:white;padding:0.1rem 0.5rem;border-radius:0.25rem;font-size:0.7rem;">Sin conexión</span>'
    st.markdown(
        f'<span style="color:#64748b;font-size:0.85rem;">{badge} La IA analizará la adivinanza y tu interpretación '
        'para sugerir números basados en la tabla de sueños.</span>',
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

if analizar:
    if not adivinanza_input.strip() or not interpretacion.strip():
        st.warning("Por favor, completa tanto la adivinanza como tu interpretación.")
    else:
        with st.spinner("🤖 La IA está analizando la adivinanza..."):
            result = api_post_json(
                "/api/adivinanza/analizar",
                {"adivinanza": adivinanza_input, "interpretacion": interpretacion},
            )
        
        if result and result.get("sugerencias"):
            sugerencias = result["sugerencias"]
            razonamiento = result.get("razonamiento", "")
            
            st.markdown(
                '<div class="card" style="border: 1px solid #22c55e;">'
                '<h3 style="color:#22c55e;">✅ Resultado del Análisis</h3>',
                unsafe_allow_html=True,
            )
            
            st.markdown('<h4 style="color:#f1f5f9;">Números Sugeridos</h4>', unsafe_allow_html=True)
            nums_html = ""
            for s in sugerencias:
                nums_html += f'<span class="ia-number">{s["numero"]}</span>'
            st.markdown(f'<div style="text-align:center;padding:1rem;">{nums_html}</div>', unsafe_allow_html=True)
            
            st.markdown('<h4 style="color:#94a3b8;margin-top:1rem;">Razonamiento</h4>', unsafe_allow_html=True)
            for s in sugerencias:
                st.markdown(
                    f'<div style="background:#334155;border-radius:0.5rem;padding:0.5rem 1rem;margin:0.25rem 0;">'
                    f'<strong style="color:#fbbf24;">Número {s["numero"]}:</strong> '
                    f'<span style="color:#94a3b8;">{s["razon"]}</span>'
                    f'</div>', unsafe_allow_html=True
                )
            
            if razonamiento:
                st.markdown("---")
                st.markdown(
                    f'<div style="background:#1e3a5f;border-radius:0.5rem;padding:1rem;border-left:3px solid #3b82f6;">'
                    f'<p style="color:#cbd5e1;font-style:italic;">{razonamiento}</p>'
                    f'</div>', unsafe_allow_html=True
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("⏳ Cargando datos desde la IA...")

st.markdown("""
<div style="text-align:center;padding:2rem;">
    <p style="color:#475569;font-size:0.8rem;">
        💡 Consejo: Sé descriptivo en tu interpretación. La IA funciona mejor cuando le das contexto detallado.
    </p>
</div>
""", unsafe_allow_html=True)
