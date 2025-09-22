"""
Saga Endpoints para Colaboraciones Service
Endpoints específicos para manejo de sagas distribuidas
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from ..core.seedworks.message_bus import bus
from ..application.comandos import IniciarColaboracionComando
from ..infrastructure.database.connection import SessionLocal

router = APIRouter()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreateCollaborationForSagaRequest(BaseModel):
    """Request para crear colaboración como parte de una saga"""
    affiliate_id: str
    tipo_colaboracion: str = "CONTENT_CREATION"
    estado: str = "ACTIVA"
    metadata: Optional[Dict[str, Any]] = None
    saga_id: Optional[str] = None

class CollaborationSagaResponse(BaseModel):
    """Response para operaciones de saga"""
    collaboration_id: str
    affiliate_id: str
    tipo_colaboracion: str
    estado: str
    saga_id: Optional[str] = None
    created_at: str

@router.post("/api/colaboraciones", response_model=CollaborationSagaResponse)
def create_collaboration_saga(
    request: CreateCollaborationForSagaRequest,
    session: Session = Depends(get_session)
):
    """
    Crear colaboración - Compatible con Saga
    Este endpoint es llamado por el BFF como parte de la saga
    """
    try:
        # Generar IDs necesarios (en un caso real, estos vendrían de la base de datos)
        collaboration_id = uuid4()
        campania_id = uuid4()
        influencer_id = uuid4()
        contrato_id = uuid4()
        
        # Crear comando
        cmd = IniciarColaboracionComando(
            id=collaboration_id,
            campania_id=campania_id,
            influencer_id=influencer_id,
            contrato_id=contrato_id,
            estado=request.estado
        )
        
        # Ejecutar a través del message bus
        bus.handle_command(cmd)
        
        # Preparar respuesta
        response = CollaborationSagaResponse(
            collaboration_id=str(collaboration_id),
            affiliate_id=request.affiliate_id,
            tipo_colaboracion=request.tipo_colaboracion,
            estado=request.estado,
            saga_id=request.saga_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating collaboration for saga: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "service": "colaboraciones",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }