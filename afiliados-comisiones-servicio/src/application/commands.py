from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from ..core.seedwork.commands import Command

@dataclass
class RegistrarConversionCommand(Command):
    affiliate_id: UUID
    event_type: str
    monto: float
    moneda: str
    occurred_at: datetime
