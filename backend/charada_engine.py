import re
import json
import os
from collections import Counter
from sqlalchemy.orm import Session
from backend.models import Charada


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
    "religion": {
        "dios", "jesús", "cristo", "virgen", "maría", "santo", "santa", "biblia", "evangelio",
        "iglesia", "templo", "capilla", "catedral", "santuario", "oración", "rezar", "fe",
        "creencia", "devoción", "milagro", "sagrado", "divino", "celestial", "bendito",
        "ángel", "arcángel", "querubín", "serafín", "apóstol", "discípulo", "profeta",
        "salvador", "redentor", "paraíso", "cielo", "infierno", "purgatorio", "pecado",
    },
    "ocultismo": {
        "bruja", "hechicera", "maga", "embrujadora", "pitonisa", "hechizo", "conjuro",
        "maleficio", "encantamiento", "maldición", "sortilegio", "vudú", "santería",
        "palero", "babalawo", "orisha", "santos", "maya", "espiritismo", "médium",
        "tabla", "ouija", "esoterismo", "hermetismo", "misticismo",
    },
    "esoterismo": {
        "tarot", "cartas", "baraja", "astrología", "horóscopo", "zodiaco", "signo",
        "aura", "chakra", "energía", "vibración", "karma", "reencarnación", "meditación",
        "yoga", "arcano", "runas", "numerología", "profecía", "oráculo", "predictivo",
        "adivinación", "clarividencia", "premonición", "presagio",
    },
    "espiritual": {
        "muerto", "difunto", "fallecido", "cadáver", "tumba", "muerte", "deceso", "final",
        "óbito", "alma", "espíritu", "fantasma", "espectro", "aparición", "ultratumba",
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
        "niño", "infante", "pequeño", "chico", "bebé", "nene", "rey", "monarca",
        "soberano", "emperador", "majestad", "reina", "soberana", "emperatriz",
        "príncipe", "heredero", "sucesor", "princesa", "heredera", "sucesora",
        "guerrero", "soldado", "luchador", "combatiente", "gladiador", "amigo",
        "enemigo", "vecino", "familia", "hermano",
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


def inferir_categoria(significados: list[str]) -> str:
    texto = " ".join(significados)
    palabras = re.sub(r"[^\w\sáéíóúñ]", " ", texto.lower()).split()
    puntajes = {}
    for palabra in palabras:
        if palabra in STOPWORDS:
            continue
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if palabra in keywords:
                puntajes[cat] = puntajes.get(cat, 0) + 1
    if puntajes:
        return max(puntajes, key=puntajes.get)
    return "general"


def extraer_palabras_clave(significados: list[str], top_n: int = 15) -> list[str]:
    tokens = []
    for sig in significados:
        palabras = re.sub(r"[^\w\sáéíóúñ]", " ", sig.lower()).split()
        for t in palabras:
            if t not in STOPWORDS and len(t) > 2:
                tokens.append(t)
    conteo = Counter(tokens)
    return [palabra for palabra, _ in conteo.most_common(top_n)]


def cargar_charada_json(path: str = "data/charada.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def poblar_charada_db(db: Session, path: str = "data/charada.json"):
    data = cargar_charada_json(path)
    count = 0
    for entry in data:
        existing = db.query(Charada).filter(Charada.numero == entry["numero"]).first()
        if not existing:
            db.add(Charada(
                numero=entry["numero"],
                significados=json.dumps(entry["significados"], ensure_ascii=False),
                categoria=inferir_categoria(entry["significados"]),
                palabras_clave=json.dumps(
                    entry.get("palabras_clave", extraer_palabras_clave(entry["significados"])),
                    ensure_ascii=False
                ),
            ))
            count += 1
    db.commit()
    return count


def _normalize(word: str) -> str:
    """Remove accents and lowercase."""
    accents = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")
    return word.lower().translate(accents)


def _build_maps(all_entries):
    """
    Build lookup maps with priority:
      1. primary_exact: first significado (primary) exact phrase match
      2. exact: any significado exact phrase match
      3. primary_word: word from primary significado
      4. word: any word from any significado
    """
    primary_exact = {}
    exact = {}
    primary_word = {}
    word_map = {}

    for c in all_entries:
        significados = json.loads(c.significados)
        for idx, sig in enumerate(significados):
            sig_norm = _normalize(sig)
            is_primary = idx == 0

            if sig_norm not in exact:
                exact[sig_norm] = c
            if is_primary and sig_norm not in primary_exact:
                primary_exact[sig_norm] = c

            for word in sig_norm.split():
                w = word.strip()
                if w and w not in STOPWORDS:
                    if w not in word_map:
                        word_map[w] = (c, sig_norm, is_primary)
                    if is_primary and w not in primary_word:
                        primary_word[w] = (c, sig_norm)

    return {
        "primary_exact": primary_exact,
        "exact": exact,
        "primary_word": primary_word,
        "word": word_map,
    }


def buscar_en_sueno(db: Session, texto: str) -> list[dict]:
    texto_limpio = re.sub(r"[^\w\sáéíóúñÁÉÍÓÚÑ]", " ", texto.lower())
    palabras = texto_limpio.split()

    all_entries = db.query(Charada).all()
    maps = _build_maps(all_entries)

    resultados = []
    seen_numbers = set()
    i = 0
    while i < len(palabras):
        palabra = palabras[i]
        palabra_norm = _normalize(palabra)
        if not palabra_norm or palabra_norm in STOPWORDS:
            i += 1
            continue

        entry = None
        matched_sig = None
        skip = 1

        # Priority 1: multi-word exact phrase match (try longest first)
        for end in range(min(i + 4, len(palabras) - 1), i, -1):
            phrase = " ".join(_normalize(palabras[j]) for j in range(i, end + 1))
            if phrase in maps["primary_exact"]:
                entry = maps["primary_exact"][phrase]
                matched_sig = phrase
                skip = end - i + 1
                break
            if phrase in maps["exact"]:
                entry = maps["exact"][phrase]
                matched_sig = phrase
                skip = end - i + 1
                break

        if not entry and palabra_norm in maps["primary_exact"]:
            entry = maps["primary_exact"][palabra_norm]
            matched_sig = palabra_norm
        elif not entry and palabra_norm in maps["exact"]:
            entry = maps["exact"][palabra_norm]
            matched_sig = palabra_norm
        elif not entry and palabra_norm in maps["primary_word"]:
            entry, matched_sig = maps["primary_word"][palabra_norm]
        elif not entry and palabra_norm in maps["word"]:
            entry, matched_sig, _ = maps["word"][palabra_norm]

        if entry and entry.numero not in seen_numbers:
            seen_numbers.add(entry.numero)
            resultados.append({
                "palabra": palabras[i],
                "numero": entry.numero,
                "significado": json.loads(entry.significados)[0],
                "categoria": entry.categoria,
                "posicion": i,
            })

        i += skip

    return resultados


def generar_combinacion_por_orden(resultados: list[dict]) -> str:
    numeros = [str(r["numero"]) for r in resultados]
    if len(numeros) >= 3:
        return "-".join(numeros[:3])
    elif len(numeros) == 2:
        return "-".join(numeros) + "-" + numeros[0]
    elif len(numeros) == 1:
        return numeros[0] + "-" + numeros[0] + "-" + numeros[0]
    return ""
