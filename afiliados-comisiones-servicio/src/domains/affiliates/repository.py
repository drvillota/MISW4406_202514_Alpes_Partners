from __future__ import annotations
from typing import Optional
from uuid import UUID
from ...core.seedwork.repository import Repository
from .entities import Afiliado

class AfiliadoRepository(Repository):
    def add(self, entity: Afiliado) -> None: ...
    def get(self, entity_id: UUID) -> Optional[Afiliado]: ...
