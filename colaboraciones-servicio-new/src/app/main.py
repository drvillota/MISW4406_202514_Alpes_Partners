from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from typing import Any
import logging

from fastapi import FastAPI
from ..infrastructure.database.connection import Base, engine
from ..infrastructure.messaging.despachadores import ColaboracionPublisher
from ..infrastructure.messaging.consumidores import EventConsumerService
from ..entrypoints.router import router
from ..infrastructure.config.settings import get_settings
import uvicorn

# Configuración central
settings = get_settings()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger("pulsar").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

app_configs: dict[str, Any] = {"title": "Colaboraciones (Pulsar)"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("Iniciando servicio de Colaboraciones...")

    try:
        # Crear tablas en la DB
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de base de datos creadas")

        # Publisher usando la URL de settings
        app.state.publisher = ColaboracionPublisher()
        logger.info(f"Publisher conectado a {settings.pulsar_url}")

        # Consumidores de eventos externos
        def simple_event_handler(domain_event):
            try:
                event_type = type(domain_event).__name__
                logger.info(f"Procesando evento externo: {event_type}")
            except Exception as e:
                logger.error(f"Error procesando evento: {e}")

        try:
            app.state.consumer_service = EventConsumerService(simple_event_handler)
            app.state.consumer_task = asyncio.create_task(
                app.state.consumer_service.start_all_consumers()
            )
            logger.info("Consumidores de eventos iniciados")
        except Exception as e:
            logger.warning(f"Consumidores no disponibles (Pulsar offline?): {e}")
            app.state.consumer_service = None
            app.state.consumer_task = None

        logger.info("Servicio Colaboraciones iniciado correctamente")

    except Exception as e:
        logger.error(f"Error iniciando servicio: {e}")
        raise

    yield

    # Cleanup
    logger.info("Cerrando servicio Colaboraciones...")
    try:
        if hasattr(app.state, "consumer_service") and app.state.consumer_service:
            await app.state.consumer_service.stop_all_consumers()
            logger.info("Consumidores detenidos")

        if hasattr(app.state, "consumer_task") and app.state.consumer_task and not app.state.consumer_task.done():
            app.state.consumer_task.cancel()
            try:
                await app.state.consumer_task
            except asyncio.CancelledError:
                logger.info("Tarea de consumidores cancelada")

        if hasattr(app.state, "publisher"):
            app.state.publisher.close()
            logger.info("Publisher cerrado")

    except Exception as e:
        logger.error(f"Error cerrando servicio: {e}")


app = FastAPI(lifespan=lifespan, **app_configs)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "src.app.main:app",
        host=settings.UVICORN_HOST,
        port=settings.UVICORN_PORT,
        reload=settings.DEBUG,
    )
