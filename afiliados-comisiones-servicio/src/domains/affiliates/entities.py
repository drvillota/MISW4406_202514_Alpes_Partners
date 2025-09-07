from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID

@dataclass
class Afiliado:
    id: UUID
    nombre: str
    tasa_comision: float  # porcentaje (ej. 12.5 equivale a 12.5%)
