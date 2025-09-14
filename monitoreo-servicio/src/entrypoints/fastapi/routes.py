
from __future__ import annotations
from fastapi import APIRouter, Query
from datetime import datetime
from typing import Optional
from ...infrastructure.config.settings import get_settings
from ...infrastructure.schemas.api_schema import (
    HealthResponse, 
    MetricsResponse, 
    EventResponse,
    EventType,
    Period
)
from ...application.queries import GetMetricsQuery, GetEventsQuery

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
        service=settings.APP_NAME
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
