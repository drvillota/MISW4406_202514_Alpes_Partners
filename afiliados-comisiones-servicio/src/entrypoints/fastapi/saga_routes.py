"""
Saga Endpoints para Afiliados-Comisiones Service
Endpoints específicos para manejo de sagas distribuidas
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from decimal import Decimal

from ..core.seedwork.message_bus import bus
from ..application.commands import RegisterAffiliateCommand
from ..infrastructure.db.sqlalchemy import SessionLocal

router = APIRouter()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreateAffiliateForSagaRequest(BaseModel):
    """Request para crear afiliado como parte de una saga"""
    name: str
    email: str
    commission_rate: float
    status: str = "ACTIVE"
    metadata: Optional[Dict[str, Any]] = None
    saga_id: Optional[str] = None

class AffiliateUpdateRequest(BaseModel):
    """Request para actualizar afiliado"""
    status: str

class AffiliateSagaResponse(BaseModel):
    """Response para operaciones de saga"""
    affiliate_id: str
    name: str
    email: str
    status: str
    commission_rate: float
    saga_id: Optional[str] = None
    created_at: str

@router.post("/api/afiliados", response_model=AffiliateSagaResponse)
def create_affiliate_saga(
    request: CreateAffiliateForSagaRequest,
    session: Session = Depends(get_session)
):
    """
    Crear afiliado - Compatible con Saga
    Este endpoint es llamado por el BFF como parte de la saga
    """
    try:
        # Crear comando
        cmd = RegisterAffiliateCommand(
            name=request.name,
            email=request.email,
            commission_rate=Decimal(str(request.commission_rate))
        )
        
        # Ejecutar a través del message bus
        bus.handle_command(cmd)
        
        # Preparar respuesta (simular ID generado)
        affiliate_id = str(uuid4())
        
        response = AffiliateSagaResponse(
            affiliate_id=affiliate_id,
            name=request.name,
            email=request.email,
            status=request.status,
            commission_rate=request.commission_rate,
            saga_id=request.saga_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating affiliate for saga: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/afiliados/{affiliate_id}/deactivate")
def deactivate_affiliate_saga(
    affiliate_id: str,
    request: AffiliateUpdateRequest,
    session: Session = Depends(get_session)
):
    """
    Desactivar afiliado - Compensación de Saga
    Este endpoint es llamado para compensar la creación de afiliado
    """
    try:
        # TODO: Implementar lógica de desactivación usando el repository
        
        return {
            "message": f"Affiliate {affiliate_id} deactivated for saga compensation",
            "affiliate_id": affiliate_id,
            "status": request.status,
            "compensated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error compensating affiliate {affiliate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "service": "afiliados-comisiones",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }