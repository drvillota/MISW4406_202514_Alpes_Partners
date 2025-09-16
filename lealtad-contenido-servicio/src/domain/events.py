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

# Eventos externos que consume este servicio

@dataclass  
class ContenidoRegistrado:
    """Evento externo: Se registró un contenido (del servicio tracking)"""
    content_id: str
    affiliate_id: str
    titulo: str
    contenido: str
    tipo: str
    publicar: str
    created_at: str