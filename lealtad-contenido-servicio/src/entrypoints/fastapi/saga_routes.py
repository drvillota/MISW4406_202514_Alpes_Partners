"""
Saga Endpoints para Lealtad-Contenido Service
Endpoints específicos para manejo de sagas distribuidas
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from ...core.seedwork.message_bus import bus
from ...application.commands import RegistrarContentCommand
from ...infrastructure.db.sqlalchemy import SessionLocal

router = APIRouter()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreateContentForSagaRequest(BaseModel):
    """Request para crear contenido como parte de una saga"""
    titulo: str
    descripcion: str
    tipo: str = "BLOG"
    autor: str = "Sistema"
    metadata: Optional[Dict[str, Any]] = None
    saga_id: Optional[str] = None

class ContentSagaResponse(BaseModel):
    """Response para operaciones de saga"""
    content_id: str
    titulo: str
    estado: str
    saga_id: Optional[str] = None
    created_at: str

@router.post("/api/contenido", response_model=ContentSagaResponse)
def create_content_saga(
    request: CreateContentForSagaRequest,
    session: Session = Depends(get_session)
):
    """
    Crear contenido - Compatible con Saga
    Este endpoint es llamado por el BFF como parte de la saga
    """
    try:
        # Crear comando
        cmd = RegistrarContentCommand(
            id=uuid4(),
            affiliate_id=uuid4(),  # Temporal, se vinculará después
            titulo=request.titulo,
            contenido=request.descripcion,
            tipo=request.tipo
        )
        
        # Ejecutar a través del message bus
        result = bus.handle_command(cmd)
        
        # Preparar respuesta
        response = ContentSagaResponse(
            content_id=str(cmd.id),
            titulo=request.titulo,
            estado="CREATED",
            saga_id=request.saga_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating content for saga: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/contenido/{content_id}")
def delete_content_saga(
    content_id: str,
    session: Session = Depends(get_session)
):
    """
    Eliminar contenido - Compensación de Saga
    Este endpoint es llamado para compensar la creación de contenido
    """
    try:
        # Buscar y eliminar contenido
        # TODO: Implementar lógica de eliminación/desactivación
        
        return {
            "message": f"Content {content_id} deleted/deactivated for saga compensation",
            "content_id": content_id,
            "compensated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error compensating content {content_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "service": "lealtad-contenido",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }