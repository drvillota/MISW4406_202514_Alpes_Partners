"""Entidades de dominio simplificadas para afiliados-comisiones

Solo las entidades esenciales sin over-engineering DDD
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Optional

@dataclass
class Affiliate:
    """Entidad Afiliado - Simplificada"""
    id: UUID
    name: str
    email: str
    commission_rate: Decimal  # Porcentaje: 10.5 = 10.5%
    created_at: datetime
    active: bool = True
    
    def calculate_commission(self, conversion_amount: Decimal) -> Decimal:
        return (conversion_amount * self.commission_rate) / Decimal('100')

@dataclass  
class Commission:
    """Entidad Comisión - Simplificada"""
    id: UUID
    affiliate_id: UUID
    conversion_id: UUID  # UUID de la conversión interna
    amount: Decimal
    calculated_at: datetime
    currency: str = "USD"
    status: str = "pending"  # pending, paid, cancelled

@dataclass
class ConversionEvent:
    """Representa un evento de conversión para procesar comisiones"""
    id: UUID
    affiliate_id: UUID
    event_type: str  # PURCHASE, SIGNUP, etc.
    amount: Decimal
    occurred_at: datetime
    currency: str = "USD"
    processed: bool = False