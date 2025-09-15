
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from ...core.seedwork.message_bus import bus
from ...application.commands import RegistrarConversionCommand
from ...application.commands import ConsultarComisionesPorAfiliadoQuery
from ...infrastructure.db.sqlalchemy import SessionLocal
from ...infrastructure.db.models import AffiliateModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
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
    logger.info(f"Processing conversion for affiliate: {payload.affiliate_id}")
    
    cmd = RegistrarConversionCommand(
        affiliate_id=payload.affiliate_id,
        event_type=payload.event_type,
        monto=payload.monto,
        moneda=payload.moneda,
        occurred_at=payload.occurred_at or datetime.now(timezone.utc)
    )
    
    logger.info(f"Command created: {type(cmd).__name__}")
    logger.info(f"Registered handlers: {list(bus._command_handlers.keys())}")
    
    try:
        logger.info("Attempting to handle command")
        result = bus.handle_command(cmd)
        logger.info(f"Command processed successfully: {result}")
        return result
    except KeyError as ke:
        logger.error(f"Handler not found for: {type(cmd).__name__}")
        logger.error(f"Available handlers: {list(bus._command_handlers.keys())}")
        raise HTTPException(status_code=500, detail=f"Command handler not registered for {type(cmd).__name__}")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        logger.error("Full traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing command: {str(e)}") 

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
    name: str  # Cambió de 'nombre' a 'name'
    email: str  # Agregado campo email requerido
    commission_rate: float  # Cambió de 'tasa_comision' a 'commission_rate'

@router.post("/dev/seed_affiliate")
def seed_affiliate(payload: SeedAffiliateIn, session: Session = Depends(get_session)):
    m = AffiliateModel(
        id=payload.id or uuid4(), 
        name=payload.name,  # Cambió de 'nombre' a 'name'
        email=payload.email,  # Agregado campo email
        commission_rate=payload.commission_rate  # Cambió de 'tasa_comision' a 'commission_rate'
    )
    session.add(m); session.commit()
    return {"affiliate_id": str(m.id)}
