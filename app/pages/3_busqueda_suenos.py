import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Búsqueda de Sueños - SueñaLotto", page_icon="🌙", layout="wide")

st.markdown("""
<style>
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
st.markdown('<p style="color:#94a3b8;text-align:center;">Describe tu sueño y descubre los números de la Charada Cubana asociados</p>', unsafe_allow_html=True)

@st.cache_data(ttl=60)
def api_get(path, params=None):
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None

def api_post(path, json_data=None):
    try:
        r = httpx.post(f"{API_URL}{path}", json=json_data, timeout=15)
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
        buscar = st.button("🔍 Buscar en Charada", type="primary", use_container_width=True)

    with col_info:
        st.markdown(
            '<span style="color:#64748b;font-size:0.85rem;">La Charada Cubana asigna números a palabras clave. '
            'Escribe tu sueño y extraeremos los números asociados.</span>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

if buscar and texto_sueno.strip():
    with st.spinner("Analizando sueño..."):
        result = api_post("/api/charada/buscar", {"texto": texto_sueno})
    
    if result and result.get("resultados"):
        resultados = result["resultados"]
        
        st.markdown('<div class="card"><h3>🔢 Números Encontrados</h3>', unsafe_allow_html=True)
        
        nums_html = ""
        for r in resultados:
            nums_html += f'<span class="dream-number">{r["numero"]:02d}</span>'
        n = len(resultados)
        
        if n > 0:
            st.markdown(
                f'<div style="text-align:center;padding:1rem;">{nums_html}</div>',
                unsafe_allow_html=True,
            )
        
        st.markdown('<h4 style="color:#94a3b8;margin-top:1rem;">Combinaciones Sugeridas</h4>', unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown('<div class="meaning-box" style="border-left: 3px solid #fbbf24;">', unsafe_allow_html=True)
            numeros_orden = [str(r["numero"] % 10) for r in resultados]
            if len(numeros_orden) >= 3:
                pick3 = "".join(numeros_orden[:3])
                st.markdown(f'<strong>Pick 3 sugerido:</strong> <span style="color:#fbbf24;font-size:1.5rem;">{pick3[0]}-{pick3[1]}-{pick3[2]}</span>', unsafe_allow_html=True)
            if len(numeros_orden) >= 4:
                pick4 = "".join(numeros_orden[:4])
                st.markdown(f'<strong>Pick 4 sugerido:</strong> <span style="color:#22c55e;font-size:1.5rem;">{pick4[0]}-{pick4[1]}-{pick4[2]}-{pick4[3]}</span>', unsafe_allow_html=True)
            elif len(numeros_orden) == 3:
                st.markdown(f'<strong>Pick 4 sugerido:</strong> <span style="color:#22c55e;font-size:1.5rem;">{numeros_orden[0]}-{numeros_orden[1]}-{numeros_orden[2]}-{numeros_orden[0]}</span>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_c2:
            if len(resultados) >= 3:
                freq_nums = [r["numero"] % 10 for r in resultados]
                from collections import Counter
                top = Counter(freq_nums).most_common(3)
                if len(top) == 3:
                    st.markdown(f'<div class="meaning-box" style="border-left: 3px solid #22c55e;">', unsafe_allow_html=True)
                    st.markdown(f'<strong>Por frecuencia:</strong> <span style="color:#22c55e;font-size:1.5rem;">{top[0][0]}-{top[1][0]}-{top[2][0]}</span>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown('<h4 style="color:#94a3b8;">📖 Significados por orden de aparición</h4>', unsafe_allow_html=True)
        
        for i, r in enumerate(resultados):
            categoria_html = ""
            if r.get("categoria"):
                categoria_html = f'<span style="color:#94a3b8;font-size:0.85rem;">{r["categoria"]}</span>'
            st.markdown(
                f'<div class="meaning-box" style="display:flex;align-items:center;gap:1rem;">'
                f'<span style="background:#fbbf24;color:#0f172a;font-weight:bold;border-radius:50%;width:2rem;height:2rem;'
                f'text-align:center;line-height:2rem;">{r["numero"]:02d}</span>'
                f'<div><strong style="color:#f1f5f9;">{r["significado"]}</strong>'
                f' · {categoria_html}'
                f'</div>'
                f'</div>', unsafe_allow_html=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    else:
        st.warning("No se encontraron palabras de la Charada Cubana en tu sueño. Prueba con más detalles o palabras diferentes.")

elif buscar:
    st.warning("Por favor, escribe la descripción de tu sueño.")

with st.container():
    st.markdown('<div class="card"><h3>📚 Referencia Rápida de la Charada</h3>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.9rem;">Algunas palabras comunes y sus números en la Charada Cubana:</p>',
        unsafe_allow_html=True,
    )
    
    ref_data = [
        ("0", "Caballo", "8", "Viaje"),
        ("1", "Sol/Amor", "9", "Gallo"),
        ("2", "Luna/Casa", "10", "Casa"),
        ("3", "Fuego", "15", "Perro"),
        ("4", "Muerto/Muerte", "21", "Río"),
        ("5", "Dinero", "46", "Sueño"),
        ("6", "Tristeza", "57", "Ángel"),
        ("7", "Agua/Lluvia", "73", "Serpiente"),
    ]
    
    ref_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">'
    for num, sig in ref_data:
        ref_html += f'<div style="background:#334155;padding:0.3rem 0.8rem;border-radius:0.3rem;">' \
                    f'<span style="color:#fbbf24;font-weight:bold;">{num}</span> → {sig}</div>'
    ref_html += "</div>"
    st.markdown(ref_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
