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
    leal: str
    commission_rate: Decimal  # Porcentaje: 10.5 = 10.5%
    created_at: datetime
    active: bool = True

@dataclass  
class Content:
    """Entidad Contenido - Simplificada"""
    id: UUID
    affiliate_id: UUID
    titulo: str
    contenido: str
    tipo: str
    publicar: str
    created_at: datetime
