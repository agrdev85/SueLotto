"""
Gestor de Base de Datos — SueñaLotto.

Proporciona:
  - Export/import completo de la base de datos (JSON)
  - CRUD genérico sobre las tablas del modelo
  - Copias de seguridad automáticas 2x/día (00:00 y 12:00)
  - Listado, restauración y borrado de backups
"""
import os
import json
import time
import logging
import threading
from datetime import datetime, date

from sqlalchemy import Date, DateTime, Integer, Float, Boolean, String, Text, insert
from sqlalchemy.exc import IntegrityError

from backend.database import SessionLocal, IS_SQLITE
from backend import models

logger = logging.getLogger("suenalotto.dbmanager")

BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "backups",
)
STATUS_FILE = os.path.join(BACKUP_DIR, "status.json")

# Horas del día en que se ejecuta el backup automático:
# 0  = 12:00 AM (medianoche / 12 de la noche)
# 12 = 12:00 PM (mediodía / 12 de la mañana)
BACKUP_HOURS = (0, 12)
MAX_BACKUPS = 30  # retención: se eliminan los backups más antiguos

# Columnas sensibles de la tabla users que nunca deben verse ni editarse
# desde el frontend (hash de contraseña y tokens internos).
SENSITIVE_USER_COLS = {
    "password_hash",
    "email_verification_token",
    "password_reset_token",
    "password_reset_expires",
}

TABLE_MODELS = [
    ("resultados", models.Resultado),
    ("charada", models.Charada),
    ("adivinanzas", models.Adivinanza),
    ("posible_salir", models.PosibleSalir),
    ("users", models.User),
    ("bets", models.Bet),
    ("user_usage", models.UserUsage),
    ("other_games", models.OtherGameResult),
]

TABLE_BY_NAME = {name: model for name, model in TABLE_MODELS}


def _prepare_user_payload(model, data: dict) -> dict:
    """Para la tabla users: recibe la contraseña en texto plano en el campo
    'password' y la hashea internamente en 'password_hash'. Elimina columnas
    sensibles que no deben manejarse desde el frontend."""
    if model.__tablename__ != "users":
        return data
    out = dict(data)
    password = out.pop("password", None)
    if password:
        from backend.auth import hash_password
        out["password_hash"] = hash_password(password)
    else:
        out.pop("password_hash", None)
    for col in SENSITIVE_USER_COLS:
        if col != "password_hash":
            out.pop(col, None)
    return out

_scheduler_thread = None
_lock = threading.Lock()
_last_backup_key = None


# ─── Serialización ──────────────────────────────────────────────────

def _serialize_value(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _coerce(value, col_type):
    if value is None:
        return None
    if isinstance(col_type, DateTime):
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))
    if isinstance(col_type, Date):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value)[:10])
    if isinstance(col_type, Boolean):
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "si", "t", "on")
        return bool(value)
    if isinstance(col_type, Integer):
        if isinstance(value, str) and not value.strip():
            return None
        return int(value)
    if isinstance(col_type, Float):
        if isinstance(value, str) and not value.strip():
            return None
        return float(value)
    return value


def _row_to_dict(model, obj) -> dict:
    d = {c.name: _serialize_value(getattr(obj, c.name)) for c in model.__table__.columns}
    # Sanitizar sorteo en export para no propagar valores legacy con comillas
    if d.get("sorteo") and isinstance(d["sorteo"], str):
        d["sorteo"] = d["sorteo"].strip().strip("'\"")
    return d


def _get_model(table: str):
    model = TABLE_BY_NAME.get(table)
    if model is None:
        raise ValueError(f"Tabla desconocida: {table}")
    return model


def _apply_values(model, obj, data: dict):
    for col in model.__table__.columns:
        if col.name in data and data[col.name] is not None:
            setattr(obj, col.name, _coerce(data[col.name], col.type))


# Tamaño de lote para inserts masivos. Con distancias cortas (SQLite) un
# lote mayor es más rápido; sobre Postgres remoto (Neon) lotes moderados
# evitan errores de network/connection y mantienen la transacción viva.
IMPORT_BATCH = 500


def _rows_to_columns(model, rows: list) -> list[dict]:
    """Convierte filas exportadas a listas de dicts para insert executemany.
    Se omiten las columnas con valor None (se aplican defaults del server).
    Sanitiza `sorteo` quitando comillas literales heredadas de datos legacy
    (p. ej. "'E'" -> "E", "'M'" -> "M") para que quepa en VARCHAR(1)."""
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        obj = {}
        for col in model.__table__.columns:
            if col.name in row and row[col.name] is not None:
                val = _coerce(row[col.name], col.type)
                if col.name == "sorteo" and isinstance(val, str):
                    val = val.strip().strip("'\"")
                obj[col.name] = val
        out.append(obj)
    return out


# ─── Export / Import ────────────────────────────────────────────────

def export_db(db=None) -> dict:
    """Exporta la base de datos completa a un dict JSON-serializable."""
    own = db is None
    if own:
        db = SessionLocal()
    try:
        tables = {}
        for name, model in TABLE_MODELS:
            rows = db.query(model).all()
            tables[name] = [_row_to_dict(model, r) for r in rows]
        return {
            "app": "suenalotto",
            "type": "backup",
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "engine": "sqlite" if IS_SQLITE else "postgresql",
            "tables": tables,
        }
    finally:
        if own:
            db.close()


def import_db(data: dict, mode: str = "replace", db=None) -> dict:
    """
    Importa una exportación/backup.

    mode:
      - replace: borra la tabla y reinserta los datos (usando inserts por
        lotes ejecutados con executemany → rápido incluso contra Postgres
        remoto como Neon, donde la importación fila a fila se colgaba).
      - merge:  actualiza/inserta fila por fila (requiere 'id' presente).
    """
    if not isinstance(data, dict):
        raise ValueError("Formato inválido: se esperaba un objeto JSON")
    tables = data.get("tables") if isinstance(data.get("tables"), dict) else data
    if not isinstance(tables, dict):
        raise ValueError("Formato inválido: no se encontró la sección 'tables'")

    own = db is None
    if own:
        db = SessionLocal()
    imported = {}
    try:
        for name, model in TABLE_MODELS:
            rows = tables.get(name)
            try:
                if not isinstance(rows, list) or not rows:
                    if mode == "replace" and name in tables:
                        db.query(model).delete()
                        db.flush()
                    continue

                if mode == "replace":
                    db.query(model).delete()
                    db.flush()
                    prepared = _rows_to_columns(model, rows)
                    stmt = insert(model)
                    for i in range(0, len(prepared), IMPORT_BATCH):
                        db.execute(stmt, prepared[i:i + IMPORT_BATCH])
                        db.commit()
                    imported[name] = len(prepared)
                else:
                    count = 0
                    for row in rows:
                        if not isinstance(row, dict) or row.get("id") is None:
                            continue
                        existing = db.get(model, int(row["id"]))
                        if existing is None:
                            existing = model()
                        _apply_values(model, existing, row)
                        db.add(existing)
                        count += 1
                    db.commit()
                    imported[name] = count
            except Exception as e:
                db.rollback()
                raise ValueError(f"Tabla '{name}': {e}")

        _reset_sequences(db)
        return {"status": "ok", "mode": mode, "imported": imported}
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Violación de unicidad o integridad: {e.orig}")
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error al importar: {e}")
    finally:
        if own:
            db.close()


def _reset_sequences(db):
    """Re-sincroniza secuencias de autoincremento en PostgreSQL tras un import."""
    if IS_SQLITE:
        return
    for name, model in TABLE_MODELS:
        if "id" not in model.__table__.columns:
            continue
        try:
            db.execute(
                f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {name}), 1), "
                f"(SELECT MAX(id) FROM {name}) IS NOT NULL)"
            )
        except Exception as e:
            logger.warning("No se pudo resetear secuencia de %s: %s", name, e)


# ─── CRUD genérico ──────────────────────────────────────────────────

def get_tables_meta(db=None) -> list:
    own = db is None
    if own:
        db = SessionLocal()
    try:
        meta = []
        for name, model in TABLE_MODELS:
            columns = []
            for col in model.__table__.columns:
                if isinstance(col.type, DateTime):
                    ctype = "DATETIME"
                elif isinstance(col.type, Date):
                    ctype = "DATE"
                else:
                    ctype = str(col.type).upper()
                columns.append({
                    "name": col.name,
                    "type": ctype,
                    "nullable": col.nullable,
                    "primary": col.primary_key,
                })
            meta.append({
                "table": name,
                "count": db.query(model).count(),
                "columns": columns,
            })
        return meta
    finally:
        if own:
            db.close()


def get_records(db, table: str, page: int = 1, size: int = 50) -> dict:
    model = _get_model(table)
    total = db.query(model).count()
    records = (
        db.query(model)
        .order_by(model.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    rows = [_row_to_dict(model, r) for r in records]
    if table == "users":
        for r in rows:
            for col in SENSITIVE_USER_COLS:
                r.pop(col, None)
    return {
        "table": table,
        "total": total,
        "page": page,
        "size": size,
        "records": rows,
    }


def create_record(db, table: str, data: dict) -> dict:
    model = _get_model(table)
    data = _prepare_user_payload(model, data)
    if model.__tablename__ == "users" and not data.get("password_hash"):
        raise ValueError("La contraseña es obligatoria para crear un usuario")
    obj = model()
    _apply_values(model, obj, data)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Violación de unicidad o integridad: {e.orig}")
    db.refresh(obj)
    return {"status": "ok", "id": obj.id}


def update_record(db, table: str, record_id: int, data: dict) -> dict:
    model = _get_model(table)
    data = _prepare_user_payload(model, data)
    obj = db.get(model, record_id)
    if obj is None:
        raise ValueError("Registro no encontrado")
    _apply_values(model, obj, data)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Violación de unicidad o integridad: {e.orig}")
    return {"status": "ok", "id": record_id}


def delete_record(db, table: str, record_id: int) -> dict:
    model = _get_model(table)
    obj = db.get(model, record_id)
    if obj is None:
        raise ValueError("Registro no encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "ok", "id": record_id}


# ─── Backups ────────────────────────────────────────────────────────

def _save_status(**extra):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    status = {"last_backup": datetime.now().isoformat(), **extra}
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, default=str)


def _prune_backups():
    backups = list_backups()
    for old in backups[MAX_BACKUPS:]:
        try:
            os.remove(os.path.join(BACKUP_DIR, old["filename"]))
            logger.info("Backup antiguo eliminado: %s", old["filename"])
        except OSError:
            pass


def run_backup(manual: bool = False) -> dict:
    """Ejecuta un backup completo de la BD a un archivo JSON."""
    data = export_db()
    os.makedirs(BACKUP_DIR, exist_ok=True)
    filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(BACKUP_DIR, filename)
    total_rows = sum(len(rows) for rows in data["tables"].values())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
    _prune_backups()
    _save_status(manual=manual, filename=filename, total_rows=total_rows)
    logger.info("Backup %s creado: %s (%d filas)", "manual" if manual else "automático", filename, total_rows)
    return {
        "status": "ok",
        "filename": filename,
        "total_rows": total_rows,
        "created_at": datetime.now().isoformat(),
    }


def list_backups() -> list:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backups = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith("backup_") and f.endswith(".json"):
            path = os.path.join(BACKUP_DIR, f)
            try:
                stat = os.stat(path)
                backups.append({
                    "filename": f,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except OSError:
                continue
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return backups


def restore_backup(filename: str) -> dict:
    safe = os.path.basename(filename)
    if not safe.startswith("backup_") or not safe.endswith(".json"):
        raise ValueError("Nombre de backup inválido")
    path = os.path.join(BACKUP_DIR, safe)
    if not os.path.exists(path):
        raise ValueError("Backup no encontrado")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    result = import_db(data, mode="replace")
    _save_status(manual=True, filename=safe, action="restore", restored_at=datetime.now().isoformat())
    logger.info("Backup restaurado: %s", safe)
    return {"status": "ok", "restored": safe, **result}


def delete_backup(filename: str) -> dict:
    safe = os.path.basename(filename)
    path = os.path.join(BACKUP_DIR, safe)
    if not os.path.exists(path) or not safe.startswith("backup_"):
        raise ValueError("Backup no encontrado")
    os.remove(path)
    return {"status": "ok", "deleted": safe}


def get_backup_status() -> dict:
    status = {}
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status = json.load(f)
    backups = list_backups()
    return {
        "status": status,
        "schedule": [f"{h:02d}:00" for h in BACKUP_HOURS],
        "backups_total": len(backups),
        "last_backups": backups[:5],
        "backup_dir": BACKUP_DIR,
    }


# ─── Scheduler automático (00:00 y 12:00) ───────────────────────────

def _backup_loop():
    global _last_backup_key
    logger.info("Backup scheduler iniciado — horas: %s", [f"{h:02d}:00" for h in BACKUP_HOURS])
    while True:
        try:
            now = datetime.now()
            if now.hour in BACKUP_HOURS and now.minute <= 1:
                key = f"{now.date()}_{now.hour}"
                if _last_backup_key != key:
                    _last_backup_key = key
                    try:
                        res = run_backup(manual=False)
                        logger.info("Backup automático ejecutado: %s", res.get("filename"))
                    except Exception as e:
                        logger.error("Backup automático falló: %s", e)
            elif now.minute > 1:
                _last_backup_key = None
        except Exception as e:
            logger.error("Error en loop de backups: %s", e)
        time.sleep(60)


def start_backup_scheduler():
    global _scheduler_thread
    with _lock:
        if _scheduler_thread is not None and _scheduler_thread.is_alive():
            return
        try:
            _scheduler_thread = threading.Thread(target=_backup_loop, daemon=True)
            _scheduler_thread.start()
            logger.info("Thread de backups iniciado")
        except Exception as e:
            logger.error("Error iniciando thread de backups: %s", e)
