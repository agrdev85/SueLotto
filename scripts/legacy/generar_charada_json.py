"""
Genera data/charada.json enriquecido desde un dump SQL de la tabla charada.
Formato esperado: INSERT INTO charada (numero, significado, categoria) VALUES ...
Uso: python scripts/generar_charada_json.py [ruta_sql_dump]
"""

import re
import json
import sys
from pathlib import Path

CATEGORY_KEYWORDS = {
    "animales": {
        "caballo", "yegua", "corcel", "potro", "gallo", "gallina", "perro", "can", "cachorro",
        "canino", "sabueso", "gato", "felino", "minino", "micho", "gata", "pájaro", "ave",
        "gorrión", "canario", "jilguero", "pescado", "pez", "sardina", "salmón", "trucha",
        "serpiente", "culebra", "reptil", "víbora", "boa", "toro", "buey", "astado", "bovino",
        "vaca", "res", "ternera", "ganado", "vacuno", "lechera", "cerdo", "puerco", "cochino",
        "marrano", "chancho", "oveja", "borrego", "carnero", "lanar", "rebaño", "león", "tigre",
        "tigresa", "leona", "mono", "simio", "primate", "chango", "mico", "elefante", "paquidermo",
        "mamífero", "trompa", "marfil", "cabra", "chivo", "caprino", "cabrío", "chiva",
        "ratón", "roedor", "laucha", "campañol", "topo", "caracol", "molusco", "concha", "baboso",
        "mariposa", "palomilla", "lepidóptero", "polilla", "escorpión", "alacrán", "arácnido",
        "aguijón", "abeja", "colmena", "miel", "insecto", "zángano", "vaquilla",
    },
    "naturaleza": {
        "sol", "astro", "luna", "satélite", "noche", "cielo", "nocturno", "árbol", "planta",
        "tronco", "madera", "bosque", "flor", "rosa", "lirio", "margarita", "girasol",
        "río", "caudal", "corriente", "arroyo", "afluente", "lluvia", "aguacero", "chaparrón",
        "diluvio", "tormenta", "viento", "brisa", "ventarrón", "ráfaga", "huracán",
        "montaña", "sierra", "cerro", "cordillera", "pico", "firmamento", "cosmos", "espacio",
        "universo", "estrella", "luminaria", "constelación", "nube", "cúmulo", "niebla", "vapor",
        "bruma", "relámpago", "rayo", "centella", "chispa", "fogonazo", "trueno", "estruendo",
        "retumbo", "estampido", "arcoíris", "iris", "espectro", "volcán", "lava",
    },
    "elementos": {
        "fuego", "llama", "incendio", "hoguera", "brasas", "agua", "mar", "manantial",
        "tierra", "suelo", "terreno", "superficie", "planeta", "aire", "oxígeno", "atmósfera",
        "lago", "laguna", "océano", "ola",
    },
    "espiritual": {
        "muerto", "difunto", "fallecido", "cadáver", "tumba", "muerte", "deceso", "final",
        "óbito", "diablo", "satanás", "demonio", "lucifer", "maligno", "belcebú",
        "santo", "bendito", "sagrado", "divino", "celestial", "ángel", "querubín",
        "arcángel", "espíritu", "endemoniado", "maldito", "condenado", "alma", "fantasma",
        "espíritu", "oración", "milagro", "fe",
    },
    "objetos": {
        "dinero", "plata", "billete", "moneda", "fortuna", "cash", "carta", "mensaje",
        "correspondencia", "correo", "misiva", "auto", "carro", "coche", "automóvil",
        "vehículo", "avión", "aeroplano", "aeronave", "jet", "nave", "barco", "embarcación",
        "navío", "buque", "velero", "tren", "ferrocarril", "metro", "locomotora", "vagón",
        "sombrero", "gorro", "gorra", "tocado", "visera", "zapato", "calzado", "tenis",
        "sandalia", "mocasín", "ropa", "vestimenta", "prenda", "atuendo", "vestuario",
        "anillo", "aro", "sortija", "argolla", "círculo", "corona", "diadema", "cetro",
        "guirnalda", "insignia", "espada", "sable", "cuchillo", "daga", "estoque",
        "escudo", "amparo", "protección", "resguardo", "defensa", "llave", "abrelatas",
        "abridor", "clave", "acceso", "candado", "cerrojo", "seguro", "cerradura",
        "pestillo", "reloj", "cronómetro", "despertador", "hora", "tiempo",
        "teléfono", "celular", "móvil", "smartphone", "aparato", "espejo", "cristal",
        "vidrio", "reflejo", "retrovisor", "llavero", "maleta", "bolsa",
    },
    "sentimientos": {
        "tristeza", "melancolía", "llanto", "pena", "dolor", "amor", "cariño", "afecto",
        "pasión", "romance", "pesadilla", "pesadumbre", "angustia", "zozobra", "congoja",
        "alegría", "felicidad", "gozo", "placer", "dicha", "odio", "rencor", "ira",
        "miedo", "temor", "pánico", "esperanza", "ilusión", "nostalgia", "ternura",
    },
    "lugares": {
        "casa", "hogar", "vivienda", "residencia", "domicilio", "iglesia", "templo",
        "capilla", "catedral", "santuario", "cementerio", "camposanto", "panteón",
        "sepulcro", "mausoleo", "cárcel", "prisión", "presidio", "penal", "penitenciaría",
        "hospital", "clínica", "sanatorio", "dispensario", "escuela", "colegio", "academia",
        "instituto", "universidad", "parque", "jardín", "plaza", "pradera", "prado",
        "playa", "costa", "litoral", "orilla", "balneario", "calle", "avenida", "barrio",
        "ciudad", "pueblo", "aldea", "país", "cabaña", "castillo", "palacio",
    },
    "comida": {
        "pan", "harina", "masa", "bollo", "hogaza", "comida", "alimento", "vianda",
        "nutrición", "cena", "bebida", "trago", "copa", "brebaje", "cerveza", "vino",
        "sopa", "caldo", "crema", "consomé", "menestra", "arroz", "grano", "paella",
        "risotto", "cereal", "frijoles", "legumbres", "porotos", "habichuelas", "vainitas",
        "fruta", "verdura", "carne", "pollo", "huevo", "leche", "queso", "mantequilla",
        "aceite", "sal", "azúcar", "café", "té", "chocolate", "dulce", "pastel",
    },
    "personas": {
        "enfermo", "paciente", "doliente", "convaleciente", "herido", "mujer", "dama",
        "señora", "hembra", "fémina", "hombre", "varón", "caballero", "macho", "señor",
        "niño", "infante", "pequeño", "chico", "bebé", "nene", "bruja", "hechicera",
        "maga", "embrujadora", "pitonisa", "rey", "monarca", "soberano", "emperador",
        "majestad", "reina", "soberana", "emperatriz", "príncipe", "heredero",
        "sucesor", "princesa", "heredera", "sucesora", "guerrero", "soldado", "luchador",
        "combatiente", "gladiador", "amigo", "enemigo", "vecino", "familia", "hermano",
    },
    "profesiones": {
        "médico", "doctor", "galeno", "facultativo", "cirujano", "maestro", "profesor",
        "abogado", "juez", "policía", "bombero", "carpintero", "albañil", "mecánico",
        "electricista", "plomero", "pintor", "escritor", "artista", "músico", "cantante",
        "bailarín", "cocinero", "mesero", "piloto", "conductor", "dependiente", "vendedor",
    },
    "eventos": {
        "matrimonio", "boda", "unión", "casamiento", "nupcias", "fiesta", "celebración",
        "festejo", "party", "parranda", "cumpleaños", "aniversario", "funeral", "velorio",
        "entierro", "graduación", "baile", "concierto", "reunión", "cita", "encuentro",
        "despedida", "llegada", "viaje", "paseo",
    },
    "conceptos": {
        "suerte", "azar", "destino", "hado", "trabajo", "empleo", "labor", "oficio",
        "ocupación", "sueño", "anhelo", "deseo", "fantasía", "gloria", "fama", "celebridad",
        "renombre", "honra", "victoria", "triunfo", "éxito", "logro", "conquista",
        "guerra", "conflicto", "batalla", "contienda", "combate", "paz", "armonía",
        "tranquilidad", "serenidad", "calma", "libertad", "justicia", "verdad",
        "mentira", "tiempo", "vida", "sabiduría", "conocimiento", "educación",
    },
}

STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "e",
    "que", "es", "con", "en", "por", "para", "se", "su", "al", "lo", "como",
    "más", "pero", "sus", "le", "ya", "este", "entre", "porque", "donde",
    "cuando", "muy", "sin", "sobre", "todo", "tan", "era", "son", "fue",
    "ser", "han", "hay", "aquel", "esa", "eso", "mis", "nos", "les",
}


def inferir_categoria(significado: str) -> str:
    palabras = re.sub(r"[^\w\sáéíóúñ]", " ", significado.lower()).split()
    categorias_puntaje = {}
    for palabra in palabras:
        if palabra in STOPWORDS:
            continue
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if palabra in keywords:
                categorias_puntaje[cat] = categorias_puntaje.get(cat, 0) + 1
    if categorias_puntaje:
        return max(categorias_puntaje, key=categorias_puntaje.get)
    return "general"


def extraer_palabras_clave(significados: list[str]) -> list[str]:
    palabras = set()
    for sig in significados:
        tokens = re.sub(r"[^\w\sáéíóúñ]", " ", sig.lower()).split()
        for t in tokens:
            if t not in STOPWORDS and len(t) > 2:
                palabras.add(t)
    return sorted(palabras)


def parse_sql_dump(ruta: str) -> list[dict]:
    with open(ruta, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"INSERT\s+INTO\s+charada\s*[^)]*?\s*VALUES\s*\((\d+),\s*'([^']+)',\s*'([^']*)'"
    matches = re.findall(pattern, content, re.IGNORECASE)

    if not matches:
        pattern2 = r"\((\d+),\s*'([^']+)'(?:,\s*'([^']*)')?"
        matches = re.findall(pattern2, content)

    entries = {}
    for match in matches:
        num = int(match[0])
        sig = match[1].strip()
        cat = match[2].strip() if len(match) > 2 and match[2] else ""
        if num not in entries:
            entries[num] = {"significados": set(), "categoria": cat}
        entries[num]["significados"].add(sig)

    result = []
    for num in sorted(entries.keys()):
        entry = entries[num]
        significados = list(entry["significados"])
        cat = entry["categoria"] if entry["categoria"] else inferir_categoria(" ".join(significados))
        result.append({
            "numero": num,
            "significados": significados,
            "categoria": cat,
            "palabras_clave": extraer_palabras_clave(significados),
        })

    return result


def generar_json_desde_sql(ruta_sql: str, ruta_salida: str = "data/charada.json"):
    print(f"📄 Parseando {ruta_sql}...")
    data = parse_sql_dump(ruta_sql)
    if not data:
        print("⚠️  No se encontraron datos en el SQL. Usando datos de ejemplo...")
        return
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Generado {ruta_salida} con {len(data)} entradas")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/generar_charada_json.py <ruta_sql_dump>")
        print("Ejemplo: python scripts/generar_charada_json.py data/charada_dump.sql")
        sys.exit(1)
    generar_json_desde_sql(sys.argv[1])
