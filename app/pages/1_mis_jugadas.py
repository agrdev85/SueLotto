import streamlit as st
import httpx
import os
import plotly.express as px
from datetime import date
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Mis Jugadas - SueñaLotto", page_icon="📝", layout="wide")

def _check_auth():
    token = st.session_state.get("token")
    if not token:
        st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">Acceso Requerido</h2><p style="color:#94a3b8;">Inicia sesión para acceder a Mis Jugadas.</p></div>', unsafe_allow_html=True)
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
        st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">Error de conexión</h2><p style="color:#94a3b8;">¿Está el backend encendido?</p></div>', unsafe_allow_html=True)
        st.stop()
        return {}

_t = _check_auth()
if not _t:
    st.stop()

st.markdown("""
<style>
    .stAppDeployButton, .stMainMenu, #MainMenu, footer { display: none !important; visibility: hidden !important; }
    header[data-testid="stHeader"] { background: rgba(15, 23, 42, 0.95) !important; backdrop-filter: blur(12px); border-bottom: 1px solid rgba(251, 191, 36, 0.15); }
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; }
    .card h3 { color: #f1f5f9; }
    .bet-stat-card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; text-align: center; }
    .bet-stat-card .stat-value { font-size: 1.4rem; font-weight: 800; }
    .bet-stat-card .stat-label { font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.2rem; }
    .bet-stat-card .stat-value.positive { color: #22c55e; }
    .bet-stat-card .stat-value.negative { color: #ef4444; }
    .bet-stat-card .stat-value.accent { color: #fbbf24; }
    .pago-box { text-align:center; padding:0.3rem 0; border:1px solid #334155; border-radius:0.5rem; background:#1e293b; }
    .pago-box .label { font-size:0.65rem; color:#64748b; display:block; }
    .pago-box .value { font-size:1.1rem; font-weight:800; color:#fbbf24; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="color:#fbbf24;text-align:center;">📝 Mis Jugadas</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#94a3b8;text-align:center;">Registra tus jugadas y calcula ganancias potenciales</p>', unsafe_allow_html=True)

def api_get(path, params=None):
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, headers=headers, timeout=15)
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
        r = httpx.post(f"{API_URL}{path}", json=json_data or {}, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except:
        return None

bets = api_get("/api/bets")

total_apostado = sum(b.get("precio", 0) or 0 for b in bets) if bets else 0
ganancia_total = sum(float(b.get("ganancia", 0) or 0) for b in bets) if bets else 0

# ─── Stats ───
numeros_set = []
if bets:
    for b in bets:
        if b.get("numeros"):
            for n in b["numeros"].replace("-"," ").split():
                try: numeros_set.append(int(n))
                except: pass

stats = st.columns(5)
stats[0].markdown(f'<div class="bet-stat-card"><div class="stat-value accent">${total_apostado:.2f}</div><div class="stat-label">Total Apostado</div></div>', unsafe_allow_html=True)
stats[1].markdown(f'<div class="bet-stat-card"><div class="stat-value" style="color:#3b82f6;">${ganancia_total:.2f}</div><div class="stat-label">Ganancia Total</div></div>', unsafe_allow_html=True)
balance = ganancia_total - total_apostado
bc = "positive" if balance >= 0 else "negative"
stats[2].markdown(f'<div class="bet-stat-card"><div class="stat-value {bc}">${balance:.2f}</div><div class="stat-label">Balance</div></div>', unsafe_allow_html=True)
stats[3].markdown(f'<div class="bet-stat-card"><div class="stat-value positive">{len(bets) if bets else 0}</div><div class="stat-label">Jugadas</div></div>', unsafe_allow_html=True)
mas_jugado = max(set(numeros_set), key=numeros_set.count) if numeros_set else "—"
stats[4].markdown(f'<div class="bet-stat-card"><div class="stat-value">{mas_jugado}</div><div class="stat-label">N° más jugado</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ─── Payout config + New Bet Form ───
col_form, col_history = st.columns([1, 1])

with col_form:
    st.markdown('<div class="card"><h3>✏️ Nueva jugada</h3>', unsafe_allow_html=True)

    pagos = st.session_state.get("pagos", {"fijo": 75, "corrido": 25, "parle": 900})

    st.markdown("### ⚙️ Pagos")
    pc = st.columns(3)
    for i, (key, label, delta, minv, maxv) in enumerate([
        ("fijo", "FIJO", 5, 1, 999),
        ("corrido", "CORRIDO", 5, 1, 999),
        ("parle", "PARLE", 50, 1, 9999),
    ]):
        with pc[i]:
            fc1, fc2, fc3 = st.columns([1, 2, 1])
            with fc1:
                if st.button("−", key=f"pm_{key}", use_container_width=True):
                    pagos[key] = max(minv, pagos[key] - delta)
                    st.session_state["pagos"] = pagos; st.rerun()
            with fc2:
                st.markdown(f'<div class="pago-box"><span class="label">{label}</span><span class="value">${pagos[key]}</span></div>', unsafe_allow_html=True)
            with fc3:
                if st.button("+", key=f"pp_{key}", use_container_width=True):
                    pagos[key] = min(maxv, pagos[key] + delta)
                    st.session_state["pagos"] = pagos; st.rerun()
    st.session_state["pagos"] = pagos

    st.markdown("---")

    b_fecha = st.date_input("Fecha", value=date.today(), key="mj_fecha")

    b_numeros_str = st.text_input("Números separados por coma o guión", placeholder="Ej: 1,2,3 o 1-2-3", key="mj_nums")
    b_desc = st.text_input("Descripción (opcional)", placeholder="Ej: Jugada de la suerte", key="mj_desc")

    nums_clean = []
    if b_numeros_str:
        nums_clean = [n.strip() for n in b_numeros_str.replace("-"," ").replace(","," ").split() if n.strip().isdigit()]
        nums_clean = [int(n) for n in nums_clean]

    monto_fijo_total = 0
    monto_corrido_total = 0
    per_number_data = []

    if nums_clean:
        N = len(nums_clean)
        num_parlets = N * (N - 1) // 2 if N >= 2 else 0
        st.markdown(f'<div style="margin-bottom:0.5rem;font-size:0.85rem;color:#94a3b8;">📐 <strong style="color:#f1f5f9;">{N} números</strong> → <strong style="color:#fbbf24;">{num_parlets}</strong> combinaciones Parlet</div>', unsafe_allow_html=True)

        st.markdown("### 🎯 Montos por número")
        for idx, n in enumerate(nums_clean):
            row = st.columns([0.5, 2.5, 2.5, 0.6, 2.5])
            row[0].markdown(f'<div style="font-weight:800;font-size:1.1rem;color:#fbbf24;padding-top:0.3rem;">{n:02d}</div>', unsafe_allow_html=True)

            with row[1]:
                fc = st.columns([1, 2.5, 1])
                mf_key = f"mj_mf_{idx}"
                mf_val = st.session_state.get(mf_key, 0.0)
                if fc[0].button("−", key=f"mj_mf_m_{idx}", use_container_width=True):
                    st.session_state[mf_key] = max(0.0, mf_val - 0.5)
                    st.rerun()
                mf = fc[1].number_input("", min_value=0.0, step=0.5, format="%.2f", key=mf_key, label_visibility="collapsed", placeholder="FIJO $")
                if fc[2].button("+", key=f"mj_mf_p_{idx}", use_container_width=True):
                    st.session_state[mf_key] = mf_val + 0.5
                    st.rerun()

            with row[2]:
                fc = st.columns([1, 2.5, 1])
                mc_key = f"mj_mc_{idx}"
                mc_val = st.session_state.get(mc_key, 0.0)
                if fc[0].button("−", key=f"mj_mc_m_{idx}", use_container_width=True):
                    st.session_state[mc_key] = max(0.0, mc_val - 0.5)
                    st.rerun()
                mc = fc[1].number_input("", min_value=0.0, step=0.5, format="%.2f", key=mc_key, label_visibility="collapsed", placeholder="CORR $")
                if fc[2].button("+", key=f"mj_mc_p_{idx}", use_container_width=True):
                    st.session_state[mc_key] = mc_val + 0.5
                    st.rerun()

            cand = row[3].checkbox("🔒", key=f"mj_cd_{idx}", help="Candado")

            p_fijo = mf * pagos["fijo"]
            p_corrido = mc * pagos["corrido"]
            row[4].markdown(f'<div style="font-size:0.7rem;color:#94a3b8;padding-top:0.3rem;">🏆 FIJO <strong style="color:#fbbf24;">${p_fijo:.2f}</strong> + CORR <strong style="color:#fbbf24;">${p_corrido:.2f}</strong></div>', unsafe_allow_html=True)

            per_number_data.append({"n": n, "fijo": mf, "corrido": mc, "candado": cand})
            monto_fijo_total += mf
            monto_corrido_total += mc

        candado_total = st.number_input("💰 Monto total Candado ($)", min_value=0.0, step=1.0, value=0.0, key="mj_candado_total")
        total_precio = monto_fijo_total + monto_corrido_total + candado_total

        N_encerrados = sum(1 for d in per_number_data if d["candado"])
        parlets = N_encerrados * (N_encerrados - 1) // 2 if N_encerrados >= 2 else 0
        if parlets > 0 and candado_total > 0:
            valor_parlet = candado_total / parlets
            gp = valor_parlet * pagos["parle"]
            st.markdown(f'<div style="padding:0.5rem;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);border-radius:0.5rem;font-size:0.8rem;color:#f1f5f9;">🏆 <strong>Si aciertas un número:</strong> ganas el FIJO y CORRIDO de ese número. Además Parle <strong style="color:#fbbf24;">${gp:.2f}</strong></div>', unsafe_allow_html=True)

        st.markdown(f'<div style="text-align:right;font-size:1.3rem;color:#fbbf24;font-weight:800;margin-top:0.75rem;">Total: ${total_precio:.2f}</div>', unsafe_allow_html=True)

        if st.button("💾 Guardar Jugada", type="primary", width='stretch', key="mj_save"):
            numeros_str = "-".join(str(d["n"]) for d in per_number_data)
            fijo_str = ",".join(str(d["fijo"]) for d in per_number_data)
            corrido_str = ",".join(str(d["corrido"]) for d in per_number_data)
            candado_str = ",".join(str(d["n"]) for d in per_number_data if d["candado"])
            api_post("/api/bets", {
                "fecha": b_fecha.isoformat(),
                "numeros": numeros_str,
                "fijo": fijo_str,
                "corrido": corrido_str,
                "parle": str(candado_total),
                "candado": candado_str,
                "precio": total_precio,
                "descripcion": b_desc,
            })
            st.success("✅ Jugada guardada")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─── History Column ───
with col_history:
    st.markdown('<div class="card"><h3>📋 Historial</h3>', unsafe_allow_html=True)
    if bets:
        b_header = ['Fecha', 'Juego', 'Números', '$ FIJO', '$ CORR', 'Candado', 'Total $', 'Ganancia $', '']
        cols = st.columns([1, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.8, 0.4])
        for i, h in enumerate(b_header):
            cols[i].markdown(f'<div style="color:#64748b;font-size:0.6rem;font-weight:600;text-transform:uppercase;">{h}</div>', unsafe_allow_html=True)
        for b in bets:
            cols = st.columns([1, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.8, 0.4])
            cols[0].markdown(f'<div style="font-size:0.7rem;color:#f1f5f9;">{b["fecha"][:10]}</div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div style="font-size:0.7rem;color:#f1f5f9;">{b["juego"]}</div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div style="font-size:0.7rem;font-weight:700;color:#fbbf24;">{b["numeros"]}</div>', unsafe_allow_html=True)
            cols[3].markdown(f'<div style="font-size:0.7rem;color:#f1f5f9;">{b.get("fijo") or "—"}</div>', unsafe_allow_html=True)
            cols[4].markdown(f'<div style="font-size:0.7rem;color:#f1f5f9;">{b.get("corrido") or "—"}</div>', unsafe_allow_html=True)
            cols[5].markdown(f'<div style="font-size:0.7rem;color:#f1f5f9;">{b.get("candado") or "—"}</div>', unsafe_allow_html=True)
            cols[6].markdown(f'<div style="font-size:0.7rem;font-weight:700;color:#fbbf24;">${b.get("precio", 0):.2f}</div>', unsafe_allow_html=True)
            gk = f"mj_gan_{b['id']}"
            gv = st.session_state.get(gk, b.get("ganancia", 0) or 0)
            cols[7].number_input("", min_value=0.0, step=1.0, value=float(gv), key=gk, label_visibility="collapsed", format="%.2f")
            if cols[8].button("✕", key=f"mj_del_{b['id']}", help="Eliminar"):
                api_post(f"/api/bets/{b['id']}/delete", json_data={})
                st.rerun()

        if len(bets) >= 2:
            st.markdown("<br>", unsafe_allow_html=True)
            nums_all = []
            for b in bets:
                if b.get("numeros"):
                    for n in b["numeros"].replace("-"," ").split():
                        try: nums_all.append(int(n))
                        except: pass
            if nums_all:
                from collections import Counter
                freq = Counter(nums_all)
                top_nums = freq.most_common(10)
                fig = px.bar(
                    x=[str(n) for n, _ in top_nums],
                    y=[c for _, c in top_nums],
                    labels={"x": "Número", "y": "Veces"},
                    color=[c for _, c in top_nums],
                    color_continuous_scale="blues",
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8", height=200, margin=dict(l=10, r=10, t=10, b=20),
                    xaxis=dict(tickmode="linear", dtick=1, showgrid=False),
                    yaxis=dict(showgrid=False), showlegend=False,
                )
                fig.update_traces(marker_line_color="#334155", marker_line_width=1)
                st.plotly_chart(fig, width='stretch')
    else:
        st.info("No hay jugadas registradas. Usa el formulario de la izquierda para crear tu primera jugada.")
    st.markdown('</div>', unsafe_allow_html=True)
