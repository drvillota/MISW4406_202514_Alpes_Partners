from __future__ import annotations
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from ..infrastructure.config.settings import get_settings
from ..infrastructure.database.connection import Base, engine, SessionLocal
from ..infrastructure.database.repositories import EventRepositorySQL, EventQueryRepositorySQL
from ..infrastructure.messaging.consumers import EventConsumerService
from ..application.handlers import EventHandler
from ..entrypoints.fastapi.routes import router
import uvicorn

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
tasks = []

# Instancia global del handler (con repositorios SQL)
event_handler = None

async def handle_event(event):
    """Handler para procesar eventos desde Pulsar"""
    from ..application.commands import RecordEventCommand
    
    # Convertir el evento simple a comando de aplicación
    command = RecordEventCommand(
        event_type=event.event_type,
        user_id=event.user_id,
        session_id=event.session_id,
        metadata=event.metadata,
        occurred_at=event.occurred_at
    )
    
    # Procesar usando el handler de aplicación
    result = await event_handler.handle_record_event(command)
    logger.info(f"Event processed: {result}")
    
    return result

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global event_handler
    
    # Crear tablas
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Crear sesión de base de datos
    session = SessionLocal()
    
    # Instanciar repositorios
    event_repo = EventRepositorySQL(session)
    query_repo = EventQueryRepositorySQL(session)
    
    # Instanciar handler con repositorios
    event_handler = EventHandler(event_repo, query_repo)
    logger.info("Event handler initialized with SQL repositories")
    
    # Iniciar consumidores de eventos
    consumer_service = EventConsumerService(event_handler=handle_event)
    consumer_task = asyncio.create_task(consumer_service.start_all_consumers())
    tasks.append(consumer_task)
    logger.info("Event consumers started")
    
    yield
    
    # Cleanup al cerrar la aplicación
    session.close()  # Cerrar sesión DB
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    logger.info("Application shutdown complete")

app_configs: dict[str, Any] = {
    "title": "Monitoreo Service - Analytics & Monitoring Service",
    "description": "Servicio de monitoreo y análisis de eventos (conversiones, clicks, ventas)",
    "version": "1.0.0"
}

app = FastAPI(lifespan=lifespan, **app_configs)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "src.app.main:app", 
        host=settings.UVICORN_HOST, 
        port=settings.UVICORN_PORT, 
        reload=settings.DEBUG,  # Usar DEBUG en lugar de is_development
        log_level="info"  # Valor fijo en lugar de settings.LOG_LEVEL
    )
