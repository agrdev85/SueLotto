from sqlalchemy import Column, Integer, String, Date, Text, Float, DateTime, UniqueConstraint, Boolean
from sqlalchemy.sql import func
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
    significados = Column(Text, nullable=False)
    categoria = Column(String(50), nullable=True)
    palabras_clave = Column(Text, nullable=True)


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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    tier = Column(String(20), nullable=False, default="free")
    tier_expires = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(200), nullable=True)
    password_reset_token = Column(String(200), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)


class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    fecha = Column(Date, nullable=False)
    turno = Column(String(20), nullable=True)
    juego = Column(String(10), nullable=False)
    numeros = Column(String(50), nullable=False)
    fijo = Column(String(10), nullable=True)
    corrido = Column(String(10), nullable=True)
    parle = Column(String(10), nullable=True)
    candado = Column(String(10), nullable=True)
    precio = Column(Float, nullable=True)
    descripcion = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class UserUsage(Base):
    __tablename__ = "user_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    fecha = Column(Date, nullable=False)
    charada_count = Column(Integer, default=0)
    busquedas_count = Column(Integer, default=0)
    historica_count = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", "fecha", name="uq_user_usage"),
    )


class OtherGameResult(Base):
    __tablename__ = "other_games"

    id = Column(Integer, primary_key=True, index=True)
    game_name = Column(String(50), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    numbers = Column(String(200), nullable=False)
    extra = Column(String(100), nullable=True)
    drawing_date = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("game_name", "fecha", name="uq_other_game"),
    )
