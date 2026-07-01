from pydantic import BaseModel
from typing import Optional
from datetime import date


class ResultadoBase(BaseModel):
    fecha: date
    juego: str
    sorteo: str
    n1: int
    n2: int
    n3: int
    n4: Optional[int] = None


class ResultadoCreate(ResultadoBase):
    pass


class ResultadoResponse(ResultadoBase):
    id: int

    class Config:
        from_attributes = True


class CharadaBase(BaseModel):
    numero: int
    significado: str
    categoria: Optional[str] = None


class CharadaResponse(CharadaBase):
    id: int

    class Config:
        from_attributes = True


class CharadaSearchResult(BaseModel):
    palabra: str
    numero: int
    significado: str
    posicion: int


class CharadaSearchResponse(BaseModel):
    texto_original: str
    resultados: list[CharadaSearchResult]


class AdivinanzaBase(BaseModel):
    fecha: date
    texto: str


class AdivinanzaResponse(AdivinanzaBase):
    id: int

    class Config:
        from_attributes = True


class AdivinanzaAnalisisRequest(BaseModel):
    adivinanza: str
    interpretacion: str


class AdivinanzaAnalisisResponse(BaseModel):
    sugerencias: list[dict]
    razonamiento: str


class FrecuenciaResponse(BaseModel):
    numero: int
    frecuencia: int
    porcentaje: float


class AtrasadoResponse(BaseModel):
    numero: int
    dias_sin_salir: int


class PrediccionResponse(BaseModel):
    numero: int
    probabilidad: float


class PrediccionesResponse(BaseModel):
    juego: str
    sorteo: str
    predicciones: list[PrediccionResponse]


class ResultadoHistoricoFilter(BaseModel):
    juego: Optional[str] = None
    sorteo: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    contienen_digitos: Optional[str] = None
    page: int = 1
    size: int = 50


class MatrizRequest(BaseModel):
    numero: int
    tipo_matriz: str = "nueva"


class SecuenciaRequest(BaseModel):
    secuencia: list[int]
    tipo_matriz: str = "nueva"


class CompararRequest(BaseModel):
    secuencia: list[int]
    tipo_matriz: str = "nueva"
    calientes: list[int] = []
    posibles: list[int] = []
    juego: Optional[str] = None
    sorteo: Optional[str] = None


class AlrededorResponse(BaseModel):
    numero: int
    tipo_matriz: str
    numeros: list[int]
    total: int


class SecuenciaResponse(BaseModel):
    secuencia: list[int]
    tipo_matriz: str
    numeros: list[int]
    total: int


class CompararResponse(BaseModel):
    secuencia: list[int]
    tipo_matriz: str
    alrededor: list[int]
    calientes: list[int]
    posibles: list[int]
    interseccion_calientes: list[int]
    interseccion_posibles: list[int]
    interseccion_ambos: list[int]
    discriminante: list[int]
    total_alrededor: int
    total_interseccion_calientes: int
    total_interseccion_posibles: int
    total_interseccion_ambos: int
    total_discriminante: int
    discriminante_scored: list[dict] = []


class NumeroScore(BaseModel):
    numero: int
    score: float
    frecuencia: int
    dias_sin_salir: int
    probabilidad_ml: float


class CalientesResponse(BaseModel):
    juego: str
    sorteo: Optional[str]
    limite: int
    dias: int
    numeros: list[int]
    frecuencias: dict[str, int]


class PosiblesSalirResponse(BaseModel):
    fecha: str
    numeros: list[int]
    sorteo: str


class CharadaEnriquecidaResponse(BaseModel):
    numero: int
    significados: list[str]
    categoria: str
    palabras_clave: list[str]
