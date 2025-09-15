from dataclasses import dataclass, field
from seedwork.aplicacion.dto import DTO

@dataclass(frozen=True)
class ColaboracionDTO(DTO):
    id: str = field(default_factory=str)
    id_campania: str = field(default_factory=str)
    id_influencer: str = field(default_factory=str)
    contrato_url: str = field(default_factory=str)
    estado: str = field(default_factory=str)
    fecha_creacion: str = field(default_factory=str)
