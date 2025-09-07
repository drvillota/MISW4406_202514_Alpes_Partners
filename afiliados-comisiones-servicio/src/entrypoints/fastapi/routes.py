
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from ...core.seedwork.message_bus import bus
from ...application.commands import RegistrarConversionCommand
from ...application.queries import ConsultarComisionesPorAfiliadoQuery
from ...infrastructure.db.sqlalchemy import SessionLocal
from ...infrastructure.db.models import AfiliadoModel
from sqlalchemy.orm import Session

router = APIRouter()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ConversionIn(BaseModel):
    affiliate_id: UUID
    event_type: str = Field(..., examples=["COMPRA", "REGISTRO"]) 
    monto: float
    moneda: str = "USD"
    occurred_at: datetime | None = None

@router.post("/conversions")
def registrar_conversion(payload: ConversionIn):
    cmd = RegistrarConversionCommand(
        affiliate_id=payload.affiliate_id,
        event_type=payload.event_type,
        monto=payload.monto,
        moneda=payload.moneda,
        occurred_at=payload.occurred_at or datetime.utcnow()
    )
    try:
        return bus.handle_command(cmd)
    except KeyError:
        raise HTTPException(status_code=500, detail="Command handler not registered") 

@router.get("/affiliates/{affiliate_id}/commissions")
def listar_comisiones(affiliate_id: UUID, desde: datetime | None = None, hasta: datetime | None = None):
    # Delegar al handler de consulta registrado en app.main
    try:
        from ...app.main import query_handler
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No query handler: {e}")
    if not query_handler:
        raise HTTPException(status_code=500, detail="Query handler not initialized yet")
    q = ConsultarComisionesPorAfiliadoQuery(affiliate_id=affiliate_id, desde=desde, hasta=hasta)
    return query_handler(q)

# --- Endpoints utilitarios para demo ---
class SeedAffiliateIn(BaseModel):
    id: UUID | None = None
    nombre: str
    tasa_comision: float

@router.post("/dev/seed_affiliate")
def seed_affiliate(payload: SeedAffiliateIn, session: Session = Depends(get_session)):
    m = AfiliadoModel(id=payload.id or uuid4(), nombre=payload.nombre, tasa_comision=payload.tasa_comision)
    session.add(m); session.commit()
    return {"affiliate_id": str(m.id)}
