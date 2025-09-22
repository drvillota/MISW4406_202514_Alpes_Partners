# src/app/main.py
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from typing import Any
import logging

from fastapi import FastAPI
from infrastructure.database.connection import Base, engine, SessionLocal
from infrastructure.messaging.despachadores import Despachador, ColaboracionPublisher
from infrastructure.messaging.consumidores import ColaboracionEventConsumer
from entrypoints.util_router import router as util_router
from infrastructure.config.settings import get_settings
from core.seedworks.message_bus import bus
from application.handlers import create_handlers
from application.comandos import (
    IniciarColaboracionComando,
    FirmarContratoComando,
    CancelarContratoComando,
    FinalizarColaboracionComando,
    RegistrarPublicacionComando,
)
from application.queries import ConsultarColaboracionQuery, ListarColaboracionesQuery
import uvicorn
import pulsar
from pulsar.schema import AvroSchema
from infrastructure.schemas.schemas import (
    PublicacionRegistradaSchema,
    ColaboracionIniciadaSchema,
)

# Configuración central
settings = get_settings()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger("pulsar").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

app_configs: dict[str, Any] = {"title": "Colaboraciones (Pulsar)"}


def ensure_topic(topic_name: str, schema_class) -> None:
    """Forzar creación del tópico con schema Avro"""
    try:
        client = pulsar.Client(settings.pulsar_url)
        producer = client.create_producer(
            topic_name,
            schema=AvroSchema(schema_class),
        )
        producer.close()
        client.close()
        logger.info(f"Tópico asegurado con Avro: {topic_name}")
    except Exception as e:
        logger.error(f"No se pudo asegurar el tópico {topic_name}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("Iniciando servicio de Colaboraciones...")
    session = None

    try:
        # Crear tablas en DB
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de base de datos creadas")

        # Asegurar tópicos con Avro antes de arrancar consumers
        ensure_topic("persistent://public/default/publicaciones-registradas", PublicacionRegistradaSchema)
        ensure_topic("persistent://public/default/colaboracion-eventos", ColaboracionIniciadaSchema)

        # Instancia única del despachador
        despachador = Despachador()
        despachador.connect()

        # Publisher compartiendo el mismo despachador
        app.state.publisher = ColaboracionPublisher(despachador)
        logger.info(f"Publisher conectado a {settings.pulsar_url}")

        # Crear sesión y registrar handlers
        session = SessionLocal()
        handlers = create_handlers(session)

        cmd_handler = handlers["command_handler"]
        bus.register_command(IniciarColaboracionComando, cmd_handler.handle_iniciar_colaboracion)
        bus.register_command(FirmarContratoComando, cmd_handler.handle_firmar_contrato)
        bus.register_command(CancelarContratoComando, cmd_handler.handle_cancelar_contrato)
        bus.register_command(FinalizarColaboracionComando, cmd_handler.handle_finalizar_colaboracion)
        bus.register_command(RegistrarPublicacionComando, cmd_handler.handle_registrar_publicacion)

        app.state.query_handler = handlers["query_handler"]
        logger.info("Handlers de comandos y queries registrados en el bus")

        # Consumidores Pulsar
        def simple_event_handler(domain_event):
            try:
                logger.info(f"Procesando evento externo: {type(domain_event).__name__}")
            except Exception as e:
                logger.error(f"Error procesando evento: {e}")

        try:
            app.state.consumer_service = ColaboracionEventConsumer(simple_event_handler)
            app.state.consumer_task = asyncio.create_task(
                app.state.consumer_service.start_all_consumers()
            )
            logger.info("Consumidores de eventos iniciados")
        except Exception as e:
            logger.warning(f"Consumidores no disponibles: {e}")
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

        if session:
            session.close()
    except Exception as e:
        logger.error(f"Error cerrando servicio: {e}")


app = FastAPI(lifespan=lifespan, **app_configs)
app.include_router(util_router, prefix="/utils", tags=["Utils"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.UVICORN_HOST,
        port=settings.UVICORN_PORT,
        reload=settings.DEBUG,
    )
