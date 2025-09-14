"""Eventos de dominio del agregado Afiliado

En este archivo se definen los eventos de dominio específicos del agregado Afiliado

"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional
from ...core.seedwork.events import DomainEvent

@dataclass
class AfiliadoCreado(DomainEvent):
    """Evento emitido cuando se crea un nuevo afiliado"""
    affiliate_id: UUID
    nombre: str
    tasa_comision: float
    fecha_registro: datetime
    
    def __init__(self, affiliate_id: UUID, nombre: str, tasa_comision: float, fecha_registro: datetime):
        super().__init__(name="AfiliadoCreado")
        self.affiliate_id = affiliate_id
        self.nombre = nombre
        self.tasa_comision = tasa_comision
        self.fecha_registro = fecha_registro

@dataclass
class AfiliadoActivado(DomainEvent):
    """Evento emitido cuando se activa un afiliado"""
    affiliate_id: UUID
    fecha_activacion: datetime
    
    def __init__(self, affiliate_id: UUID, fecha_activacion: datetime):
        super().__init__(name="AfiliadoActivado")
        self.affiliate_id = affiliate_id
        self.fecha_activacion = fecha_activacion

@dataclass
class AfiliadoDesactivado(DomainEvent):
    """Evento emitido cuando se desactiva un afiliado"""
    affiliate_id: UUID
    motivo: str
    fecha_desactivacion: datetime
    
    def __init__(self, affiliate_id: UUID, motivo: str, fecha_desactivacion: datetime):
        super().__init__(name="AfiliadoDesactivado")
        self.affiliate_id = affiliate_id
        self.motivo = motivo
        self.fecha_desactivacion = fecha_desactivacion

@dataclass
class TasaComisionActualizada(DomainEvent):
    """Evento emitido cuando se actualiza la tasa de comisión de un afiliado"""
    affiliate_id: UUID
    tasa_anterior: float
    nueva_tasa: float
    fecha_cambio: datetime
    
    def __init__(self, affiliate_id: UUID, tasa_anterior: float, nueva_tasa: float, fecha_cambio: datetime):
        super().__init__(name="TasaComisionActualizada")
        self.affiliate_id = affiliate_id
        self.tasa_anterior = tasa_anterior
        self.nueva_tasa = nueva_tasa
        self.fecha_cambio = fecha_cambio