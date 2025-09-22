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
        from ..application.commands import RegistrarConversionCommand
        from ..core.seedwork.message_bus import bus
        
        handlers = create_handlers(session)
        
        # Hacer handlers accesibles globalmente
        global command_handler, query_handler
        command_handler = handlers['command_handler'] 
        query_handler = handlers['query_handler']
        
        # Registrar handlers en el message bus (solo comandos para el POC)
        logger.info(f"Registrando handler para: {RegistrarConversionCommand}")
        bus.register_command(RegistrarConversionCommand, command_handler.handle_registrar_conversion)
        logger.info("Handler registrado para RegistrarConversionCommand")
        
        # Verificar que se registraron correctamente
        registered_commands = list(bus._command_handlers.keys())
        logger.info(f"Comandos registrados en el bus: {registered_commands}")
        
        logger.info("Handlers inicializados y registrados en message bus")
        
        # Inicializar consumidores de eventos con handler que ejecuta comandos
        def comprehensive_event_handler(domain_event):
            """Handler que procesa eventos de dominio ejecutando comandos apropiados"""
            try:
                from ..domain.events import AffiliateRegistered, ConversionRegistered
                from ..application.commands import RegisterAffiliateCommand, RegistrarConversionCommand
                from decimal import Decimal
                import uuid
                from datetime import datetime, timezone
                
                # Asegurar que el command_handler esté disponible
                if command_handler is None:
                    logger.error("Command handler no está inicializado")
                    return
                
                event_type = type(domain_event).__name__
                logger.info(f"Procesando evento de dominio: {event_type}")
                
                if isinstance(domain_event, AffiliateRegistered):
                    # Ejecutar comando para registrar afiliado
                    try:
                        cmd = RegisterAffiliateCommand(
                            name=domain_event.name,
                            email=domain_event.email,
                            commission_rate=Decimal(str(domain_event.commission_rate))
                        )
                        
                        result = command_handler.handle_register_affiliate(cmd)
                        logger.info(f"Afiliado registrado desde evento: {result}")
                        
                    except Exception as e:
                        logger.error(f"Error registrando afiliado desde evento: {e}")
                
                elif isinstance(domain_event, ConversionRegistered):
                    # Ejecutar comando para procesar conversión
                    try:
                        cmd = RegistrarConversionCommand(
                            affiliate_id=uuid.UUID(domain_event.affiliate_id),
                            event_type='COMPRA',  # Mapear según el contexto
                            monto=domain_event.amount,
                            moneda=domain_event.currency,
                            occurred_at=datetime.fromtimestamp(domain_event.timestamp, tz=timezone.utc)
                        )
                        
                        result = command_handler.handle_registrar_conversion(cmd)
                        logger.info(f"Conversión procesada desde evento: {result}")
                        
                    except Exception as e:
                        logger.error(f"Error procesando conversión desde evento: {e}")
                
                # Para eventos personalizados que publicamos
                elif hasattr(domain_event, '__dict__'):
                    # Manejar eventos que no son del dominio estándar (eventos custom de Pulsar)
                    event_type_field = getattr(domain_event, 'event_type', None)
                    
                    if event_type_field == 'AffiliateRegistered':
                        try:
                            cmd = RegisterAffiliateCommand(
                                name=getattr(domain_event, 'name', ''),
                                email=getattr(domain_event, 'email', ''),
                                commission_rate=Decimal(str(getattr(domain_event, 'commission_rate', 0)))
                            )
                            
                            result = command_handler.handle_register_affiliate(cmd)
                            logger.info(f"Afiliado registrado desde evento custom: {result}")
                            
                        except Exception as e:
                            logger.error(f"Error registrando afiliado desde evento custom: {e}")
                    
                    elif event_type_field == 'ConversionRequested':
                        try:
                            cmd = RegistrarConversionCommand(
                                affiliate_id=uuid.UUID(getattr(domain_event, 'affiliate_id', '')),
                                event_type=getattr(domain_event, 'conversion_type', 'COMPRA'),
                                monto=getattr(domain_event, 'amount', 0),
                                moneda=getattr(domain_event, 'currency', 'USD'),
                                occurred_at=datetime.fromisoformat(getattr(domain_event, 'occurred_at', '').replace('Z', '+00:00'))
                            )
                            
                            result = command_handler.handle_registrar_conversion(cmd)
                            logger.info(f"Conversión procesada desde evento custom: {result}")
                            
                        except Exception as e:
                            logger.error(f"Error procesando conversión desde evento custom: {e}")
                
                else:
                    logger.info(f"Evento no procesable: {event_type}")
                    
            except Exception as e:
                logger.error(f"Error general procesando evento: {e}")
                import traceback
                traceback.print_exc()
        
        # Crear consumidores pero solo si Pulsar está disponible
        try:
            app.state.consumer_service = EventConsumerService(comprehensive_event_handler)
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
