"""
Service Clients - Clientes HTTP para comunicación con microservicios
"""
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .config import settings

logger = logging.getLogger(__name__)


class ServiceClients:
    """Cliente unificado para comunicación con todos los microservicios"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        
    async def _make_request(self, method: str, url: str, json_data: Optional[Dict] = None, 
                           service_name: str = "unknown") -> Dict[str, Any]:
        """Método base para hacer requests HTTP con manejo de errores"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"{method.upper()} request to {service_name}: {url}")
                
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url, json=json_data)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=json_data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                result = response.json() if response.content else {}
                logger.info(f"{service_name} response: {response.status_code}")
                return result
                
        except httpx.TimeoutException:
            error_msg = f"Timeout calling {service_name} at {url}"
            logger.error(f"{error_msg}")
            raise Exception(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"{service_name} returned {e.response.status_code}: {e.response.text}"
            logger.error(f"{error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error calling {service_name}: {str(e)}"
            logger.error(f"{error_msg}")
            raise Exception(error_msg)
    
    # === LEALTAD-CONTENIDO SERVICE ===
    
    async def create_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crear contenido base en lealtad-contenido"""
        url = f"{settings.lealtad_contenido_url}/api/contenido"
        
        # Adaptar payload al formato esperado por el servicio
        adapted_payload = {
            "titulo": payload["title"],
            "descripcion": payload["description"],
            "tipo": payload.get("content_type", "BLOG"),
            "autor": payload.get("author_name", "Sistema"),
            "metadata": {
                "author_email": payload.get("author_email", ""),
                "created_via": "BFF_SAGA"
            }
        }
        
        result = await self._make_request("POST", url, adapted_payload, "lealtad-contenido")
        
        # Adaptar respuesta
        return {
            "content_id": result.get("id", result.get("content_id", "unknown")),
            "title": result.get("titulo", payload["title"]),
            "status": result.get("estado", "CREATED")
        }
    
    async def delete_content(self, content_id: str) -> Dict[str, Any]:
        """Eliminar contenido (compensación)"""
        url = f"{settings.lealtad_contenido_url}/api/contenido/{content_id}"
        return await self._make_request("DELETE", url, service_name="lealtad-contenido")
    
    # === AFILIADOS-COMISIONES SERVICE ===
    
    async def create_affiliate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crear afiliado en afiliados-comisiones"""
        url = f"{settings.afiliados_comisiones_url}/api/afiliados"
        
        adapted_payload = {
            "name": payload["name"],
            "email": payload["email"],
            "commission_rate": payload["commission_rate"],
            "status": "ACTIVE",
            "metadata": {
                "content_id": payload.get("content_id", ""),
                "created_via": "BFF_SAGA"
            }
        }
        
        result = await self._make_request("POST", url, adapted_payload, "afiliados-comisiones")
        
        return {
            "affiliate_id": result.get("id", result.get("affiliate_id", "unknown")),
            "name": result.get("name", payload["name"]),
            "email": result.get("email", payload["email"]),
            "status": result.get("status", "ACTIVE")
        }
    
    async def deactivate_affiliate(self, affiliate_id: str) -> Dict[str, Any]:
        """Desactivar afiliado (compensación)"""
        url = f"{settings.afiliados_comisiones_url}/api/afiliados/{affiliate_id}/deactivate"
        return await self._make_request("PUT", url, {"status": "INACTIVE"}, "afiliados-comisiones")
    
    # === COLABORACIONES SERVICE ===
    
    async def create_collaboration(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crear colaboración en colaboraciones-servicio"""
        url = f"{settings.colaboraciones_url}/api/colaboraciones"
        
        adapted_payload = {
            "affiliate_id": payload["affiliate_id"],
            "tipo_colaboracion": payload.get("collaboration_type", "CONTENT_CREATION"),
            "estado": "ACTIVA",
            "metadata": {
                "affiliate_name": payload.get("affiliate_name", ""),
                "affiliate_email": payload.get("affiliate_email", ""),
                "created_via": "BFF_SAGA"
            }
        }
        
        result = await self._make_request("POST", url, adapted_payload, "colaboraciones")
        
        return {
            "collaboration_id": result.get("id", result.get("collaboration_id", "unknown")),
            "affiliate_id": result.get("affiliate_id", payload["affiliate_id"]),
            "type": result.get("tipo_colaboracion", payload.get("collaboration_type")),
            "status": result.get("estado", "ACTIVA")
        }
    
    # === MONITOREO SERVICE ===
    
    async def register_metrics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Registrar métricas en monitoreo"""
        url = f"{settings.monitoreo_url}/api/metrics"
        
        adapted_payload = {
            "event_type": payload["event_type"],
            "entity_id": payload["affiliate_id"],
            "entity_type": "AFFILIATE",
            "data": {
                "affiliate_id": payload["affiliate_id"],
                "content_id": payload.get("content_id", ""),
                "collaboration_id": payload.get("collaboration_id", ""),
                "affiliate_name": payload.get("affiliate_name", ""),
                "metadata": payload.get("metadata", {})
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        result = await self._make_request("POST", url, adapted_payload, "monitoreo")
        
        return {
            "metrics_id": result.get("id", result.get("metrics_id", "unknown")),
            "event_type": result.get("event_type", payload["event_type"]),
            "status": result.get("status", "RECORDED")
        }
    
    # === HEALTH CHECKS ===
    
    async def check_service_health(self, service_url: str, service_name: str) -> Dict[str, Any]:
        """Verificar salud de un servicio"""
        try:
            url = f"{service_url}/health"
            result = await self._make_request("GET", url, service_name=service_name)
            return {
                "service": service_name,
                "status": "healthy",
                "response": result,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "service": service_name,
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Verificar salud de todos los microservicios"""
        services = [
            (settings.lealtad_contenido_url, "lealtad-contenido"),
            (settings.afiliados_comisiones_url, "afiliados-comisiones"),
            (settings.colaboraciones_url, "colaboraciones"),
            (settings.monitoreo_url, "monitoreo")
        ]
        
        results = {}
        for service_url, service_name in services:
            results[service_name] = await self.check_service_health(service_url, service_name)
        
        return results