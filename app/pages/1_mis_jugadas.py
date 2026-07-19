import streamlit as st
import plotly.express as px
from datetime import date
import os, sys
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Mis Jugadas - SueñaLotto", page_icon="📝", layout="wide")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.shared import render_global_header, api_get, api_post, init_session_state

init_session_state()

if not st.session_state.get("user"):
    st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">Acceso Requerido</h2><p style="color:#94a3b8;">Inicia sesión para acceder a Mis Jugadas.</p></div>', unsafe_allow_html=True)
    st.stop()

render_global_header()

st.markdown("""
<style>
    .card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; }
    .card h3 { color: var(--text-primary); margin-bottom: 0.5rem; }
    .bet-stat-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 0.75rem; padding: 1rem; text-align: center; }
    .bet-stat-card .stat-value { font-size: 1.4rem; font-weight: 800; }
    .bet-stat-card .stat-label { font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.2rem; }
    .bet-stat-card .stat-value.positive { color: #22c55e; }
    .bet-stat-card .stat-value.negative { color: #ef4444; }
    .bet-stat-card .stat-value.accent { color: #fbbf24; }
    .pago-box { text-align:center; padding:0.3rem 0; border:1px solid var(--border-color); border-radius:0.5rem; background:var(--bg-card); }
    .pago-box .label { font-size:0.65rem; color:#64748b; display:block; }
    .pago-box .value { font-size:1.1rem; font-weight:800; color:#fbbf24; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="color:#fbbf24;text-align:center;">📝 Mis Jugadas</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:var(--text-secondary);text-align:center;">Registra tus jugadas y calcula ganancias potenciales</p>', unsafe_allow_html=True)

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

    st.markdown("""
    <style>
        .pay-row { display:flex; align-items:center; justify-content:space-between; background:rgba(30,41,59,0.5); border-radius:0.75rem; padding:0.5rem 0.75rem; margin-bottom:0.5rem; gap:0.5rem; }
        .pay-label { font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px; font-weight:600; min-width:5rem; }
        .pay-value { font-size:1.1rem; font-weight:800; color:#fbbf24; min-width:3.5rem; text-align:center; }
        .num-card { background:rgba(30,41,59,0.4); border:1px solid rgba(51,65,85,0.6); border-radius:0.75rem; padding:0.75rem; margin-bottom:0.6rem; transition:border-color 0.2s; }
        .num-card:hover { border-color:rgba(251,191,36,0.4); }
        .num-card .num-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem; }
        .num-card .num-title { font-size:1.1rem; font-weight:900; color:#fbbf24; }
        .num-card .num-input-group { display:flex; align-items:center; gap:0.4rem; }
        .num-card .num-input-group label { font-size:0.65rem; color:#94a3b8; font-weight:600; text-transform:uppercase; min-width:3.5rem; }
        .num-card .payout-preview { font-size:0.75rem; color:#94a3b8; padding-top:0.3rem; }
        .num-card .payout-preview strong { color:#22c55e; }
        .num-card.candado { border-color:rgba(34,197,94,0.4); background:rgba(34,197,94,0.05); }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Pagos")
    for key, label, delta, minv, maxv in [
        ("fijo", "FIJO", 5, 1, 999),
        ("corrido", "CORRIDO", 5, 1, 999),
        ("parle", "PARLE", 50, 1, 9999),
    ]:
        pc1, pc2, pc3, pc4 = st.columns([0.7, 0.3, 1.2, 1.2])
        pc1.markdown(f'<div style="padding:0.35rem 0;font-size:0.7rem;color:#94a3b8;font-weight:600;text-transform:uppercase;">{label}</div>', unsafe_allow_html=True)
        if pc2.button("−", key=f"pm_{key}", use_container_width=True):
            pagos[key] = max(minv, pagos[key] - delta)
            st.session_state["pagos"] = pagos; st.rerun()
        pagos[key] = pc3.number_input("", min_value=minv, max_value=maxv, value=pagos[key], step=delta, key=f"pago_{key}", label_visibility="collapsed", format="%d")
        if pc4.button("+", key=f"pp_{key}", use_container_width=True):
            pagos[key] = min(maxv, pagos[key] + delta)
            st.session_state["pagos"] = pagos; st.rerun()
    st.session_state["pagos"] = pagos

    st.markdown("---")

    b_fecha = st.date_input("📅 Fecha", value=date.today(), key="mj_fecha")

    b_numeros_str = st.text_input("🔢 Números separados por coma o guión", placeholder="Ej: 1,2,3 o 1-2-3", key="mj_nums")
    b_desc = st.text_input("📝 Descripción (opcional)", placeholder="Ej: Jugada de la suerte", key="mj_desc")

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
        st.markdown(f'<div style="margin:0.5rem 0;padding:0.5rem 0.75rem;background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2);border-radius:0.5rem;font-size:0.85rem;color:#94a3b8;">📐 <strong style="color:#fbbf24;">{N} números</strong> → <strong style="color:#fbbf24;">{num_parlets}</strong> combinaciones Parlet</div>', unsafe_allow_html=True)

        st.markdown("### 🎯 Montos por número")
        for idx, n in enumerate(nums_clean):
            mf_key = f"mj_mf_{idx}"
            mc_key = f"mj_mc_{idx}"
            cd_key = f"mj_cd_{idx}"
            mf_val = st.session_state.get(mf_key, 0.0)
            mc_val = st.session_state.get(mc_key, 0.0)
            cand_val = st.session_state.get(cd_key, False)

            col_a, col_b, col_c, col_d = st.columns([0.5, 1.8, 1.8, 0.5])
            col_a.markdown(f'<div style="font-weight:900;font-size:1.2rem;color:#fbbf24;padding:0.4rem 0;text-align:center;">{n:02d}</div>', unsafe_allow_html=True)
            mf = col_b.number_input("FIJO $", min_value=0.0, step=0.5, format="%.2f", key=mf_key, label_visibility="collapsed", placeholder="FIJO $")
            mc = col_c.number_input("CORR $", min_value=0.0, step=0.5, format="%.2f", key=mc_key, label_visibility="collapsed", placeholder="CORR $")
            cand = col_d.checkbox("🔒", key=cd_key, help="Incluir en Candado/Parlet")

            p_fijo = mf * pagos["fijo"]
            p_corrido = mc * pagos["corrido"]
            st.markdown(
                f'<div style="font-size:0.7rem;color:#64748b;margin:-0.3rem 0 0.3rem 0.5rem;">🏆 <strong style="color:#22c55e;">${p_fijo:.2f}</strong> si FIJO + <strong style="color:#22c55e;">${p_corrido:.2f}</strong> si CORRIDO</div>'
                if mf > 0 or mc > 0 else
                f'<div style="font-size:0.65rem;color:#475569;margin:-0.3rem 0 0.3rem 0.5rem;">Sin monto asignado</div>',
                unsafe_allow_html=True,
            )

            per_number_data.append({"n": n, "fijo": mf, "corrido": mc, "candado": cand})
            monto_fijo_total += mf
            monto_corrido_total += mc

        st.markdown("---")
        candado_total = st.number_input("💰 Monto total Candado ($)", min_value=0.0, step=1.0, value=0.0, key="mj_candado_total", help="Monto total a repartir entre los números con candado activo")
        total_precio = monto_fijo_total + monto_corrido_total + candado_total

        st.markdown(
            f'<div style="text-align:right;padding:0.75rem 1rem;background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2);border-radius:0.75rem;margin:0.75rem 0;">'
            f'<div style="font-size:0.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">Total a jugar</div>'
            f'<div style="font-size:1.5rem;font-weight:900;color:#fbbf24;">${total_precio:.2f}</div>'
            f'<div style="font-size:0.7rem;color:#64748b;">${monto_fijo_total:.2f} FIJO + ${monto_corrido_total:.2f} CORR + ${candado_total:.2f} Candado</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        N_encerrados = sum(1 for d in per_number_data if d["candado"])
        parlets = N_encerrados * (N_encerrados - 1) // 2 if N_encerrados >= 2 else 0
        if parlets > 0 and candado_total > 0:
            valor_parlet = candado_total / parlets
            gp = valor_parlet * pagos["parle"]
            st.markdown(
                f'<div style="padding:0.6rem 0.75rem;background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.25);border-radius:0.5rem;font-size:0.8rem;color:#94a3b8;margin-bottom:0.75rem;">'
                f'<strong>🏆 Si aciertas un número:</strong> ganas el FIJO y CORRIDO de ese número + Parlet <strong style="color:#fbbf24;">${gp:.2f}</strong>'
                f'</div>', unsafe_allow_html=True,
            )

        if st.button("💾 Guardar Jugada", type="primary", use_container_width=True, key="mj_save"):
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
