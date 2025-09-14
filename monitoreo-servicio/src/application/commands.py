from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

# Comandos simplificados para el servicio de monitoreo

@dataclass
class RecordEventCommand:
    """Comando para registrar un evento de monitoreo"""
    event_type: str  # 'conversion', 'click', 'sale'
    user_id: str
    session_id: str
    metadata: Dict[str, Any]
    occurred_at: datetime
