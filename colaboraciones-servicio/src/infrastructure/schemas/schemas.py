"""Schemas de Pulsar para eventos del microservicio de Colaboraciones"""

from pulsar.schema import Record, String, Integer, Array
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, List

class BaseEventSchema(Record):
    """Schema base para eventos de colaboraciones"""
    colaboracion_id = String()
    campania_id = String()
    influencer_id = String()
    timestamp = Integer()  # Unix timestamp


class ColaboracionIniciadaSchema(BaseEventSchema):
    """Evento: se inició una colaboración"""
    contrato_id = String()
    fecha_inicio = String()  # ISO8601
    fecha_fin = String()     # ISO8601


class ContratoFirmadoSchema(BaseEventSchema):
    """Evento: se firmó un contrato"""
    contrato_id = String()


class ContratoCanceladoSchema(BaseEventSchema):
    """Evento: se canceló un contrato"""
    contrato_id = String()
    motivo = String()


class ColaboracionFinalizadaSchema(BaseEventSchema):
    """Evento: se finalizó una colaboración"""
    pass


class PublicacionRegistradaSchema(BaseEventSchema):
    """Evento: un influencer registró una publicación en la colaboración"""
    url = String()
    red = String()
    fecha = String()  # ISO8601


####################################
"""Schemas Pydantic para requests y responses del microservicio de Colaboraciones"""

# --- Requests ---
class IniciarColaboracionRequest(BaseModel):
    campania_id: str
    influencer_id: str
    contrato_id: str
    fecha_inicio: date
    fecha_fin: date


class RegistrarPublicacionRequest(BaseModel):
    url: str
    red: str
    fecha: date


# --- Responses ---
class PublicacionResponse(BaseModel):
    url: str
    red: str
    fecha: date


class ColaboracionResponse(BaseModel):
    id: str
    campania_id: str
    influencer_id: str
    contrato_id: str
    estado: str
    publicaciones: List[PublicacionResponse] = Field(default_factory=list)
    created_at: datetime