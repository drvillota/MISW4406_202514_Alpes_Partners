"""Eventos de dominio e integración simplificados

Eventos esenciales para comunicación entre microservicios
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

# Eventos de Integración (se publican a Pulsar)

@dataclass
class AffiliateRegistered:
    """Evento: Se registró un nuevo afiliado"""
    affiliate_id: str
    name: str
    email: str
    commission_rate: float
    timestamp: int  # Unix timestamp

@dataclass
class AffiliateActivated:
    """Evento: Se activó un afiliado"""
    affiliate_id: str
    timestamp: int

@dataclass
class AffiliateDeactivated:
    """Evento: Se desactivó un afiliado"""
    affiliate_id: str
    reason: str
    timestamp: int

@dataclass
class CommissionCalculated:
    """Evento: Se calculó una nueva comisión"""
    commission_id: str
    affiliate_id: str
    conversion_id: str
    amount: float
    currency: str
    timestamp: int

# Eventos externos que consume este servicio

@dataclass  
class ConversionRegistered:
    """Evento externo: Se registró una conversión (del servicio tracking)"""
    conversion_id: str
    affiliate_id: str
    user_id: str
    amount: float
    currency: str
    timestamp: int