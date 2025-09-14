from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Queries simplificadas para el servicio de monitoreo

@dataclass
class GetMetricsQuery:
    """Query para obtener métricas básicas"""
    period: str = "24h"  # '1h', '24h', '7d'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

@dataclass 
class GetEventsQuery:
    """Query para obtener eventos"""
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
