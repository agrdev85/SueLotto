import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.shared import api_get

st.set_page_config(page_title="Pago Exitoso - SueñaLotto", page_icon="✅", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 550px; margin: auto; padding-top: 3rem; }
    .success-card {
        background: linear-gradient(135deg, #064e3b, #065f46);
        border: 1px solid #10b981;
        border-radius: 1rem;
        padding: 2.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .success-card h1 { color: #34d399; margin: 0 0 0.5rem; }
    .success-card p { color: #a7f3d0; font-size: 1.1rem; }
    .plan-badge {
        display: inline-block;
        background: rgba(251,191,36,0.15);
        border: 1px solid rgba(251,191,36,0.4);
        color: #fbbf24;
        padding: 0.4rem 1.2rem;
        border-radius: 2rem;
        font-weight: 700;
        font-size: 1rem;
        margin: 1rem 0;
    }
    .feature-list { text-align: left; margin: 1.5rem 0; }
    .feature-list p { color: #94a3b8; font-size: 0.9rem; margin: 0.3rem 0; }
</style>
""", unsafe_allow_html=True)

params = st.query_params
plan = params.get("plan", "")

plan_names = {
    "pro": "Pro Mensual",
    "lifetime": "De por Vida",
}
plan_name = plan_names.get(plan, plan)

st.markdown(f"""
<div class="success-card">
    <h1>Pago Confirmado</h1>
    <p>Tu plan ha sido activado correctamente</p>
    <div class="plan-badge">{plan_name}</div>
</div>
""", unsafe_allow_html=True)

if plan == "pro":
    st.markdown("""
    <div class="feature-list">
        <p>✅ Búsquedas históricas ilimitadas</p>
        <p>✅ Búsqueda de sueños ilimitada</p>
        <p>✅ Adivinanzas con IA diarias</p>
        <p>✅ Matriz Charada completa</p>
        <p>✅ Estadísticas avanzadas</p>
        <p>✅ Números calientes y atrasados</p>
        <p>✅ Predicciones inteligentes</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("Tu plan vence en 30 días. Recibirás un email de recordatorio 5 días antes del vencimiento.")
elif plan == "lifetime":
    st.markdown("""
    <div class="feature-list">
        <p>✅ Todo lo del plan Pro, de por vida</p>
        <p>✅ Sin renovaciones ni mensualidades</p>
        <p>✅ Acceso a todas las funciones actuales y futuras</p>
        <p>✅ Soporte prioritario</p>
    </div>
    """, unsafe_allow_html=True)
    st.success("Tu acceso es permanente. No necesitas renovar nada.")
else:
    st.info("Tu pago ha sido procesado. El plan se activará automáticamente.")

st.markdown("---")
if st.button("Ir a SueñaLotto", type="primary", use_container_width=True):
    st.switch_page("dashboard.py")
