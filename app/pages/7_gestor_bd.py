import streamlit as st
import httpx
import json
import os
import sys
from datetime import date, datetime

st.set_page_config(page_title="Gestor de BD - SueñaLotto", page_icon="🗄️", layout="wide")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.shared import render_global_header, api_get, api_post, init_session_state
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

init_session_state()

if not st.session_state.get("user"):
    st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🔒</div><h2 style="color:#f1f5f9;">Acceso Restringido</h2><p style="color:#94a3b8;">Necesitas iniciar sesión.</p></div>', unsafe_allow_html=True)
    st.stop()

user_tier = st.session_state.get("user", {}).get("tier")
if user_tier != "admin":
    st.markdown('<div style="max-width:500px;margin:3rem auto;text-align:center;padding:3rem;background:#1e293b;border-radius:1rem;border:1px solid #334155;"><div style="font-size:3rem;margin-bottom:1rem;">🚫</div><h2 style="color:#ef4444;">Solo Administradores</h2><p style="color:#94a3b8;">El Gestor de Base de Datos es exclusivo para administradores.</p></div>', unsafe_allow_html=True)
    st.stop()

render_global_header()

st.markdown('<h1 style="color:#fbbf24;text-align:center;">🗄️ Gestor de Base de Datos</h1>', unsafe_allow_html=True)

TABLAS = {
    "resultados": "Resultados",
    "charada": "Charada",
    "adivinanzas": "Adivinanzas",
    "posible_salir": "Posible Salir",
    "users": "Usuarios",
    "bets": "Jugadas",
    "user_usage": "Uso de Usuarios",
    "other_games": "Otros Juegos",
}

# Columnas de la tabla users que el admin no debe ver ni editar (hash, tokens).
SENSITIVE_USER_COLS = {
    "password_hash",
    "email_verification_token",
    "password_reset_token",
    "password_reset_expires",
}


def _api_call(method: str, path: str, timeout: float = 20, **kwargs):
    """Llamada HTTP con manejo amigable de errores.
    Devuelve (data, None) en éxito o (None, mensaje_error)."""
    try:
        r = httpx.request(
            method,
            f"{API_URL}{path}",
            headers={"Authorization": f"Bearer {st.session_state.get('token', '')}"},
            timeout=timeout,
            **kwargs,
        )
    except httpx.ConnectError:
        return None, "Servidor no disponible. Intenta de nuevo."
    if r.status_code < 300:
        try:
            return r.json(), None
        except Exception:
            return {}, None
    try:
        detail = r.json().get("detail", f"Error {r.status_code}")
    except Exception:
        detail = f"Error {r.status_code}"
    if r.status_code == 401:
        detail = "Sesión expirada. Inicia sesión de nuevo."
    elif r.status_code == 405:
        detail = "Operación no soportada por el servidor."
    return None, detail


def _render_form_fields(columns, prefix, existing=None):
    """Genera los widgets del formulario y devuelve el dict con los valores.
    Para la tabla users: oculta hash/tokens y ofrece contraseña en texto plano."""
    values = {}
    editing = existing is not None
    for col in columns:
        name = col["name"]
        ctype = col["type"]
        if col.get("primary"):
            continue
        if name in SENSITIVE_USER_COLS:
            continue
        key = f"{prefix}_{name}"
        current = (existing or {}).get(name)
        if ctype == "DATE":
            if editing and current is None:
                enable = st.checkbox(f"Definir {name}", value=False, key=f"{key}_set")
                v = st.date_input(name, value=date.today(), key=key) if enable else None
            elif editing:
                try:
                    default = date.fromisoformat(current[:10])
                except (ValueError, TypeError):
                    default = date.today()
                v = st.date_input(name, value=default, key=key)
            else:
                v = st.date_input(name, value=date.today(), key=key)
            if v:
                values[name] = v.isoformat()
        elif ctype == "INTEGER":
            if name == "id":
                continue
            v = st.number_input(name, value=int(current or 0), step=1, key=key)
            values[name] = int(v)
        elif ctype == "FLOAT":
            v = st.number_input(name, value=float(current or 0.0), step=0.5, key=key)
            values[name] = float(v)
        elif ctype == "BOOLEAN":
            v = st.checkbox(name, value=bool(current), key=key)
            values[name] = v
        elif ctype == "DATETIME":
            v = st.text_input(name, value=str(current or ""), key=key, placeholder="2026-07-29T12:00:00")
            if v:
                values[name] = v
        else:
            v = st.text_input(name, value=str(current or ""), key=key)
            values[name] = v

    if any(c["name"] in SENSITIVE_USER_COLS for c in columns):
        hint = "Déjala vacía para no cambiarla." if editing else "Obligatoria."
        v = st.text_input("🔑 Contraseña", type="password", key=f"{prefix}_password",
                          placeholder=hint, help="Escribe la contraseña en texto plano; se hashea automáticamente.")
        values["password"] = v
    return values


def _rec_brief(table, rec) -> str:
    r = rec
    if table == "users":
        return (f"<b style='color:#f1f5f9;'>{r.get('username', '')}</b> · "
                f"<span style='color:#94a3b8;'>{r.get('email', '')}</span> · "
                f"<span style='color:#fbbf24;'>tier: {r.get('tier', '')}</span> · "
                f"<span style='color:#64748b;'>desde {str(r.get('created_at', ''))[:10]}</span>")
    if table == "resultados":
        nums = " - ".join(str(r.get(k)) for k in ("n1", "n2", "n3", "n4") if r.get(k) is not None)
        return f"{r.get('fecha', '')} · {r.get('juego', '')} {r.get('sorteo', '')} · <b style='color:#fbbf24;'>{nums}</b>"
    if table == "charada":
        return f"<b style='color:#fbbf24;'>{r.get('numero', '')}</b> · {str(r.get('significados', ''))[:70]}"
    if table == "adivinanzas":
        return f"{r.get('fecha', '')} · {str(r.get('texto', ''))[:70]}"
    if table == "posible_salir":
        return f"{r.get('fecha', '')} · {r.get('sorteo', '')} · <b style='color:#fbbf24;'>{r.get('numeros', '')}</b>"
    if table == "bets":
        return (f"{str(r.get('fecha', ''))[:10]} · {r.get('juego', '')} · "
                f"<b style='color:#fbbf24;'>{r.get('numeros', '')}</b> · ${r.get('precio', '')}")
    if table == "user_usage":
        return (f"user <b style='color:#f1f5f9;'>{r.get('user_id', '')}</b> · {r.get('fecha', '')} · "
                f"charada {r.get('charada_count', '')} · búsquedas {r.get('busquedas_count', '')} · histórica {r.get('historica_count', '')}")
    if table == "other_games":
        return f"{r.get('game_name', '')} · {r.get('fecha', '')} · <b style='color:#fbbf24;'>{r.get('numbers', '')}</b>"
    return str(rec)[:80]


@st.dialog("✏️ Editar registro", width="large")
def open_edit(table, columns, rec):
    st.markdown(
        f'<div style="background:#1e293b;border:1px solid #334155;border-radius:0.75rem;'
        f'padding:0.75rem 1rem;margin-bottom:1rem;">{_rec_brief(table, rec)}</div>',
        unsafe_allow_html=True,
    )
    vals = _render_form_fields(columns, f"ed_{rec['id']}", existing=rec)
    if st.button("💾 Guardar cambios", type="primary", use_container_width=True):
        if not vals.get("password"):
            vals.pop("password", None)
        data, err = _api_call("PUT", f"/api/admin/db/{table}/records/{rec['id']}", json=vals)
        if err:
            st.error(err)
        else:
            st.success("✅ Registro actualizado")
            st.rerun()


@st.dialog("🗑️ Eliminar registro", width="large")
def open_delete(table, rec):
    st.warning("⚠️ **Esta acción es irreversible.** El registro se eliminará de la base de datos definitivamente.")
    st.markdown(
        f'<div style="background:#1e293b;border:1px solid #334155;border-radius:0.75rem;'
        f'padding:0.75rem 1rem;margin-bottom:1rem;">'
        f'<div style="color:#64748b;font-size:0.75rem;">ID {rec["id"]}</div>{_rec_brief(table, rec)}</div>',
        unsafe_allow_html=True,
    )
    confirm = st.checkbox("✅ He leído la advertencia y confirmo que quiero eliminar este registro",
                          key=f"del_confirm_{table}_{rec['id']}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Eliminar definitivamente", type="primary", disabled=not confirm, use_container_width=True):
            data, err = _api_call("DELETE", f"/api/admin/db/{table}/records/{rec['id']}")
            if err:
                st.error(err)
            else:
                st.success("✅ Registro eliminado")
                st.rerun()
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()


@st.dialog("➕ Crear registro", width="large")
def open_create(table, columns):
    vals = _render_form_fields(columns, "new")
    if st.button("➕ Insertar", type="primary", use_container_width=True):
        if not vals.get("password"):
            vals.pop("password", None)
        data, err = _api_call("POST", f"/api/admin/db/{table}/records", json=vals)
        if err:
            st.error(err)
        else:
            st.success(f"✅ Registro creado con ID {data.get('id')}")
            st.rerun()


tab_tablas, tab_export, tab_backups, tab_historicos = st.tabs(["📋 Tablas y Registros", "📤 Exportar / Importar", "💾 Copias de Seguridad", "📜 Históricos (PDF)"])

# ─── Tab 1: CRUD ────────────────────────────────────────────────────
with tab_tablas:
    tables_meta = api_get("/api/admin/db/tables") or []
    if not tables_meta:
        st.error("No se pudo conectar con el backend.")
        st.stop()

    table_names = [t["table"] for t in tables_meta]
    col_sel, col_count = st.columns([3, 1])
    with col_sel:
        sel_table = st.selectbox("Tabla", table_names, format_func=lambda t: TABLAS.get(t, t), key="gbd_table")
    with col_count:
        meta_sel = next((t for t in tables_meta if t["table"] == sel_table), None)
        if meta_sel:
            st.markdown(f'<div style="text-align:center;margin-top:1.8rem;background:#1e293b;border:1px solid #334155;border-radius:0.75rem;padding:0.5rem;"><span style="font-size:1.5rem;font-weight:800;color:#fbbf24;">{meta_sel["count"]}</span><div style="color:#64748b;font-size:0.7rem;">registros</div></div>', unsafe_allow_html=True)

    columns = meta_sel["columns"] if meta_sel else []

    st.markdown("---")

    # Navegación de páginas
    total = meta_sel["count"] if meta_sel else 0
    page_size = 20
    total_pages = max(1, (total + page_size - 1) // page_size)
    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        prev_btn = st.button("⬅️ Anterior", key="db_prev", disabled=(total_pages <= 1))
    with nav3:
        next_btn = st.button("Siguiente ➡️", key="db_next", disabled=(total_pages <= 1))
    if "gbd_page" not in st.session_state:
        st.session_state["gbd_page"] = 1
    if prev_btn and st.session_state["gbd_page"] > 1:
        st.session_state["gbd_page"] -= 1
        st.rerun()
    if next_btn and st.session_state["gbd_page"] < total_pages:
        st.session_state["gbd_page"] += 1
        st.rerun()
    with nav2:
        st.markdown(f'<div style="text-align:center;color:#64748b;margin-top:0.4rem;">Página {st.session_state["gbd_page"]} de {total_pages}</div>', unsafe_allow_html=True)

    recs_resp = api_get(f"/api/admin/db/{sel_table}/records", {"page": st.session_state["gbd_page"], "size": page_size})
    records = (recs_resp or {}).get("records", [])

    st.markdown("---")

    if records:
        hc = st.columns([0.6, 3.2, 0.9, 0.9])
        for i, h in enumerate(["ID", "Registro", "Editar", "Eliminar"]):
            hc[i].markdown(
                f'<div style="color:#64748b;font-size:0.65rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.5px;padding:0.2rem 0;">{h}</div>',
                unsafe_allow_html=True,
            )
        for rec in records:
            rid = rec.get("id")
            row = st.columns([0.6, 3.2, 0.9, 0.9])
            with row[0]:
                st.markdown(
                    f'<div style="background:#334155;border-radius:0.5rem;padding:0.55rem 0.3rem;'
                    f'text-align:center;color:#fbbf24;font-weight:800;font-size:0.9rem;">{rid}</div>',
                    unsafe_allow_html=True,
                )
            with row[1]:
                st.markdown(
                    f'<div style="background:#1e293b;border:1px solid #334155;border-radius:0.5rem;'
                    f'padding:0.5rem 0.8rem;min-height:2.6rem;display:flex;align-items:center;">{_rec_brief(sel_table, rec)}</div>',
                    unsafe_allow_html=True,
                )
            with row[2]:
                if st.button("✏️", key=f"ge_{sel_table}_{rid}", help="Editar este registro", use_container_width=True):
                    open_edit(sel_table, columns, rec)
            with row[3]:
                if st.button("🗑️", key=f"gd_{sel_table}_{rid}", help="Eliminar este registro", use_container_width=True):
                    open_delete(sel_table, rec)
    else:
        st.info("No hay registros en esta tabla.")

    st.markdown("---")

    if st.button("➕ Crear nuevo registro", type="primary", use_container_width=True):
        open_create(sel_table, columns)

# ─── Tab 2: Export / Import ─────────────────────────────────────────
with tab_export:
    st.markdown('<div class="card"><h3>📤 Exportar base de datos completa</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:#94a3b8;font-size:0.85rem;">Descarga un archivo JSON con <b>todas las tablas y registros</b>. Úsalo como respaldo o para transferir la BD a otro servidor.</p>', unsafe_allow_html=True)

    export_data = api_get("/api/admin/db/export", timeout=120)
    if export_data:
        json_bytes = json.dumps(export_data, ensure_ascii=False, indent=1, default=str).encode("utf-8")
        st.download_button(
            "⬇️ Descargar backup completo (JSON)",
            data=json_bytes,
            file_name=f"suenalotto_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            type="primary",
            use_container_width=True,
        )
        total_rows = sum(len(v) for v in export_data.get("tables", {}).values())
        st.markdown(f'<p style="color:#64748b;font-size:0.75rem;">📊 Total: {total_rows} registros · {len(export_data.get("tables", {}))} tablas · generado {export_data.get("created_at", "")}</p>', unsafe_allow_html=True)
    else:
        st.error("No se pudo exportar la base de datos.")

    st.markdown("---")

    st.markdown('<h3>📥 Importar base de datos completa</h3>', unsafe_allow_html=True)
    st.warning("⚠️ El modo 'Reemplazar' borra los datos existentes de cada tabla antes de insertar. Se recomienda hacer un backup antes de importar.")
    uploaded = st.file_uploader("Sube un archivo JSON (exportación o backup)", type=["json"], key="db_import_file")
    import_mode = st.radio("Modo de importación", ["replace", "merge"], index=0, horizontal=True,
                           format_func=lambda m: "Reemplazar (borra y reinserta)" if m == "replace" else "Mezclar (actualiza/inserta por ID)")
    if uploaded and st.button("📥 Importar", type="primary", use_container_width=True):
        try:
            payload = json.loads(uploaded.getvalue().decode("utf-8"))
        except Exception:
            st.error("El archivo no es un JSON válido.")
            st.stop()
        res = api_post("/api/admin/db/import", {"mode": import_mode, "data": payload}, timeout=600)
        if res and res.get("status") == "ok":
            imported = res.get("imported", {})
            st.success(f"✅ Importación completada: {sum(imported.values())} registros en {len(imported)} tablas")
            for t, c in imported.items():
                st.markdown(f'<p style="color:#94a3b8;font-size:0.8rem;margin:0;">&nbsp;&nbsp;• {TABLAS.get(t, t)}: <b style="color:#fbbf24;">{c}</b></p>', unsafe_allow_html=True)
        else:
            detalle = st.session_state.get("last_api_error")
            st.error(f"La importación falló. {detalle or 'Revisa el formato del archivo.'}")

# ─── Tab 3: Backups ─────────────────────────────────────────────────
with tab_backups:
    st.markdown('<div class="card"><h3>💾 Copias de Seguridad Automáticas</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:#94a3b8;font-size:0.85rem;">Se realiza un backup automático de la base de datos completa <b>2 veces al día</b>: <b style="color:#fbbf24;">12:00 AM (medianoche)</b> y <b style="color:#fbbf24;">12:00 PM (mediodía)</b>.</p>', unsafe_allow_html=True)

    status = api_get("/api/admin/db/backup-status") or {}
    sched = status.get("schedule", ["00:00", "12:00"])
    st.markdown(f'<p style="color:#64748b;font-size:0.85rem;">🕐 Horario programado: <b>{", ".join(sched)}</b> · Backups guardados: <b style="color:#fbbf24;">{status.get("backups_total", 0)}</b> · Retención: 30 backups</p>', unsafe_allow_html=True)
    last_status = status.get("status", {})
    if last_status.get("last_backup"):
        st.markdown(f'<p style="color:#22c55e;font-size:0.85rem;">✅ Último backup: <b>{last_status.get("filename", "")}</b> ({last_status.get("created_at", last_status.get("last_backup", ""))}) · {last_status.get("total_rows", "?")} registros</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#fbbf24;font-size:0.85rem;">⏳ Aún no se ha ejecutado ningún backup automático. Ejecuta uno manualmente o espera la próxima hora programada.</p>', unsafe_allow_html=True)

    if st.button("🛡️ Hacer backup AHORA", type="primary", use_container_width=True):
        res = api_post("/api/admin/db/backups/run")
        if res and res.get("status") == "ok":
            st.success(f"✅ Backup creado: {res.get('filename')} ({res.get('total_rows')} registros)")
            st.rerun()
        else:
            st.error("No se pudo crear el backup.")

    st.info("💡 **Importante:** en el plan Free de Render el disco es efímero (se borra al reiniciar el servicio). Descarga los backups a tu máquina regularmente con el botón de exportación para tener respaldos permanentes.", icon="⚠️")

    st.markdown("---")
    st.markdown('<h3>🗂️ Backups guardados</h3>', unsafe_allow_html=True)
    backups = api_get("/api/admin/db/backups") or []
    if not backups:
        st.info("No hay backups guardados todavía.")
    else:
        st.markdown(f'<p style="color:#64748b;font-size:0.75rem;">Directorio: <code>{status.get("backup_dir", "")}</code></p>', unsafe_allow_html=True)
        for b in backups:
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                st.markdown(f'<div style="background:#1e293b;border:1px solid #334155;border-radius:0.5rem;padding:0.5rem 0.8rem;"><b style="color:#f1f5f9;font-size:0.85rem;">{b["filename"]}</b><div style="color:#64748b;font-size:0.7rem;">{b["created_at"]}</div></div>', unsafe_allow_html=True)
            with c2:
                size_kb = b["size"] / 1024
                st.markdown(f'<div style="text-align:center;margin-top:0.9rem;color:#94a3b8;font-size:0.8rem;">{size_kb:.1f} KB</div>', unsafe_allow_html=True)
            with c3:
                if st.button("🔄 Restaurar", key=f"restore_{b['filename']}", use_container_width=True):
                    res = api_post(f"/api/admin/db/backups/{b['filename']}/restore")
                    if res and res.get("status") == "ok":
                        st.success(f"✅ Backup restaurado: {b['filename']}")
                        st.rerun()
                    else:
                        st.error("No se pudo restaurar el backup.")
            with c4:
                if st.button("🗑️", key=f"del_{b['filename']}", use_container_width=True):
                    r = httpx.request("DELETE", f"{API_URL}/api/admin/db/backups/{b['filename']}",
                                      headers={"Authorization": f"Bearer {st.session_state['token']}"}, timeout=15)
                    if r.status_code == 200:
                        st.success("Backup eliminado")
                        st.rerun()
                    else:
                        st.error("No se pudo eliminar.")

# ─── Tab 4: Históricos (PDF) ────────────────────────────────────────
with tab_historicos:
    st.markdown('<div class="card"><h3>📜 Históricos desde PDF (Pick 3 / Pick 4)</h3>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.85rem;">Al arrancar, el servidor intenta descargar automáticamente los '
        'PDFs oficiales desde 1988. Si esa descarga falla (sin conexión, timeout, OOM) la tabla queda con muy pocos '
        'registros. Aquí puedes <b>repoblarla manualmente</b> sin esperar al arranque. La operación descarga el PDF de '
        'nuevo, lo parsea e inserta lo que falte (deduplica por juego, fecha y sorteo).</p>',
        unsafe_allow_html=True,
    )

    status = _api_call("GET", "/api/system/history-status", timeout=60)[0] or {}
    juegos = status.get("juegos", {})

    if status.get("importing"):
        st.warning("⏳ Hay una importación automática en curso. Puedes lanzar una repoblación manual igualmente (se ejecutan en serie).")

    if not juegos:
        st.error("No se pudo consultar el estado del histórico. ¿El backend está corriendo?")
    else:
        for j, s in juegos.items():
            completo = bool(s.get("completo"))
            count = s.get("count", 0)
            min_f = str(s.get("min_fecha") or "—")[:10]
            max_f = str(s.get("max_fecha") or "—")[:10]
            icon = "✅" if completo else "❌"
            color = "#22c55e" if completo else "#ef4444"
            st.markdown(
                f'<div style="background:#1e293b;border:1px solid #334155;border-radius:0.75rem;'
                f'padding:0.6rem 1rem;margin-bottom:0.5rem;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<b style="color:#f1f5f9;">{j}</b>'
                f'<span style="color:{color};font-weight:700;">{icon} {"Completo" if completo else "Incompleto / vacío"}</span>'
                f'</div>'
                f'<div style="color:#94a3b8;font-size:0.8rem;">📊 <b style="color:#fbbf24;">{count}</b> registros · desde <b>{min_f}</b> · hasta <b>{max_f}</b></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    last_pop = status.get("last_populate") or {}
    if last_pop and last_pop.get("ejecutado"):
        juego_txt = last_pop.get("juego") or "ambos"
        fuerza_txt = f" · forzada: {last_pop.get('fuerza')}"
        st.markdown(
            f'<p style="color:#64748b;font-size:0.8rem;">🕐 Última repoblación manual: '
            f'<b>{str(last_pop.get("ejecutado", ""))[:19]}</b> · juego: <b>{juego_txt}</b>{fuerza_txt}</p>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    fuerza = st.checkbox(
        "🔄 Forzar re-importación (descarga el PDF aunque el histórico esté completo)",
        value=False,
        key="gbd_hist_fuerza",
        help="Útil si crees que faltan registros o el PDF oficial cambió. La inserción deduplica, no duplica registros.",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        btn_p3 = st.button("📥 Repoblar Pick 3", use_container_width=True)
    with c3:
        btn_p4 = st.button("📥 Repoblar Pick 4", use_container_width=True)
    with c2:
        btn_ambos = st.button("📥 Repoblar Ambos", type="primary", use_container_width=True)

    if btn_p3 or btn_p4 or btn_ambos:
        juego = ("Pick 3" if btn_p3 else "Pick 4") if (btn_p3 or btn_p4) else None
        with st.spinner("⬇️ Descargando PDF, parseando e insertando… (puede tardar 1-3 min)"):
            reporte, err = _api_call(
                "POST", "/api/admin/db/populate-historical",
                json={"juego": juego, "fuerza": fuerza}, timeout=900,
            )
        if err:
            st.error(f"La repoblación falló: {err}")
        else:
            st.success("✅ Repoblación completada.")
            for j, r in (reporte or {}).get("juegos", {}).items():
                if r.get("salteado"):
                    st.markdown(f'<p style="color:#64748b;font-size:0.85rem;">&nbsp;&nbsp;• {j}: <b>salteado</b> (ya estaba completo). Usa “Forzar” para re-importar igualmente.</p>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<p style="color:#94a3b8;font-size:0.85rem;">&nbsp;&nbsp;• {j}: <b style="color:#fbbf24;">{r.get("insertados", 0)}</b> '
                        f'registros nuevos · total <b style="color:#fbbf24;">{r.get("count", 0)}</b> · desde <b>{str(r.get("min_fecha") or "—")[:10]}</b> '
                        f'hasta <b>{str(r.get("max_fecha") or "—")[:10]}</b></p>',
                        unsafe_allow_html=True,
                    )

    st.info("💡 Los registros quedan guardados en la base de datos (Neon), de modo que sobreviven a los reinicios "
            "del servidor. Si la descarga automática al arrancar falló, este proceso es el respaldo.")
