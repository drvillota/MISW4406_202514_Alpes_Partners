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
    leal: str  # Indica si es afiliado leal o no

@dataclass
class ActivateAffiliateCommand(Command):
    """Comando: Activar afiliado"""
    affiliate_id: UUID

@dataclass
class DeactivateAffiliateCommand(Command):
    """Comando: Desactivar afiliado"""
    affiliate_id: UUID
    reason: str = "Manual deactivation"

@dataclass
class RegistrarContentCommand(Command):
    """Comando: Registrar contenido (compatibilidad)"""
    affiliate_id: UUID
    titulo: str
    contenido: str
    tipo: str  # Tipo de contenido, e.g., 'Testimonio', 'Reseña'
    publicar: str = "No"
    created_at: datetime

@dataclass
class PublishContentCommand(Command):
    """Comando: Publicar contenido"""
    content_id: UUID

# CONSULTAS SIMPLIFICADAS

@dataclass
class GetAffiliateQuery(Command):
    """Consulta: Obtener datos de un afiliado"""
    affiliate_id: UUID

@dataclass
class ListContentsQuery(Command):
    """Consulta: Listar contenidos de un afiliado"""
    affiliate_id: UUID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

@dataclass
class ListAffiliatesQuery(Command):
    """Consulta: Listar todos los afiliados"""
    active_only: bool = True

@dataclass  
class ConsultarContenidosPorAfiliadoQuery(Command):
    """Consulta: Consultar contenidos por afiliado (compatibilidad)"""
    affiliate_id: UUID
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
