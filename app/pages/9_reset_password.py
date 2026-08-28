import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.shared import api_post

st.set_page_config(page_title="Restablecer Contraseña - SueñaLotto", page_icon="🔐", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 500px; margin: auto; padding-top: 2rem; }
    .stForm { background: var(--bg-card, #1e293b); border-radius: 1rem; padding: 1.5rem; border: 1px solid var(--border-color, #334155); }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>🔐 Restablecer Contraseña</h1>", unsafe_allow_html=True)

params = st.query_params
token = params.get("token", "")

if not token:
    st.error("Enlace inválido o expirado. Solicita uno nuevo desde la pantalla de inicio de sesión.")
    st.markdown("[← Volver al inicio](/)")
    st.stop()

with st.form("reset_form"):
    new_pass = st.text_input("Nueva contraseña", type="password", placeholder="Mínimo 8 caracteres")
    confirm_pass = st.text_input("Confirmar contraseña", type="password", placeholder="Repite la contraseña")
    if st.form_submit_button("Cambiar contraseña", type="primary", use_container_width=True):
        if not new_pass or not confirm_pass:
            st.error("Ambos campos son requeridos.")
        elif new_pass != confirm_pass:
            st.error("Las contraseñas no coinciden.")
        elif len(new_pass) < 8:
            st.error("La contraseña debe tener al menos 8 caracteres.")
        else:
            resp = api_post("/api/auth/reset-password", {"token": token, "password": new_pass})
            if resp and resp.get("status") == "ok":
                st.success("Contraseña actualizada correctamente.")
                st.markdown("[← Iniciar sesión](/)")
            else:
                detail = st.session_state.get("last_api_error")
                st.error(f"Error: {detail}" if detail else "No se pudo actualizar la contraseña. El enlace puede haber expirado.")
