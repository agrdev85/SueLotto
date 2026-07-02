import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Búsqueda de Sueños - SueñaLotto", page_icon="🌙", layout="wide")

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
    .dream-number { display: inline-block; background: linear-gradient(135deg, #f59e0b, #ef4444); color: white; font-weight: bold; 
                    font-size: 1.5rem; width: 3rem; height: 3rem; text-align: center; line-height: 3rem; border-radius: 0.5rem; margin: 0.25rem; }
    .highlight-word { background: #fbbf24; color: #0f172a; padding: 0.1rem 0.3rem; border-radius: 0.2rem; font-weight: bold; }
    .meaning-box { background: #334155; border-radius: 0.5rem; padding: 0.5rem 1rem; margin: 0.25rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="color:#fbbf24;text-align:center;">🌙 Búsqueda de Sueños</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#94a3b8;text-align:center;">Describe tu sueño y descubre los números asociados según la tabla de sueños</p>', unsafe_allow_html=True)

@st.cache_data(ttl=60)
def api_get(path, params=None):
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return None

def api_post(path, json_data=None):
    try:
        r = httpx.post(f"{API_URL}{path}", json=json_data, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3>📝 Describe tu sueño</h3>', unsafe_allow_html=True)

    texto_sueno = st.text_area(
        "Escribe tu sueño con el mayor detalle posible:",
        placeholder="Ejemplo: Soñé con un perro que corría detrás de un gallo cerca del río...",
        height=150,
        label_visibility="collapsed",
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        buscar = st.button("🔍 Buscar en Charada", type="primary", width='stretch')

    with col_info:
        st.markdown(
            '<span style="color:#64748b;font-size:0.85rem;">La tabla asigna números a palabras clave. '
            'Escribe tu sueño y extraeremos los números asociados.</span>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

if buscar and texto_sueno.strip():
    with st.spinner("Analizando sueño..."):
        result = api_post("/api/charada/buscar", {"texto": texto_sueno})
        freqs = api_get("/api/estadisticas/frecuencias", {"juego": "Pick 3", "dias": 90})
    
    if result and result.get("resultados"):
        resultados = result["resultados"]
        freq_map = {f["numero"]: f for f in freqs} if freqs else {}
        
        st.markdown('<div class="card"><h3>🔢 Números de tu Sueño</h3>', unsafe_allow_html=True)
        
        nums_html = ""
        for r in resultados:
            nums_html += f'<span class="dream-number">{r["numero"]:02d}</span>'
        st.markdown(
            f'<div style="text-align:center;padding:1rem 0;">{nums_html}</div>',
            unsafe_allow_html=True,
        )
        
        if freq_map:
            ranked = []
            for r in resultados:
                n = r["numero"]
                fdata = freq_map.get(n)
                rank = "🔴" if fdata and fdata["frecuencia"] > 5 else ("🟡" if fdata and fdata["frecuencia"] > 2 else "⚪")
                ranked.append((rank, n, fdata["frecuencia"] if fdata else 0, r["significado"]))
            ranked.sort(key=lambda x: x[2], reverse=True)
            
            st.markdown('<h4 style="color:#94a3b8;">📊 Más usados en sorteos reales (90 días)</h4>', unsafe_allow_html=True)
            for rank, n, freq, sig in ranked:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.2rem 0;border-bottom:1px solid #334155;">'
                    f'<span style="font-size:1.2rem;">{rank}</span>'
                    f'<span style="background:#fbbf24;color:#0f172a;font-weight:bold;border-radius:0.3rem;padding:0.1rem 0.5rem;">{n:02d}</span>'
                    f'<span style="color:#e2e8f0;flex:1;">{sig}</span>'
                    f'<span style="color:#94a3b8;">{freq} apariciones</span>'
                    f'</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown('<h4 style="color:#94a3b8;">📖 Significados en la Charada</h4>', unsafe_allow_html=True)
        
        for r in resultados:
            cat = f' · <span style="color:#94a3b8;font-size:0.85rem;">{r.get("categoria", "")}</span>' if r.get("categoria") else ""
            st.markdown(
                f'<div style="background:#334155;border-radius:0.5rem;padding:0.4rem 1rem;margin:0.2rem 0;display:flex;align-items:center;gap:1rem;">'
                f'<span style="background:#fbbf24;color:#0f172a;font-weight:bold;border-radius:0.3rem;padding:0.1rem 0.5rem;">{r["numero"]:02d}</span>'
                f'<span style="color:#f1f5f9;">{r["significado"]}</span>{cat}'
                f'</div>', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    else:
        st.warning("No se encontraron palabras conocidas en tu sueño. Prueba con más detalles o palabras diferentes.")

elif buscar:
    st.warning("Por favor, escribe la descripción de tu sueño.")

with st.container():
    st.markdown('<div class="card"><h3>📚 Referencia Rápida de la Charada</h3>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.9rem;">Algunas palabras comunes y sus números asociados:</p>',
        unsafe_allow_html=True,
    )
    
    ref_data = [
        ("1", "Caballo"), ("15", "Perro"),
        ("2", "Mariposa"), ("21", "Maja"),
        ("3", "Marinero"), ("46", "Guagua"),
        ("4", "Gato Boca"), ("73", "Serpiente"),
        ("5", "Monja"), ("75", "Cinematógrafo / Perro mediano"),
        ("6", "Jicotea"), ("85", "Casa"),
        ("7", "Caracol"), ("95", "Guerra del mar / Perro grande"),
        ("8", "Viaje"), ("100", "Pescado"),
        ("9", "Elefante"), ("0", "Buzo"),
        ("10", "Pescado Grande"),
    ]
    
    ref_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">'
    for num, sig in ref_data:
        ref_html += f'<div style="background:#334155;padding:0.3rem 0.8rem;border-radius:0.3rem;">' \
                    f'<span style="color:#fbbf24;font-weight:bold;">{num}</span> → {sig}</div>'
    ref_html += "</div>"
    st.markdown(ref_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
