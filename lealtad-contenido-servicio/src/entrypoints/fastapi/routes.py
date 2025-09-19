
from __future__ import annotations
import logging
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from ...core.seedwork.message_bus import bus
from ...application.commands import RegistrarContentCommand
from ...application.commands import ConsultarContenidosPorAfiliadoQuery
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

class ContentIn(BaseModel):
    affiliate_id: UUID
    titulo: str
    contenido: str
    tipo: str
    publicar: str = "No"
    created_at: datetime | None = None

@router.post("/contents")
def registrar_contenido(payload: ContentIn):
    logger.info(f"Processing content registration for affiliate: {payload.affiliate_id}")

    cmd = RegistrarContentCommand(
        affiliate_id=payload.affiliate_id,
        titulo=payload.titulo,
        contenido=payload.contenido,
        tipo=payload.tipo,
        publicar=payload.publicar,
        created_at=payload.created_at or datetime.now(timezone.utc)
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

@router.get("/affiliates/{affiliate_id}/contents")
def listar_contenidos(affiliate_id: UUID, desde: datetime | None = None, hasta: datetime | None = None):
    # Delegar al handler de consulta registrado en app.main
    try:
        from ...app.main import query_handler
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No query handler: {e}")
    if not query_handler:
        raise HTTPException(status_code=500, detail="Query handler not initialized yet")
    q = ConsultarContenidosPorAfiliadoQuery(affiliate_id=affiliate_id, desde=desde, hasta=hasta)
    return query_handler.handle_consultar_contenido_por_afiliado(q)

# --- Endpoints utilitarios para demo ---
class SeedAffiliateIn(BaseModel):
    id: UUID | None = None
    name: str  # Cambió de 'nombre' a 'name'
    email: str  # Agregado campo email requerido
    commission_rate: float  # Cambió de 'tasa_comision' a 'commission_rate'
    leal: str

@router.post("/dev/seed_affiliate")
def seed_affiliate(payload: SeedAffiliateIn, session: Session = Depends(get_session)):
    m = AffiliateModel(
        id=payload.id or uuid4(), 
        name=payload.name,  # Cambió de 'nombre' a 'name'
        email=payload.email,  # Agregado campo email
        commission_rate=payload.commission_rate,  # Cambió de 'tasa_comision' a 'commission_rate'
        leal=payload.leal
    )
    session.add(m); session.commit()
    return {"affiliate_id": str(m.id)}

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

@router.post("/dev/pulsar/test-publish")
def probar_publicacion():
    """Probar la publicación de un evento de prueba"""
    try:
        from ...infrastructure.messaging.despachadores import IntegracionPublisher
        
        publisher = IntegracionPublisher()
        
        # Crear evento de prueba
        class EventoPrueba:
            def __init__(self):
                self.id = str(uuid4())
                self.affiliate_id = str(uuid4())
                self.valor = 100.0
                self.moneda = "USD"
        
        evento = EventoPrueba()
        resultado = publisher.publicar_contenido_creado(evento)
        
        publisher.close()
        
        return {
            "status": "success" if resultado else "failed",
            "event_id": evento.id,
            "message": "Test event published" if resultado else "Failed to publish test event",
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
            "persistent://public/default/comisiones.creadas",
            "persistent://public/default/affiliate-events",
            "persistent://public/default/conversion-events",
            "persistent://public/default/commission-events"
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
