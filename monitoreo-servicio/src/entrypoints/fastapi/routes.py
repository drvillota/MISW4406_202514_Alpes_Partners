
from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import uuid4
import time
from ...infrastructure.config.settings import get_settings
from ...infrastructure.schemas.api_schema import (
    HealthResponse, 
    MetricsResponse, 
    EventResponse,
    EventType,
    Period
)
from ...application.queries import GetMetricsQuery, GetEventsQuery
from ...infrastructure.messaging.publishers import get_event_publisher

settings = get_settings()
router = APIRouter()

def get_event_handler():
    """Obtiene el handler global desde main.py"""
    from ...app.main import event_handler
    return event_handler

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="Monitoring"
    )

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(period: Period = Query(Period.DAY)):
    """Obtiene métricas básicas desde PostgreSQL"""
    handler = get_event_handler()
    query = GetMetricsQuery(period=period.value)
    result = await handler.handle_get_metrics(query)
    return MetricsResponse(**result)

@router.get("/events")
async def get_events(
    event_type: Optional[EventType] = Query(None),
    limit: int = Query(10)
):
    """Lista eventos recientes desde PostgreSQL"""
    handler = get_event_handler()
    query = GetEventsQuery(
        event_type=event_type.value if event_type else None,
        limit=limit
    )
    result = await handler.handle_get_events(query)
    return result

# --- Constantes para descriptions ---
USER_ID_DESC = "ID del usuario"
SESSION_ID_DESC = "ID de la sesión"

# --- Modelos para endpoints de desarrollo ---
class ClickEventRequest(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()), description=USER_ID_DESC)
    session_id: str = Field(default_factory=lambda: f"session_{int(time.time())}", description=SESSION_ID_DESC)
    url: str = Field(default="https://alpes.com/product/123", description="URL del click")

class ConversionEventRequest(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()), description=USER_ID_DESC)
    session_id: str = Field(default_factory=lambda: f"session_{int(time.time())}", description=SESSION_ID_DESC)
    amount: float = Field(default=100.0, description="Monto de la conversión")

class SaleEventRequest(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()), description=USER_ID_DESC)
    session_id: str = Field(default_factory=lambda: f"session_{int(time.time())}", description=SESSION_ID_DESC)
    order_id: str = Field(default_factory=lambda: f"order_{int(time.time())}", description="ID del pedido")
    amount: float = Field(default=250.0, description="Monto de la venta")

# --- Endpoints de desarrollo para publicar eventos ---
@router.post("/dev/publish/click")
async def publish_click_event(event: Optional[ClickEventRequest] = None):
    """Publicar un evento de click de prueba en Pulsar"""
    try:
        # Si no se proporciona evento, usar valores por defecto
        if event is None:
            event = ClickEventRequest()
            
        publisher = get_event_publisher()
        
        # Preparar datos con timestamp actual
        click_data = {
            "user_id": event.user_id,
            "session_id": event.session_id,
            "url": event.url,
            "timestamp": int(time.time() * 1000)  # Timestamp en milisegundos
        }
        
        # Publicar evento
        result = publisher.publish_click_event(click_data)
        
        return {
            "message": "Click event published successfully",
            "result": result,
            "tip": "Check /events endpoint to see if the event was processed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error publishing click event: {str(e)}")

@router.post("/dev/publish/conversion")
async def publish_conversion_event(event: Optional[ConversionEventRequest] = None):
    """Publicar un evento de conversión de prueba en Pulsar"""
    try:
        if event is None:
            event = ConversionEventRequest()
            
        publisher = get_event_publisher()
        
        conversion_data = {
            "user_id": event.user_id,
            "session_id": event.session_id,
            "amount": event.amount,
            "timestamp": int(time.time() * 1000)
        }
        
        result = publisher.publish_conversion_event(conversion_data)
        
        return {
            "message": "Conversion event published successfully", 
            "result": result,
            "tip": "Check /events?event_type=conversion to see if the event was processed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error publishing conversion event: {str(e)}")

@router.post("/dev/publish/sale")
async def publish_sale_event(event: Optional[SaleEventRequest] = None):
    """Publicar un evento de venta de prueba en Pulsar"""
    try:
        if event is None:
            event = SaleEventRequest()
            
        publisher = get_event_publisher()
        
        sale_data = {
            "user_id": event.user_id,
            "session_id": event.session_id,
            "order_id": event.order_id,
            "amount": event.amount,
            "timestamp": int(time.time() * 1000)
        }
        
        result = publisher.publish_sale_event(sale_data)
        
        return {
            "message": "Sale event published successfully",
            "result": result, 
            "tip": "Check /events?event_type=sale to see if the event was processed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error publishing sale event: {str(e)}")

@router.get("/dev/pulsar/status")
async def pulsar_status():
    """Verificar el estado de conexión con Pulsar"""
    try:
        publisher = get_event_publisher()
        publisher.connect()
        
        return {
            "status": "connected",
            "pulsar_url": settings.pulsar_url,
            "topics": ["clicks", "conversions", "sales"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "pulsar_url": settings.pulsar_url,
            "timestamp": datetime.now().isoformat()
        }
