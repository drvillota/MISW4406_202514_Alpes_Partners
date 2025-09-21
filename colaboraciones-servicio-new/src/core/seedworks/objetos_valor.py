"""Objetos valor base para colaboraciones con influencers

En este archivo se definen objetos de valor reutilizables 
para contratos y colaboraciones en el dominio de marketing/influencers.

"""

from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import date, datetime

@dataclass(frozen=True)
class ObjetoValor:
    ...

@dataclass(frozen=True)
class Identificador(ObjetoValor):
    codigo: UUID

    def __post_init__(self):
        if not isinstance(self.codigo, UUID):
            raise ValueError("El identificador debe ser un UUID válido")

    @staticmethod
    def nuevo():
        return Identificador(uuid4())

# Email de contacto de un creador o agencia
@dataclass(frozen=True)
class Email(ObjetoValor):
    direccion: str
    
    def __post_init__(self):
        if "@" not in self.direccion:
            raise ValueError("Email debe contener @")


# Estados de un contrato/colaboración
@dataclass(frozen=True)
class EstadoColaboracion(ObjetoValor):
    valor: str
    
    def __post_init__(self):
        estados_validos = ["VIGENTE", "FINALIZADA", "CANCELADA"]
        if self.valor not in estados_validos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {estados_validos}")

# Estados de una campaña
@dataclass(frozen=True)
class EstadoCampania(ObjetoValor):
    valor: str
    
    def __post_init__(self):
        estados_validos = ["NUEVA", "ACTIVA", "FINALIZADA"]
        if self.valor not in estados_validos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {estados_validos}")

# Estados de un contrato
@dataclass(frozen=True)
class EstadoContrato(ObjetoValor):
    valor: str
    
    def __post_init__(self):
        estados_validos = ["PENDIENTE", "FIRMADO", "CANCELADO"]
        if self.valor not in estados_validos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {estados_validos}")


# Fechas de inicio y fin de contratos
@dataclass(frozen=True)
class Periodo(ObjetoValor):
    inicio: date
    fin: date
    
    def __post_init__(self):
        if self.inicio >= self.fin:
            raise ValueError("La fecha de inicio debe ser anterior a la de fin")

@dataclass(frozen=True)
class RedSocial(ObjetoValor):
    nombre: str

    def __post_init__(self):
        if not self.nombre or len(self.nombre.strip()) == 0:
            raise ValueError("El nombre de la red social es requerido")

@dataclass(frozen=True)
class IdentidadEnRed(ObjetoValor):
    red: RedSocial
    nickname: str

    def __post_init__(self):
        if not self.nickname or len(self.nickname.strip()) == 0:
            raise ValueError("El nickname es requerido para la identidad en red")

@dataclass(frozen=True)
class NombreCampania(ObjetoValor):
    valor: str

    def __post_init__(self):
        if not self.valor or len(self.valor.strip()) == 0:
            raise ValueError("El nombre de la campaña no puede estar vacío")

@dataclass(frozen=True)
class Publicacion(ObjetoValor):
    url: str
    red: RedSocial
    fecha: date

    def __post_init__(self):
        if not self.url or not self.url.startswith("http"):
            raise ValueError("La publicación debe tener una URL válida")