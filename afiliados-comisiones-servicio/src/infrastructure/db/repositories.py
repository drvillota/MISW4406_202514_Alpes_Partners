from __future__ import annotations
from uuid import UUID
from typing import Optional, List
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from ...domains.affiliates.entities import Afiliado
from ...domains.commissions.entities import Conversion, Comision
from ...domains.affiliates.repository import AfiliadoRepository
from ...domains.commissions.repository import ConversionRepository, ComisionRepository
from .models import AfiliadoModel, ConversionModel, ComisionModel
from .sqlalchemy import SessionLocal

class AfiliadoRepoSQL(AfiliadoRepository):
    def __init__(self, session: Session): self.session = session
    def add(self, entity: Afiliado) -> None:
        self.session.add(AfiliadoModel(id=entity.id, nombre=entity.nombre, tasa_comision=entity.tasa_comision))
    def get(self, entity_id: UUID) -> Optional[Afiliado]:
        m = self.session.get(AfiliadoModel, entity_id)
        if not m: return None
        return Afiliado(id=m.id, nombre=m.nombre, tasa_comision=m.tasa_comision)

class ConversionRepoSQL(ConversionRepository):
    def __init__(self, session: Session): self.session = session
    def add(self, entity: Conversion) -> None:
        self.session.add(ConversionModel(id=entity.id, affiliate_id=entity.affiliate_id, event_type=entity.event_type, monto=entity.monto, moneda=entity.moneda, occurred_at=entity.occurred_at))
    def get(self, entity_id: UUID) -> Optional[Conversion]:
        m = self.session.get(ConversionModel, entity_id)
        if not m: return None
        return Conversion(id=m.id, affiliate_id=m.affiliate_id, event_type=m.event_type, monto=m.monto, moneda=m.moneda, occurred_at=m.occurred_at)

class ComisionRepoSQL(ComisionRepository):
    def __init__(self, session: Session): self.session = session
    def add(self, entity: Comision) -> None:
        self.session.add(ComisionModel(id=entity.id, affiliate_id=entity.affiliate_id, conversion_id=entity.conversion_id, valor=entity.valor, moneda=entity.moneda, estado=entity.estado, created_at=entity.created_at))
    def get(self, entity_id: UUID) -> Optional[Comision]:
        m = self.session.get(ComisionModel, entity_id)
        if not m: return None
        return Comision(id=m.id, affiliate_id=m.affiliate_id, conversion_id=m.conversion_id, valor=m.valor, moneda=m.moneda, estado=m.estado, created_at=m.created_at)
    def list_by_affiliate(self, affiliate_id: UUID, desde: Optional[str]=None, hasta: Optional[str]=None) -> List[Comision]:
        q = select(ComisionModel).where(ComisionModel.affiliate_id == affiliate_id)
        if desde:
            q = q.where(ComisionModel.created_at >= text(f"'{desde}'"))
        if hasta:
            q = q.where(ComisionModel.created_at <= text(f"'{hasta}'"))
        res = self.session.execute(q).scalars().all()
        return [Comision(id=m.id, affiliate_id=m.affiliate_id, conversion_id=m.conversion_id, valor=m.valor, moneda=m.moneda, estado=m.estado, created_at=m.created_at) for m in res]
