import logging
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID, uuid4
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from pydantic import BaseModel

from infrastructure.database.connection import SessionLocal
from core.seedworks.message_bus import bus
from application.comandos import (
    IniciarColaboracionComando,
    FirmarContratoComando,
    CancelarContratoComando,
    FinalizarColaboracionComando,
    RegistrarPublicacionComando,
)
from application.queries import (
    ConsultarColaboracionQuery,
    ListarColaboracionesQuery,
)
from infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Requests DTOs ---
class IniciarColaboracionIn(BaseModel):
    campania_id: UUID
    influencer_id: UUID
    fecha_inicio: date
    fecha_fin: date

class PublicacionIn(BaseModel):
    url: str
    red: str
    fecha: date

# --- Endpoints principales ---
@router.post("/colaboraciones")
def iniciar_colaboracion(payload: IniciarColaboracionIn):
    cmd = IniciarColaboracionComando(
        campania_id=payload.campania_id,
        influencer_id=payload.influencer_id,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
    )
    try:
        return bus.handle_command(cmd)
    except Exception as e:
        logger.error(f"Error iniciando colaboración: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/colaboraciones/{colaboracion_id}/publicaciones")
def registrar_publicacion(colaboracion_id: UUID, payload: PublicacionIn):
    cmd = RegistrarPublicacionComando(
        colaboracion_id=colaboracion_id,
        url=payload.url,
        red=payload.red,
        fecha=payload.fecha,
    )
    try:
        return bus.handle_command(cmd)
    except Exception as e:
        logger.error(f"Error registrando publicación: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/colaboraciones/{colaboracion_id}")
def consultar_colaboracion(colaboracion_id: UUID):
    q = ConsultarColaboracionQuery(colaboracion_id=colaboracion_id)
    try:
        return bus.handle_command(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/colaboraciones")
def listar_colaboraciones():
    q = ListarColaboracionesQuery()
    try:
        return bus.handle_command(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Diagnóstico ---
@router.get("/dev/settings")
def show_settings():
    return {
        "database_url": settings.DATABASE_URL,
        "pulsar_url": settings.pulsar_url,
        "uvicorn_host": settings.UVICORN_HOST,
        "uvicorn_port": settings.UVICORN_PORT,
        "debug": settings.DEBUG,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
