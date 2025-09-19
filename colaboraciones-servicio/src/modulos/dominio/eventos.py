"""
Eventos de dominio para Colaboraciones
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from seedwork.dominio.eventos import EventoDominio


@dataclass
class ColaboracionCreada(EventoDominio):
    id: str = field(default_factory=lambda: str(uuid4()))
    campaña_id: str = None
    influencer_id: str = None
    contrato_url: str = None
    fecha_creacion: int = field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))


@dataclass
class ContratoValidado(EventoDominio):
    id: str = field(default_factory=lambda: str(uuid4()))
    colaboracion_id: str = None
    fecha_validacion: int = field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))


@dataclass
class ContratoRechazado(EventoDominio):
    id: str = field(default_factory=lambda: str(uuid4()))
    colaboracion_id: str = None
    motivo: str = None
    fecha_rechazo: int = field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))


@dataclass
class ColaboracionFinalizada(EventoDominio):
    id: str = field(default_factory=lambda: str(uuid4()))
    colaboracion_id: str = None
    fecha_finalizacion: int = field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))