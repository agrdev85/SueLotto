"""
Script crítico: Importa datos históricos de la Florida Lottery desde PDFs.
Descarga desde:
  - https://files.floridalottery.com/exptkt/p3.pdf (Pick 3)
  - https://files.floridalottery.com/exptkt/p4.pdf (Pick 4)
Parseo con pdfplumber + regex, carga masiva a la BD.
"""

import sys
import os
import re
import ssl
import requests
import pdfplumber
from datetime import datetime, date
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, init_db
from backend.crud import bulk_insert_resultados
from backend.models import Resultado, Base

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

PDF_URLS = {
    "Pick 3": "https://files.floridalottery.com/exptkt/p3.pdf",
    "Pick 4": "https://files.floridalottery.com/exptkt/p4.pdf",
}

PDF_PATHS = {
    "Pick 3": os.path.join(DATA_DIR, "p3.pdf"),
    "Pick 4": os.path.join(DATA_DIR, "p4.pdf"),
}

# Regex patterns for extracting results
# Format: MM/DD/YY E/M d- d- d(- d) FB# 
PATTERN_PICK3 = re.compile(
    r"(\d{2}/\d{2}/\d{2})\s+([EM])\s+(\d)\s*-\s*(\d)\s*-\s*(\d)(?:\s+FB\d)?"
)
PATTERN_PICK4 = re.compile(
    r"(\d{2}/\d{2}/\d{2})\s+([EM])\s+(\d)\s*-\s*(\d)\s*-\s*(\d)\s*-\s*(\d)(?:\s+FB\s*\d)?"
)


class _LegacySSLAdapter(HTTPAdapter):
    """Adapter that uses a more permissive SSL context for legacy servers."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


_session = None


def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.mount("https://", _LegacySSLAdapter())
    return _session


def descargar_pdf(url: str, path: str) -> bool:
    """Descarga el PDF y lo guarda sobrescribiendo el anterior.
    Si falla la descarga, usa el archivo local existente si hay uno."""
    print(f"  Descargando {url}...")
    try:
        resp = _get_session().get(url, timeout=30, stream=True)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  Guardado en {path} ({os.path.getsize(path)} bytes)")
        return True
    except Exception:
        if os.path.exists(path):
            print(f"  Sin conexión — usando archivo local: {path}")
            return True
        print(f"  [ERROR] No se pudo descargar {url} y no hay archivo local")
        return False


def parsear_fecha(mmddyy: str):
    """Convierte MM/DD/YY a objeto date."""
    try:
        dt = datetime.strptime(mmddyy.strip(), "%m/%d/%y")
        if dt.year > 2030:
            dt = dt.replace(year=dt.year - 100)
        return dt.date()
    except ValueError:
        return None


def extraer_resultados_pdf(pdf_path: str, juego: str) -> list[dict]:
    """Extrae resultados del PDF usando pdfplumber."""
    pattern = PATTERN_PICK4 if juego == "Pick 4" else PATTERN_PICK3
    
    resultados = []
    vistos = set()
    
    print(f"  Procesando {pdf_path}...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                for match in pattern.finditer(text):
                    fecha_str = match.group(1)
                    sorteo = match.group(2)
                    n1 = int(match.group(3))
                    n2 = int(match.group(4))
                    n3 = int(match.group(5))
                    n4 = int(match.group(6)) if juego == "Pick 4" else None
                    
                    fecha = parsear_fecha(fecha_str)
                    if not fecha:
                        continue
                    
                    key = (fecha, juego, sorteo)
                    if key in vistos:
                        continue
                    vistos.add(key)
                    
                    resultado = {
                        "fecha": fecha,
                        "juego": juego,
                        "sorteo": sorteo,
                        "n1": n1,
                        "n2": n2,
                        "n3": n3,
                    }
                    if n4 is not None:
                        resultado["n4"] = n4
                    
                    resultados.append(resultado)
        
        print(f"  Extraídos {len(resultados)} resultados únicos")
        return resultados
    
    except Exception as e:
        print(f"  ERROR procesando PDF: {e}")
        return []


def importar_juego(juego: str):
    print(f"\n=== Importando {juego} ===")
    
    # Descargar PDF (sobrescribe si existe)
    pdf_path = PDF_PATHS[juego]
    if not descargar_pdf(PDF_URLS[juego], pdf_path):
        return 0
    
    # Extraer resultados
    resultados = extraer_resultados_pdf(pdf_path, juego)
    if not resultados:
        return 0
    
    # Insertar en BD
    db = SessionLocal()
    try:
        bulk_insert_resultados(db, resultados)
        print(f"  Insertados/actualizados {len(resultados)} registros")
    except Exception as e:
        db.rollback()
        print(f"  ERROR en BD: {e}")
        return 0
    finally:
        db.close()
    
    return len(resultados)


def main():
    print("=== Importador de Históricos Florida Lottery (PDF) ===")
    print("Inicializando BD...")
    init_db()
    
    # Asegurar directorio data
    os.makedirs(DATA_DIR, exist_ok=True)
    
    total = 0
    for juego in ["Pick 3", "Pick 4"]:
        total += importar_juego(juego)
    
    print(f"\nOK - Importacion completa. Total: {total} registros")


if __name__ == "__main__":
    main()