"""Eventos de dominio e integración para Colaboraciones"""

from dataclasses import dataclass


# -------------------------------
# Eventos de Integración (publicados a Pulsar)
# -------------------------------

@dataclass
class ColaboracionIniciada:
    """Evento: se inició una nueva colaboración"""
    colaboracion_id: str
    campania_id: str
    influencer_id: str
    contrato_id: str
    fecha_inicio: str 
    fecha_fin: str 


@dataclass
class ContratoFirmado:
    """Evento: un contrato fue firmado"""
    contrato_id: str
    colaboracion_id: str
    campania_id: str
    influencer_id: str


@dataclass
class ContratoCancelado:
    """Evento: un contrato fue cancelado"""
    contrato_id: str
    colaboracion_id: str
    campania_id: str
    influencer_id: str
    motivo: str


@dataclass
class ColaboracionFinalizada:
    """Evento: la colaboración terminó"""
    colaboracion_id: str
    campania_id: str
    influencer_id: str


@dataclass
class PublicacionRegistrada:
    """Evento: un influencer aportó contenido en una colaboración"""
    colaboracion_id: str
    url: str
    red: str
    fecha: str      


# -------------------------------
# Eventos externos (consumidos por este micro)
# -------------------------------

@dataclass
class CampaniaFinalizada:
    """Evento externo: una campaña llegó a su fin"""
    campania_id: str
    fecha_fin: str


@dataclass
class InfluencerRegistrado:
    """Evento externo: un influencer fue registrado en otro micro"""
    influencer_id: str
    nombre: str
    email: str
