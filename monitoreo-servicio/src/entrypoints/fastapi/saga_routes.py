"""
Saga Endpoints para Monitoreo Service
Endpoints específicos para manejo de sagas distribuidas
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from ..core.seedwork.message_bus import bus
from ..application.commands import RegistrarEventoCommand
from ..infrastructure.database.connection import SessionLocal

logger = logging.getLogger(__name__)
router = APIRouter()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RegisterMetricsForSagaRequest(BaseModel):
    """Request para registrar métricas como parte de una saga"""
    event_type: str
    entity_id: str
    entity_type: str = "AFFILIATE"
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    saga_id: Optional[str] = None

class MetricsSagaResponse(BaseModel):
    """Response para operaciones de saga"""
    metrics_id: str
    event_type: str
    entity_id: str
    status: str
    saga_id: Optional[str] = None
    created_at: str

@router.post("/api/metrics", response_model=MetricsSagaResponse)
def register_metrics_saga(
    request: RegisterMetricsForSagaRequest,
    session: Session = Depends(get_session)
):
    """
    Registrar métricas - Compatible con Saga
    Este endpoint es llamado por el BFF como parte de la saga
    """
    try:
        # Crear comando para registrar evento
        timestamp = request.timestamp or datetime.now(timezone.utc).isoformat()
        
        cmd = RegistrarEventoCommand(
            tipo_evento=request.event_type,
            entidad_id=request.entity_id,
            entidad_tipo=request.entity_type,
            datos=request.data,
            timestamp=timestamp
        )
        
        # Ejecutar a través del message bus
        bus.handle_command(cmd)
        
        # Preparar respuesta
        metrics_id = str(uuid4())
        
        response = MetricsSagaResponse(
            metrics_id=metrics_id,
            event_type=request.event_type,
            entity_id=request.entity_id,
            status="RECORDED",
            saga_id=request.saga_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error registering metrics for saga: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "service": "monitoreo",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }