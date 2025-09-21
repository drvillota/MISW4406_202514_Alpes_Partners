"""Objetos valor del dominio de cliente

En este archivo usted encontrará los objetos valor del dominio de cliente

"""

from datetime import datetime
from enum import Enum
from seedwork.dominio.objetos_valor import ObjetoValor, Ciudad
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Nombre(ObjetoValor):
    nombres: str
    apellidos: str


@dataclass(frozen=True)
class Fecha(ObjetoValor):
    valor: datetime


@dataclass(frozen=True)
class Marca(ObjetoValor):
    nombre: str
    tipo: str


@dataclass(frozen=True)
class Email(ObjetoValor):
    address: str
    dominio: str
    es_empresarial: bool


@dataclass(frozen=True)
class Redes(ObjetoValor):
    nombre: str
    usuario: str
    seguidores: int


@dataclass(frozen=True)
class Nicho(ObjetoValor):
    nombre: str
    descripcion: str


class EstadoColaboracion(Enum):
    # Mantengo valores en MAYÚSCULAS (coherente con tu Enum actual).
    INICIADO = "INICIADO"
    CANCELADO = "CANCELADO"
    FINALIZADO = "FINALIZADO"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Contrato(ObjetoValor):
    url: str
    fecha_validacion: datetime | None = None
    fecha_finalizacion: datetime | None = None
    fecha_rechazo: datetime | None = None
    # Evitar evaluar datetime.utcnow() en import; usar default_factory
    fecha_creacion: datetime = field(default_factory=datetime.utcnow)


# --- IDs: exponemos `.id` y __str__ para compatibilidad con el resto del código/tests ---

@dataclass(frozen=True)
class InfluencerId(ObjetoValor):
    id: str

    def __post_init__(self):
        if not self.id:
            raise ValueError("El InfluencerId no puede estar vacío")

@dataclass(frozen=True)
class CampaniaId(ObjetoValor):
    id: str

    def __post_init__(self):
        if not self.id:
            raise ValueError("El CampaniaId no puede estar vacío")
