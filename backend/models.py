from sqlalchemy import Column, Integer, String, Date, Text, UniqueConstraint
from backend.database import Base


class Resultado(Base):
    __tablename__ = "resultados"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    juego = Column(String(10), nullable=False, index=True)
    sorteo = Column(String(1), nullable=False)
    n1 = Column(Integer, nullable=False)
    n2 = Column(Integer, nullable=False)
    n3 = Column(Integer, nullable=False)
    n4 = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("fecha", "juego", "sorteo", name="uq_resultado"),
    )


class Charada(Base):
    __tablename__ = "charada"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, nullable=False, unique=True, index=True)
    significado = Column(String(200), nullable=False)
    categoria = Column(String(50), nullable=True)


class Adivinanza(Base):
    __tablename__ = "adivinanzas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True, index=True)
    texto = Column(Text, nullable=False)


class PosibleSalir(Base):
    __tablename__ = "posible_salir"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    sorteo = Column(String(1), nullable=False)
    numeros = Column(String(200), nullable=False)

    __table_args__ = (
        UniqueConstraint("fecha", "sorteo", name="uq_posible_salir"),
    )
