import streamlit as st
import os
import sys
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="SueñaLotto",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.shared import init_session_state

init_session_state()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

st.markdown("""
<style>
    [data-testid="stSidebar"] a[href*="10_payment_success"],
    [data-testid="stSidebar"] a[href*="11_payment_cancel"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)


def _page(*rel: str):
    return os.path.join(ROOT, "app", *rel)


user = st.session_state.get("user")
is_admin = bool(user and user.get("tier") == "admin")

nav_pages = [
    st.Page(_page("dashboard.py"), title="Sorteos", icon="🎱", default=True),
    st.Page(_page("pages", "1_mis_jugadas.py"), title="Mis Jugadas", icon="🎲"),
    st.Page(_page("pages", "2_estadisticas.py"), title="Estadísticas", icon="📈"),
    st.Page(_page("pages", "3_busqueda_historica.py"), title="Búsqueda Histórica", icon="🔎"),
    st.Page(_page("pages", "4_busqueda_suenos.py"), title="Búsqueda de Sueños", icon="💭"),
    st.Page(_page("pages", "5_adivinanzas.py"), title="Adivinanzas", icon="🪄"),
    st.Page(_page("pages", "6_matriz_charada.py"), title="Matriz Charada", icon="🧮"),
    st.Page(_page("pages", "8_soporte.py"), title="Soporte", icon="🛟"),
    st.Page(_page("pages", "9_reset_password.py"), title="Restablecer Contraseña", icon="🔐"),
    st.Page(_page("pages", "10_payment_success.py"), title="Pago Exitoso", icon="✅", url_path="10_payment_success"),
    st.Page(_page("pages", "11_payment_cancel.py"), title="Pago Cancelado", icon="❌", url_path="11_payment_cancel"),
]

# El Gestor de BD solo se muestra en el menú si el usuario logueado es admin
if is_admin:
    nav_pages.append(st.Page(_page("pages", "7_gestor_bd.py"), title="Gestor BD", icon="🗄️"))

pg = st.navigation(nav_pages)
pg.run()
