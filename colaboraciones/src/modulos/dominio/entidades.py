"""Entidades del dominio de colaboraciones

En este archivo usted encontrará las entidades del dominio de colaboraciones

"""

from datetime import datetime
import uuid
from dataclasses import dataclass, field

from seedwork.dominio.entidades import Entidad, AgregacionRaiz

from .objetos_valor import (
    InfluencerId,
    CampaniaId,
    Contrato,
    EstadoColaboracion,
    Marca,
    Nicho,
    Redes,
    Nombre,
    Email,
    Fecha,
)


@dataclass
class Campania(Entidad):
    nombre: Nombre = field(default_factory=Nombre)
    marca: Marca = field(default_factory=Marca)
    fecha_inicio: Fecha = field(default_factory=Fecha)
    fecha_fin: Fecha = field(default_factory=Fecha)
    nicho: Nicho = field(default_factory=Email)


@dataclass
class CreadorContenido(Entidad):
    nombre: Nombre = field(default_factory=Nombre)
    redes: list[Redes] = field(default_factory=list)
    email: Email = field(default_factory=Email)


@dataclass
class Colaboracion(AgregacionRaiz):
    # id público de la agregación (string UUID)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    id_campania: CampaniaId | None = None
    id_influencer: InfluencerId | None = None
    contrato: Contrato | None = None
    estado: EstadoColaboracion = EstadoColaboracion.PENDIENTE
    fecha_creacion: Fecha = field(default_factory=lambda: Fecha(datetime.utcnow()))

    @classmethod
    def crear(cls, id_campania: str, id_influencer: str, contrato_url: str | None = None):
        contrato = Contrato(url=contrato_url) if contrato_url else None
        return cls(
            id=str(uuid.uuid4()),
            id_campania=CampaniaId(id=id_campania) if id_campania else None,
            id_influencer=InfluencerId(id=id_influencer) if id_influencer else None,
            contrato=contrato,
            estado=EstadoColaboracion.PENDIENTE,
            fecha_creacion=Fecha(datetime.utcnow())
        )

    # --- Regla: una colaboración no puede estar en dos estados a la vez ---
    def _cambiar_estado(self, nuevo_estado: EstadoColaboracion):
        if self.estado == nuevo_estado:
            raise ValueError(f"La colaboración ya está en estado {self.estado}")
        self.estado = nuevo_estado

    # --- Regla: un contrato rechazado no puede volver a pendiente ---
    def validar_contrato(self):
        if self.estado == EstadoColaboracion.RECHAZADO:
            raise ValueError("Un contrato rechazado no puede volver a pendiente/validado")
        if not self.contrato or not self.contrato.url:
            raise ValueError("No se puede validar una colaboración sin contrato")

        self._cambiar_estado(EstadoColaboracion.VALIDADO)
        # Como Contrato es dataclass frozen (si lo es) tal vez necesites hacer object.__setattr__
        object.__setattr__(self.contrato, "fecha_validacion", datetime.utcnow())

    def rechazar_contrato(self, motivo: str):
        if self.estado == EstadoColaboracion.RECHAZADO:
            raise ValueError("El contrato ya fue rechazado previamente")

        self._cambiar_estado(EstadoColaboracion.RECHAZADO)
        object.__setattr__(self.contrato, "motivo_rechazo", motivo)
        object.__setattr__(self.contrato, "fecha_rechazo", datetime.utcnow())
