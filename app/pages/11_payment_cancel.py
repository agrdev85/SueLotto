import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Pago Cancelado - SueñaLotto", page_icon="❌", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 550px; margin: auto; padding-top: 3rem; }
    .cancel-card {
        background: linear-gradient(135deg, #451a03, #78350f);
        border: 1px solid #b45309;
        border-radius: 1rem;
        padding: 2.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .cancel-card h1 { color: #fbbf24; margin: 0 0 0.5rem; }
    .cancel-card p { color: #fde68a; font-size: 1.05rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="cancel-card">
    <h1>Pago Cancelado</h1>
    <p>No se realizó ningún cobro. Tu plan actual sigue activo.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("Si tuviste un problema con el pago, puedes:")
st.markdown("- Intentar de nuevo desde la sección de **Planes**")
st.markdown("- Contactar soporte si el problema persiste")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("Intentar de nuevo", type="primary", use_container_width=True):
        st.switch_page("dashboard.py")
with col2:
    if st.button("Contactar soporte", use_container_width=True):
        st.switch_page("pages/8_soporte.py")
