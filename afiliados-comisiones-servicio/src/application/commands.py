"""Comandos y consultas CQS simplificados"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional
from ..core.seedwork.commands import Command

# COMANDOS SIMPLIFICADOS

@dataclass
class RegisterAffiliateCommand(Command):
    """Comando: Registrar nuevo afiliado"""
    name: str
    email: str
    commission_rate: Decimal

@dataclass
class ProcessConversionCommand(Command):
    """Comando: Procesar conversión y calcular comisión"""
    affiliate_id: UUID
    event_type: str
    amount: Decimal
    currency: str = "USD"

@dataclass
class RegistrarConversionCommand(Command):
    """Comando: Registrar conversión (compatibilidad)"""
    affiliate_id: UUID
    event_type: str
    monto: float  # Usando float para mantener compatibilidad
    occurred_at: datetime
    moneda: str = "USD"

# CONSULTAS SIMPLIFICADAS

@dataclass
class GetAffiliateQuery(Command):
    """Consulta: Obtener datos de un afiliado"""
    affiliate_id: UUID

@dataclass
class ListCommissionsQuery(Command):
    """Consulta: Listar comisiones de un afiliado"""
    affiliate_id: UUID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None