
from __future__ import annotations
import logging
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from ...core.seedwork.message_bus import bus
from ...application.commands import RegistrarConversionCommand
from ...application.queries import ConsultarComisionesPorAfiliadoQuery
from ...infrastructure.db.sqlalchemy import SessionLocal
from ...infrastructure.db.models import AffiliateModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Endpoints utilitarios para demo ---
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

class SeedAffiliateIn(BaseModel):
    id: UUID | None = None
    name: str  # Cambió de 'nombre' a 'name'
    email: str  # Agregado campo email requerido
    commission_rate: float  # Cambió de 'tasa_comision' a 'commission_rate'

# --- Endpoints principales del demo ---

@router.get("/affiliates/{affiliate_id}/commissions")
def consultar_comisiones_afiliado(
    affiliate_id: UUID,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    session: Session = Depends(get_session)
):
    """Consultar comisiones de un afiliado específico"""
    logger.info(f"Consultando comisiones para afiliado: {affiliate_id}")
    
    try:
        # Usar el query handler directamente (no necesita pasar por message bus para queries)
        from ...application.handlers import create_handlers
        
        handlers = create_handlers(session)
        query_handler = handlers['query_handler']
        
        # Crear la query
        query = ConsultarComisionesPorAfiliadoQuery(
            affiliate_id=affiliate_id,
            desde=desde,
            hasta=hasta
        )
        
        # Ejecutar query usando el handler directamente
        commissions = query_handler.handle_list_commissions(query)
        
        # Formatear respuesta
        commission_list = []
        for commission in commissions:
            commission_list.append({
                "id": str(commission.id),
                "affiliate_id": str(commission.affiliate_id),
                "amount": float(commission.amount),
                "currency": commission.currency,
                "conversion_id": str(commission.conversion_id),
                "created_at": commission.created_at.isoformat() if commission.created_at else None,
                "status": getattr(commission, 'status', 'active')
            })
        
        return {
            "affiliate_id": str(affiliate_id),
            "total_commissions": len(commission_list),
            "commissions": commission_list,
            "query_period": {
                "desde": desde.isoformat() if desde else None,
                "hasta": hasta.isoformat() if hasta else None
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error consultando comisiones: {e}")
        logger.error("Full traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error querying commissions: {str(e)}")

@router.get("/affiliates/{affiliate_id}")
def consultar_afiliado(affiliate_id: UUID, session: Session = Depends(get_session)):
    """Consultar datos básicos de un afiliado"""
    logger.info(f"Consultando datos del afiliado: {affiliate_id}")
    
    try:
        # Consultar directamente en la base de datos para este endpoint simple
        affiliate = session.query(AffiliateModel).filter(AffiliateModel.id == affiliate_id).first()
        
        if not affiliate:
            raise HTTPException(status_code=404, detail=f"Affiliate {affiliate_id} not found")
        
        return {
            "id": str(affiliate.id),
            "name": affiliate.name,
            "email": affiliate.email,
            "commission_rate": float(affiliate.commission_rate),
            "created_at": affiliate.created_at.isoformat() if affiliate.created_at else None,
            "status": "active",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error consultando afiliado: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying affiliate: {str(e)}")

@router.post("/dev/conversions")
def registrar_conversion(payload: ConversionIn):
    logger.info(f"Publishing conversion request for affiliate: {payload.affiliate_id}")
    
    try:
        # En lugar de ejecutar comando directamente, publicar evento para que los consumidores lo procesen
        from ...infrastructure.messaging.despachadores import IntegracionPublisher
        
        publisher = IntegracionPublisher()
        
        conversion_data = {
            'affiliate_id': payload.affiliate_id,
            'event_type': payload.event_type,
            'monto': payload.monto,
            'moneda': payload.moneda,
            'occurred_at': (payload.occurred_at or datetime.now(timezone.utc)).isoformat()
        }
        
        resultado = publisher.publicar_conversion_solicitada(conversion_data)
        publisher.close()
        
        if resultado:
            logger.info("Conversion request event published successfully")
            return {
                "status": "requested",
                "message": "Conversion request published to event stream",
                "affiliate_id": str(payload.affiliate_id),
                "event_type": payload.event_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error("Failed to publish conversion request event")
            raise HTTPException(status_code=500, detail="Failed to publish conversion request")
            
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        logger.error("Full traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing conversion request: {str(e)}") 


@router.post("/dev/seed_affiliate")
def seed_affiliate(payload: SeedAffiliateIn, session: Session = Depends(get_session)):
    logger.info(f"Publishing affiliate registration event for: {payload.name}")
    
    try:
        # En lugar de insertar directamente en la DB, publicar evento
        from ...infrastructure.messaging.despachadores import IntegracionPublisher
        
        publisher = IntegracionPublisher()
        
        affiliate_data = {
            'id': payload.id or uuid4(),
            'name': payload.name,
            'email': payload.email,
            'commission_rate': payload.commission_rate
        }
        
        resultado = publisher.publicar_afiliado_registrado(affiliate_data)
        publisher.close()
        
        if resultado:
            logger.info("Affiliate registration event published successfully")
            return {
                "status": "requested", 
                "message": "Affiliate registration published to event stream",
                "affiliate_id": str(affiliate_data['id'])
            }
        else:
            logger.error("Failed to publish affiliate registration event")
            raise HTTPException(status_code=500, detail="Failed to publish affiliate registration")
            
    except Exception as e:
        logger.error(f"Error publishing affiliate registration: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing affiliate registration: {str(e)}")

# --- Endpoints de diagnóstico para Pulsar ---
@router.get("/dev/pulsar/health")
def verificar_estado_pulsar():
    """Verificar el estado de conexión con Pulsar"""
    try:
        from ...infrastructure.messaging.despachadores import Despachador
        despachador = Despachador()
        despachador.connect()
        
        return {
            "status": "connected" if despachador.is_connected() else "disconnected",
            "broker_url": despachador.broker_url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/dev/pulsar/create-topics")
def crear_topics_pulsar():
    """Crear los topics necesarios en Pulsar"""
    try:
        import pulsar
        from ...infrastructure.schema.utils import broker_host
        
        client = pulsar.Client(f'pulsar://{broker_host()}:6650')
        
        topics_to_create = [
            "persistent://public/default/affiliate-events",
            "persistent://public/default/conversion-events",
            "persistent://public/default/commission"
        ]
        
        created_topics = []
        errors = []
        
        for topic in topics_to_create:
            try:
                # Crear un productor temporal para el topic (esto lo crea si no existe)
                producer = client.create_producer(topic)
                producer.close()
                created_topics.append(topic)
                logger.info(f"Topic creado/verificado: {topic}")
            except Exception as e:
                errors.append({"topic": topic, "error": str(e)})
                logger.error(f"Error creando topic {topic}: {e}")
        
        client.close()
        
        return {
            "status": "completed",
            "created_topics": created_topics,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/dev/pulsar/topics")
def listar_topics():
    """Listar todos los topics existentes en Pulsar"""
    try:
        import requests
        from ...infrastructure.schema.utils import broker_host
        
        # Usar la API REST de Pulsar para listar topics
        admin_url = f"http://{broker_host()}:8080"
        response = requests.get(f"{admin_url}/admin/v2/persistent/public/default", timeout=10)
        
        if response.status_code == 200:
            topics = response.json()
            return {
                "status": "success",
                "topics": topics,
                "count": len(topics),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
