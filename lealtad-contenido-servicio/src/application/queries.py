from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class ConsultarContenidosPorAfiliadoQuery:
    affiliate_id: UUID
    desde: datetime | None = None
    hasta: datetime | None = None
