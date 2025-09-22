"""
Saga Orchestrator - Orquestación de transacciones distribuidas
"""
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timezone

from .config import settings
from .saga_log import SagaLogRepository
from .service_clients import ServiceClients

logger = logging.getLogger(__name__)


class SagaOrchestrator:
    """Orquestador principal de sagas"""
    
    def __init__(self, saga_repo: SagaLogRepository):
        self.saga_repo = saga_repo
        self.clients = ServiceClients()
    
    async def execute_complete_affiliate_registration(self, saga_id: str, request_data) -> bool:
        """
        🎯 Ejecuta la saga completa de registro de afiliado
        
        Pasos:
        1. Crear contenido base en lealtad-contenido
        2. Validar y crear afiliado en afiliados-comisiones
        3. Crear perfil de colaboración en colaboraciones-servicio
        4. Registrar métricas iniciales en monitoreo
        """
        try:
            logger.info(f"Iniciando saga {saga_id}: CompleteAffiliateRegistration")
            
            # PASO 1: Crear contenido base
            step_1_result = await self._step_1_create_base_content(saga_id, request_data)
            if not step_1_result["success"]:
                await self.compensate_saga(saga_id, step_1_result["error"])
                return False
            
            # PASO 2: Crear y validar afiliado
            step_2_result = await self._step_2_create_affiliate(saga_id, request_data, step_1_result["data"])
            if not step_2_result["success"]:
                await self._compensate_step_1(saga_id, step_1_result["data"])
                await self.compensate_saga(saga_id, step_2_result["error"])
                return False
            
            # PASO 3: Crear colaboración
            step_3_result = await self._step_3_create_collaboration(saga_id, request_data, step_2_result["data"])
            if not step_3_result["success"]:
                await self._compensate_step_2(saga_id, step_2_result["data"])
                await self._compensate_step_1(saga_id, step_1_result["data"])
                await self.compensate_saga(saga_id, step_3_result["error"])
                return False
            
            # PASO 4: Registrar métricas finales
            step_4_result = await self._step_4_register_metrics(saga_id, request_data, {
                "content_id": step_1_result["data"]["content_id"],
                "affiliate_id": step_2_result["data"]["affiliate_id"],
                "collaboration_id": step_3_result["data"]["collaboration_id"]
            })
            if not step_4_result["success"]:
                # Solo loguear, no compensar todo por métricas
                logger.warning(f"Métricas fallaron pero saga continúa: {step_4_result['error']}")
            
            # COMPLETAR SAGA
            await self.saga_repo.log_step(
                saga_id, "saga_completed_final", "COMPLETED",
                {
                    "content_id": step_1_result["data"]["content_id"],
                    "affiliate_id": step_2_result["data"]["affiliate_id"],
                    "collaboration_id": step_3_result["data"]["collaboration_id"],
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"Saga {saga_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Critical error in saga {saga_id}: {e}")
            await self.compensate_saga(saga_id, f"Critical error: {str(e)}")
            return False
    
    async def _step_1_create_base_content(self, saga_id: str, request_data) -> Dict[str, Any]:
        """Paso 1: Crear contenido base en lealtad-contenido"""
        try:
            logger.info(f"📝 Step 1: Creating base content for saga {saga_id}")
            
            # Llamar al servicio de lealtad-contenido
            payload = {
                "title": request_data.content_title,
                "description": request_data.content_description,
                "content_type": request_data.content_type,
                "author_name": request_data.affiliate_name,
                "author_email": request_data.affiliate_email
            }
            
            result = await self.clients.create_content(payload)
            
            await self.saga_repo.log_step(
                saga_id, "create_base_content", "COMPLETED",
                {"content_id": result["content_id"], "service": "lealtad-contenido"}
            )
            
            return {"success": True, "data": result}
            
        except Exception as e:
            error_msg = f"Failed to create base content: {str(e)}"
            await self.saga_repo.log_step(
                saga_id, "create_base_content", "FAILED", {}, error_msg
            )
            return {"success": False, "error": error_msg}
    
    async def _step_2_create_affiliate(self, saga_id: str, request_data, step_1_data) -> Dict[str, Any]:
        """Paso 2: Crear y validar afiliado en afiliados-comisiones"""
        try:
            logger.info(f"👤 Step 2: Creating affiliate for saga {saga_id}")
            
            payload = {
                "name": request_data.affiliate_name,
                "email": request_data.affiliate_email,
                "commission_rate": request_data.commission_rate,
                "content_id": step_1_data["content_id"]
            }
            
            result = await self.clients.create_affiliate(payload)
            
            await self.saga_repo.log_step(
                saga_id, "create_affiliate", "COMPLETED",
                {"affiliate_id": result["affiliate_id"], "service": "afiliados-comisiones"}
            )
            
            return {"success": True, "data": result}
            
        except Exception as e:
            error_msg = f"Failed to create affiliate: {str(e)}"
            await self.saga_repo.log_step(
                saga_id, "create_affiliate", "FAILED", {}, error_msg
            )
            return {"success": False, "error": error_msg}
    
    async def _step_3_create_collaboration(self, saga_id: str, request_data, step_2_data) -> Dict[str, Any]:
        """Paso 3: Crear colaboración en colaboraciones-servicio"""
        try:
            logger.info(f"🤝 Step 3: Creating collaboration for saga {saga_id}")
            
            payload = {
                "affiliate_id": step_2_data["affiliate_id"],
                "collaboration_type": request_data.collaboration_type,
                "affiliate_name": request_data.affiliate_name,
                "affiliate_email": request_data.affiliate_email
            }
            
            result = await self.clients.create_collaboration(payload)
            
            await self.saga_repo.log_step(
                saga_id, "create_collaboration", "COMPLETED",
                {"collaboration_id": result["collaboration_id"], "service": "colaboraciones"}
            )
            
            return {"success": True, "data": result}
            
        except Exception as e:
            error_msg = f"Failed to create collaboration: {str(e)}"
            await self.saga_repo.log_step(
                saga_id, "create_collaboration", "FAILED", {}, error_msg
            )
            return {"success": False, "error": error_msg}
    
    async def _step_4_register_metrics(self, saga_id: str, request_data, combined_data) -> Dict[str, Any]:
        """Paso 4: Registrar métricas en monitoreo"""
        try:
            logger.info(f"Step 4: Registering metrics for saga {saga_id}")
            
            payload = {
                "event_type": "AFFILIATE_REGISTERED",
                "affiliate_id": combined_data["affiliate_id"],
                "content_id": combined_data["content_id"],
                "collaboration_id": combined_data["collaboration_id"],
                "affiliate_name": request_data.affiliate_name,
                "metadata": {
                    "commission_rate": request_data.commission_rate,
                    "collaboration_type": request_data.collaboration_type,
                    "saga_id": saga_id
                }
            }
            
            result = await self.clients.register_metrics(payload)
            
            await self.saga_repo.log_step(
                saga_id, "register_metrics", "COMPLETED",
                {"metrics_id": result.get("metrics_id", "unknown"), "service": "monitoreo"}
            )
            
            return {"success": True, "data": result}
            
        except Exception as e:
            error_msg = f"Failed to register metrics: {str(e)}"
            await self.saga_repo.log_step(
                saga_id, "register_metrics", "FAILED", {}, error_msg
            )
            return {"success": False, "error": error_msg}
    
    # === COMPENSACIONES ===
    
    async def compensate_saga(self, saga_id: str, error_message: str) -> None:
        """Iniciar proceso de compensación general"""
        logger.warning(f"Starting compensation for saga {saga_id}: {error_message}")
        
        await self.saga_repo.log_compensation(
            saga_id, "saga_compensation_started", error_message,
            {"compensation_initiated_at": datetime.now(timezone.utc).isoformat()}
        )
    
    async def _compensate_step_1(self, saga_id: str, step_data: Dict[str, Any]) -> None:
        """Compensar paso 1: eliminar contenido creado"""
        try:
            if "content_id" in step_data:
                await self.clients.delete_content(step_data["content_id"])
                await self.saga_repo.log_step(
                    saga_id, "compensate_create_content", "COMPLETED",
                    {"compensated_content_id": step_data["content_id"]}
                )
        except Exception as e:
            await self.saga_repo.log_step(
                saga_id, "compensate_create_content", "FAILED", {}, str(e)
            )
    
    async def _compensate_step_2(self, saga_id: str, step_data: Dict[str, Any]) -> None:
        """Compensar paso 2: desactivar afiliado"""
        try:
            if "affiliate_id" in step_data:
                await self.clients.deactivate_affiliate(step_data["affiliate_id"])
                await self.saga_repo.log_step(
                    saga_id, "compensate_create_affiliate", "COMPLETED",
                    {"compensated_affiliate_id": step_data["affiliate_id"]}
                )
        except Exception as e:
            await self.saga_repo.log_step(
                saga_id, "compensate_create_affiliate", "FAILED", {}, str(e)
            )