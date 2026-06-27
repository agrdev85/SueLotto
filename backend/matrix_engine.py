MATRIZ_NUEVA = [
    [ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10],
    [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
    [31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
    [41, 42, 43, 44, 45, 46, 47, 48, 49, 50],
    [51, 52, 53, 54, 55, 56, 57, 58, 59, 60],
    [61, 62, 63, 64, 65, 66, 67, 68, 69, 70],
    [71, 72, 73, 74, 75, 76, 77, 78, 79, 80],
    [81, 82, 83, 84, 85, 86, 87, 88, 89, 90],
    [91, 92, 93, 94, 95, 96, 97, 98, 99,100],
]

MATRIZ_VIEJA = [
    [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10],
    [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
    [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
    [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
    [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54],
    [55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65],
    [66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76],
    [77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87],
    [88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98],
    [99,100,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
]

DIRECCIONES = [
    (-1,  0),  # N
    (-1,  1),  # NE
    ( 0,  1),  # E
    ( 1,  1),  # SE
    ( 1,  0),  # S
    ( 1, -1),  # SW
    ( 0, -1),  # W
    (-1, -1),  # NW
]

MATRICES = {
    "nueva": MATRIZ_NUEVA,
    "vieja": MATRIZ_VIEJA,
}


def _obtener_matriz(tipo_matriz: str) -> list[list[int]]:
    matriz = MATRICES.get(tipo_matriz)
    if matriz is None:
        raise ValueError(f"Tipo de matriz inválido: {tipo_matriz}. Usa 'nueva' o 'vieja'.")
    return matriz


def _encontrar_posicion(matriz: list[list[int]], numero: int) -> tuple[int, int]:
    for fila in range(len(matriz)):
        for col in range(len(matriz[0])):
            if matriz[fila][col] == numero:
                return fila, col
    raise ValueError(f"Número {numero} no encontrado en la matriz")


def _recorrer_direccion(matriz: list[list[int]], fila: int, col: int, df: int, dc: int) -> list[int]:
    filas, cols = len(matriz), len(matriz[0])
    numeros = []
    f, c = fila + df, col + dc
    while 0 <= f < filas and 0 <= c < cols:
        valor = matriz[f][c]
        if valor == 0:
            break
        numeros.append(valor)
        f += df
        c += dc
    return numeros


def obtener_numeros_alrededor(numero: int, tipo_matriz: str = "nueva") -> list[int]:
    matriz = _obtener_matriz(tipo_matriz)
    fila, col = _encontrar_posicion(matriz, numero)

    vistos = {numero}
    resultado = [numero]

    for df, dc in DIRECCIONES:
        for n in _recorrer_direccion(matriz, fila, col, df, dc):
            if n not in vistos:
                vistos.add(n)
                resultado.append(n)

    return resultado


def procesar_secuencia(secuencia: list[int], tipo_matriz: str = "nueva") -> list[int]:
    if not 1 <= len(secuencia) <= 3:
        raise ValueError("La secuencia debe tener entre 1 y 3 números")
    for n in secuencia:
        if tipo_matriz == "nueva" and not (1 <= n <= 100):
            raise ValueError(f"Número {n} fuera de rango para matriz nueva (1-100)")
        if tipo_matriz == "vieja" and not (0 <= n <= 100):
            raise ValueError(f"Número {n} fuera de rango para matriz vieja (0-100)")

    vistos = set()
    resultado = []
    for n in secuencia:
        for alrededor in obtener_numeros_alrededor(n, tipo_matriz):
            if alrededor not in vistos:
                vistos.add(alrededor)
                resultado.append(alrededor)

    return resultado


def comparar_y_reducir(
    secuencia: list[int],
    tipo_matriz: str = "nueva",
    calientes: list[int] = None,
    posibles: list[int] = None,
) -> dict:
    alrededor = procesar_secuencia(secuencia, tipo_matriz)
    calientes = calientes or []
    posibles = posibles or []

    set_calientes = set(calientes)
    set_posibles = set(posibles)
    set_ambos = set_calientes & set_posibles
    set_alrededor = set(alrededor)

    interseccion_calientes = sorted(set_alrededor & set_calientes, key=lambda x: alrededor.index(x))
    interseccion_posibles = sorted(set_alrededor & set_posibles, key=lambda x: alrededor.index(x))
    interseccion_ambos = sorted(set_alrededor & set_ambos, key=lambda x: alrededor.index(x))
    discriminante = sorted(set_alrededor - set_calientes - set_posibles, key=lambda x: alrededor.index(x))

    return {
        "alrededor": alrededor,
        "calientes": calientes,
        "posibles": posibles,
        "interseccion_calientes": interseccion_calientes,
        "interseccion_posibles": interseccion_posibles,
        "interseccion_ambos": interseccion_ambos,
        "discriminante": discriminante,
        "total_alrededor": len(alrededor),
        "total_interseccion_calientes": len(interseccion_calientes),
        "total_interseccion_posibles": len(interseccion_posibles),
        "total_interseccion_ambos": len(interseccion_ambos),
        "total_discriminante": len(discriminante),
    }
