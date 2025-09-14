from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from ...core.seedwork.events import DomainEvent

@dataclass
class ConversionRegistrada(DomainEvent):
    affiliate_id: UUID
    event_type: str
    monto: float
    moneda: str
    occurred_at: datetime

    def __init__(self, affiliate_id: UUID, event_type: str, monto: float, moneda: str, occurred_at: datetime):
        super().__init__(name="ConversionRegistrada")
        self.affiliate_id = affiliate_id
        self.event_type = event_type
        self.monto = monto
        self.moneda = moneda
        self.occurred_at = occurred_at

@dataclass
class ComisionCreada(DomainEvent):
    commission_id: UUID
    affiliate_id: UUID
    valor: float
    moneda: str

    def __init__(self, commission_id: UUID, affiliate_id: UUID, valor: float, moneda: str):
        super().__init__(name="ComisionCreada")
        self.commission_id = commission_id
        self.affiliate_id = affiliate_id
        self.valor = valor
        self.moneda = moneda

@dataclass
class ComisionPagada(DomainEvent):
    """Evento emitido cuando se paga una comisión"""
    commission_id: UUID
    affiliate_id: UUID
    valor: float
    fecha_pago: datetime

    def __init__(self, commission_id: UUID, affiliate_id: UUID, valor: float, fecha_pago: datetime):
        super().__init__(name="ComisionPagada")
        self.commission_id = commission_id
        self.affiliate_id = affiliate_id
        self.valor = valor
        self.fecha_pago = fecha_pago

@dataclass
class ComisionCancelada(DomainEvent):
    """Evento emitido cuando se cancela una comisión"""
    commission_id: UUID
    affiliate_id: UUID
    motivo: str
    fecha_cancelacion: datetime

    def __init__(self, commission_id: UUID, affiliate_id: UUID, motivo: str, fecha_cancelacion: datetime):
        super().__init__(name="ComisionCancelada")
        self.commission_id = commission_id
        self.affiliate_id = affiliate_id
        self.motivo = motivo
        self.fecha_cancelacion = fecha_cancelacion
