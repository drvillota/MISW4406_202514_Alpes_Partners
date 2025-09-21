from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from datetime import date
from typing import Optional

@dataclass
class ConsultarColaboracionQuery:
    """Consulta: Obtener detalles de una colaboración específica"""
    colaboracion_id: UUID


@dataclass
class ListarColaboracionesQuery:
    """Consulta: Listar colaboraciones con filtros opcionales"""
    campania_id: Optional[UUID] = None
    influencer_id: Optional[UUID] = None
    estado: Optional[str] = None  # "VIGENTE", "FINALIZADO", "CANCELADO"
    desde: Optional[date] = None
    hasta: Optional[date] = None
