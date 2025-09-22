"""
BFF Routes - Endpoints principales para orquestación de sagas y microservicios
"""
import logging
from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field

from infrastructure.saga_log import SagaLogRepository, SagaStatus
from infrastructure.orchestrators import SagaOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

# === MODELOS DE ENTRADA ===

class CompleteAffiliateRegistrationRequest(BaseModel):
    """Solicitud para registro completo de afiliado con contenido"""
    affiliate_name: str = Field(..., description="Nombre del afiliado")
    affiliate_email: str = Field(..., description="Email del afiliado")
    commission_rate: float = Field(..., ge=0, le=1, description="Tasa de comisión (0-1)")
    content_type: str = Field(default="BLOG", description="Tipo de contenido")
    content_title: str = Field(..., description="Título del contenido")
    content_description: str = Field(..., description="Descripción del contenido")
    collaboration_type: str = Field(default="CONTENT_CREATION", description="Tipo de colaboración")


class SagaResponse(BaseModel):
    """Respuesta estándar para sagas"""
    saga_id: str
    saga_type: str
    status: str
    message: str
    tracking_url: str


class SagaStatusResponse(BaseModel):
    """Respuesta detallada del estado de saga"""
    saga_id: str
    saga_type: str
    status: str
    steps: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    correlation_id: Optional[str] = None


# === DEPENDENCIAS ===

async def get_saga_repository(request: Request) -> SagaLogRepository:
    """Obtener repositorio de saga log"""
    return request.app.state.saga_repo


# === ENDPOINTS PRINCIPALES DE SAGAS ===

@router.post("/sagas/complete-affiliate-registration", response_model=SagaResponse)
async def complete_affiliate_registration(
    request: CompleteAffiliateRegistrationRequest,
    background_tasks: BackgroundTasks,
    saga_repo: SagaLogRepository = Depends(get_saga_repository)
):
    """
    SAGA PRINCIPAL: Registro Completo de Afiliado con Contenido
    
    Esta saga orquesta los siguientes pasos:
    1. Crear afiliado en lealtad-contenido
    2. Validar y activar en afiliados-comisiones  
    3. Registrar colaboración en colaboraciones-servicio
    4. Registrar métricas en monitoreo
    
    Con compensaciones automáticas en caso de fallo.
    """
    saga_id = str(uuid4())
    correlation_id = str(uuid4())
    
    try:
        # Iniciar saga
        await saga_repo.start_saga(
            saga_id=saga_id,
            saga_type="CompleteAffiliateRegistration",
            correlation_id=correlation_id,
            saga_metadata={
                "affiliate_name": request.affiliate_name,
                "affiliate_email": request.affiliate_email,
                "initiated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Ejecutar saga en background
        orchestrator = SagaOrchestrator(saga_repo)
        background_tasks.add_task(
            orchestrator.execute_complete_affiliate_registration,
            saga_id,
            request
        )
        
        return SagaResponse(
            saga_id=saga_id,
            saga_type="CompleteAffiliateRegistration",
            status="STARTED",
            message="Saga iniciada correctamente. El proceso se ejecutará en segundo plano.",
            tracking_url=f"/api/v1/sagas/{saga_id}/status"
        )
        
    except Exception as e:
        logger.error(f"Error iniciando saga {saga_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando saga: {str(e)}")


@router.get("/sagas/{saga_id}/status", response_model=SagaStatusResponse)
async def get_saga_status(
    saga_id: str,
    saga_repo: SagaLogRepository = Depends(get_saga_repository)
):
    """Obtener estado detallado de una saga"""
    try:
        saga = await saga_repo.get_saga(saga_id)
        if not saga:
            raise HTTPException(status_code=404, detail=f"Saga {saga_id} not found")
        
        # Convertir steps a dict para respuesta
        steps_data = []
        for step in saga.steps:
            step_dict = {
                "step_name": step.step_name,
                "status": step.status,
                "timestamp": step.timestamp,
                "payload": step.payload
            }
            if step.error_message:
                step_dict["error_message"] = step.error_message
            steps_data.append(step_dict)
        
        return SagaStatusResponse(
            saga_id=saga.id,
            saga_type=saga.saga_type,
            status=saga.status.value,
            steps=steps_data,
            created_at=saga.created_at,
            updated_at=saga.updated_at,
            correlation_id=saga.correlation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saga status {saga_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sagas")
async def list_sagas(
    limit: int = 50,
    saga_type: Optional[str] = None,
    status: Optional[str] = None,
    saga_repo: SagaLogRepository = Depends(get_saga_repository)
):
    """Listar sagas con filtros opcionales"""
    try:
        saga_status_filter = None
        if status:
            try:
                saga_status_filter = SagaStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        sagas = await saga_repo.list_sagas(
            limit=limit,
            saga_type=saga_type,
            status=saga_status_filter
        )
        
        # Convertir a formato de respuesta
        saga_summaries = []
        for saga in sagas:
            saga_summaries.append({
                "saga_id": saga.id,
                "saga_type": saga.saga_type,
                "status": saga.status.value,
                "created_at": saga.created_at,
                "updated_at": saga.updated_at,
                "steps_count": len(saga.steps),
                "correlation_id": saga.correlation_id
            })
        
        return {
            "sagas": saga_summaries,
            "total": len(saga_summaries),
            "filters": {
                "saga_type": saga_type,
                "status": status,
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sagas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sagas/statistics")
async def get_saga_statistics(
    saga_repo: SagaLogRepository = Depends(get_saga_repository)
):
    """Obtener estadísticas generales de sagas"""
    try:
        stats = await saga_repo.get_saga_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting saga statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS DE UTILIDAD Y DEBUG ===

@router.post("/sagas/{saga_id}/compensate")
async def trigger_compensation(
    saga_id: str,
    saga_repo: SagaLogRepository = Depends(get_saga_repository)
):
    """Forzar compensación manual de una saga (para testing)"""
    try:
        saga = await saga_repo.get_saga(saga_id)
        if not saga:
            raise HTTPException(status_code=404, detail=f"Saga {saga_id} not found")
        
        # Ejecutar compensación
        orchestrator = SagaOrchestrator(saga_repo)
        await orchestrator.compensate_saga(saga_id, "Manual compensation triggered")
        
        return {"message": f"Compensation triggered for saga {saga_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering compensation for saga {saga_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/sagas")
async def saga_health_check(
    saga_repo: SagaLogRepository = Depends(get_saga_repository)
):
    """Health check del sistema de sagas"""
    try:
        # Verificar conexión a base de datos
        stats = await saga_repo.get_saga_statistics()
        
        return {
            "status": "healthy",
            "saga_system": "operational",
            "database": "connected",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Saga health check failed: {e}")
        return {
            "status": "unhealthy",
            "saga_system": "error",
            "database": "disconnected",
            "error": str(e)
        }


# === ENDPOINTS DE INTEGRACIÓN DIRECTA (sin saga) ===

@router.get("/services/status")
async def get_services_status():
    """Verificar estado de todos los microservicios"""
    from infrastructure.service_clients import ServiceClients
    
    clients = ServiceClients()
    status = await clients.check_all_services()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": status
    }