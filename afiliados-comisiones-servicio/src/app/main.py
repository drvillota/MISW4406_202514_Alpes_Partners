from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from typing import Any
import logging

from fastapi import FastAPI
from ..infrastructure.config import UVICORN_PORT
from ..infrastructure.db.sqlalchemy import Base, engine, SessionLocal
from ..infrastructure.db.repositories import AffiliateRepository, CommissionRepository, ConversionEventRepository
from ..infrastructure.messaging.despachadores import IntegracionPublisher
from ..infrastructure.messaging.consumidores import EventConsumerService
from ..application.handlers import create_handlers
from ..entrypoints.fastapi.routes import router
import uvicorn

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reducir verbosidad de logs de Pulsar y otros componentes
logging.getLogger("pulsar").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)



app_configs: dict[str, Any] = {"title": "Afiliados — Comisiones (Pulsar)"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("Iniciando servicio de afiliados y comisiones...")
    
    try:
        # Crear tablas de base de datos
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de base de datos creadas")
        
        # Inicializar publisher de eventos
        app.state.publisher = IntegracionPublisher()
        logger.info("Publisher de eventos inicializado")
        
        # === INICIALIZACIÓN DE HANDLERS (movido desde on_startup) ===
        # Crear sesión de base de datos
        session = SessionLocal()
        
        # Crear handlers simplificados
        from ..application.handlers import create_handlers
        from ..application.commands import RegistrarConversionCommand, ConsultarComisionesPorAfiliadoQuery
        from ..core.seedwork.message_bus import bus
        
        handlers = create_handlers(session)
        
        # Hacer handlers accesibles globalmente
        global command_handler, query_handler
        command_handler = handlers['command_handler'] 
        query_handler = handlers['query_handler']
        
        # Registrar handlers en el message bus
        logger.info(f"🔧 Registrando handler para: {RegistrarConversionCommand}")
        bus.register_command(RegistrarConversionCommand, command_handler.handle_registrar_conversion)
        logger.info(f"Handler registrado para RegistrarConversionCommand")
        
        # Crear un wrapper para las consultas usando la instancia local
        qry_handler = query_handler
        
        def query_wrapper(query):
            if isinstance(query, ConsultarComisionesPorAfiliadoQuery):
                return qry_handler.handle_consultar_comisiones_por_afiliado(query)
            else:
                return qry_handler.handle_list_commissions(query)
        
        logger.info(f"Registrando handler para: {ConsultarComisionesPorAfiliadoQuery}")
        bus.register_command(ConsultarComisionesPorAfiliadoQuery, query_wrapper)
        logger.info(f"Handler registrado para ConsultarComisionesPorAfiliadoQuery")
        
        # Verificar que se registraron correctamente
        registered_commands = list(bus._command_handlers.keys())
        logger.info(f"Comandos registrados en el bus: {registered_commands}")
        
        logger.info("Handlers inicializados y registrados en message bus")
        
        # Inicializar consumidores de eventos (simplificado)
        def simple_event_handler(domain_event):
            """Handler simplificado para procesar eventos de dominio"""
            try:
                event_type = type(domain_event).__name__
                logger.info(f"Procesando evento: {event_type}")
                # Solo logear los eventos por ahora para reducir complejidad
            except Exception as e:
                logger.error(f"Error procesando evento: {e}")
        
        # Crear consumidores pero solo si Pulsar está disponible
        try:
            app.state.consumer_service = EventConsumerService(simple_event_handler)
            # Iniciar en background (no bloquear si Pulsar no está disponible)
            app.state.consumer_task = asyncio.create_task(
                app.state.consumer_service.start_all_consumers()
            )
            logger.info("Consumidores de eventos iniciados")
        except Exception as e:
            logger.warning(f"Consumidores no disponibles (Pulsar offline?): {e}")
            app.state.consumer_service = None
            app.state.consumer_task = None
        
        logger.info("Servicio iniciado correctamente")
        
    except Exception as e:
        logger.error(f"Error iniciando servicio: {e}")
        raise
    
    yield
    
    # Cleanup al cerrar la aplicación
    logger.info("Cerrando servicio...")
    
    try:
        # Detener consumidores
        if hasattr(app.state, 'consumer_service') and app.state.consumer_service:
            await app.state.consumer_service.stop_all_consumers()
            logger.info("Consumidores detenidos")
        
        # Cancelar tarea de consumidores
        if hasattr(app.state, 'consumer_task') and app.state.consumer_task and not app.state.consumer_task.done():
            app.state.consumer_task.cancel()
            try:
                await app.state.consumer_task
            except asyncio.CancelledError:
                logger.info("Tarea de consumidores cancelada")
                raise
        
        # Cerrar publisher
        if hasattr(app.state, 'publisher'):
            app.state.publisher.close()
            logger.info("Publisher cerrado")
            
    except Exception as e:
        logger.error(f"Error cerrando servicio: {e}")

app = FastAPI(lifespan=lifespan, **app_configs)
app.include_router(router)

# Variables globales para handlers (simplificado)
command_handler = None
query_handler = None

if __name__ == "__main__":
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=UVICORN_PORT, reload=False)
