from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Conversion:
    id: UUID
    affiliate_id: UUID
    event_type: str
    monto: float
    moneda: str
    occurred_at: datetime

@dataclass
class Comision:
    id: UUID
    affiliate_id: UUID
    conversion_id: UUID
    valor: float
    moneda: str
    estado: str  # 'pendiente'|'pagada'
    created_at: datetime

def nueva_conversion(affiliate_id: UUID, event_type: str, monto: float, moneda: str, occurred_at: datetime) -> Conversion:
    return Conversion(id=uuid4(), affiliate_id=affiliate_id, event_type=event_type, monto=monto, moneda=moneda, occurred_at=occurred_at)

def nueva_comision(affiliate_id: UUID, conversion_id: UUID, valor: float, moneda: str) -> Comision:
    return Comision(id=uuid4(), affiliate_id=affiliate_id, conversion_id=conversion_id, valor=valor, moneda=moneda, estado='pendiente', created_at=datetime.utcnow())
