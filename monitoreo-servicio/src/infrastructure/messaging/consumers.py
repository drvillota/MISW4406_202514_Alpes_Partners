"""Consumidores de eventos mejorados basados en afiliados-comisiones-servicio

En este archivo se definen los consumidores optimizados con mejor manejo de errores,
reconexión automática y mapeo de eventos.

"""

import logging
import traceback
import pulsar
import _pulsar
import asyncio
from typing import Callable, Any, Dict, Awaitable
import aiopulsar
from pulsar.schema import AvroSchema, Record
from ..schemas.event_schema import ConversionEventSchema, ClickEventSchema, SaleEventSchema, PublicacionRegistradaSchema
from ..config.settings import get_settings
from .event_mapper import PulsarEventMapper

logger = logging.getLogger(__name__)
settings = get_settings()

class EventConsumerService:
    """Servicio mejorado para consumir eventos de las colas de Pulsar"""
    
    def __init__(self, event_handler: Callable[[Any], Awaitable[Any]]):
        self.event_handler = event_handler
        self.event_mapper = PulsarEventMapper()
        self.is_running = False
        self.consumer_tasks = []

    async def start_all_consumers(self):
        """Inicia todos los consumidores concurrentemente"""
        try:
            self.is_running = True
            
            # Primero crear los tópicos si no existen
            await self._ensure_topics_exist()
            
            self.consumer_tasks = [
                asyncio.create_task(self.consume_conversions()),
                asyncio.create_task(self.consume_clicks()),
                asyncio.create_task(self.consume_sales()),
                asyncio.create_task(self.consume_publicaciones_registradas())
            ]
            
            logger.info("Starting all event consumers...")
            await asyncio.gather(*self.consumer_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error starting consumers: {e}")
            traceback.print_exc()
            await self.stop_all_consumers()

    async def _ensure_topics_exist(self):
        """Crear tópicos si no existen"""
        topics_to_create = [
            "persistent://public/default/conversion-events",
            "persistent://public/default/clicks",
            "persistent://public/default/sales",
            "persistent://public/default/publicaciones-registradas"
        ]
        
        try:
            client = await aiopulsar.connect(f'{settings.pulsar_url}')
            
            for topic in topics_to_create:
                try:
                    # Intentar crear un productor para el tópico (esto lo crea si no existe)
                    producer = await client.create_producer(topic)
                    await producer.close()
                    logger.info(f"Tópico asegurado: {topic}")
                except Exception as e:
                    logger.warning(f"No se pudo asegurar tópico {topic}: {e}")
            
            await client.close()
            logger.info("Verificación de tópicos completada")
            
        except Exception as e:
            logger.warning(f"No se pudieron verificar tópicos (Pulsar offline?): {e}")
            # Continuar sin tópicos - el servicio principal debe funcionar

    async def stop_all_consumers(self):
        """Detiene todos los consumidores"""
        logger.info("Stopping all consumers...")
        self.is_running = False
        
        for task in self.consumer_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info("Consumer task cancelled during shutdown")
                    raise

    async def consume_conversions(self):
        """Consume eventos de conversiones"""
        await self._consume_topic_with_retry(
            topic="conversion-events",
            subscription="monitor-conversions",
            event_mapper=self.event_mapper.map_conversion_event,
            consumer_type=_pulsar.ConsumerType.Shared
        )

    async def consume_clicks(self):
        """Consume eventos de clicks"""
        await self._consume_topic_with_retry(
            topic="clicks", 
            subscription="monitor-clicks",
            event_mapper=self.event_mapper.map_click_event,
            consumer_type=_pulsar.ConsumerType.Shared
        )

    async def consume_sales(self):
        """Consume eventos de ventas"""
        await self._consume_topic_with_retry(
            topic="sales",
            subscription="monitor-sales",
            event_mapper=self.event_mapper.map_sale_event,
            consumer_type=_pulsar.ConsumerType.Shared
        )

    async def consume_publicaciones_registradas(self):
        """Consume eventos de publicaciones registradas"""
        await self._consume_topic_with_retry(
            topic="publicaciones-registradas",
            subscription="monitor-publicaciones",
            event_mapper=self.event_mapper.map_publicacion_event,
            consumer_type=_pulsar.ConsumerType.Shared
        )

    async def _consume_topic_with_retry(
        self, 
        topic: str, 
        subscription: str, 
        event_mapper: Callable[[Dict[str, Any]], Any],
        consumer_type: _pulsar.ConsumerType = _pulsar.ConsumerType.Shared,
        max_retries: int = 5
    ):
        """Método genérico para consumir de un tópico con reintentos automáticos"""
        retry_count = 0
        
        while self.is_running and retry_count < max_retries:
            try:
                await self._consume_topic(topic, subscription, event_mapper, consumer_type)
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error consuming from topic {topic} (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    wait_time = min(60, 2 ** retry_count)
                    logger.info(f"Retrying connection to {topic} in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max retries exceeded for topic {topic}")
                    break

    async def _consume_topic(
        self, 
        topic: str, 
        subscription: str, 
        event_mapper: Callable[[Dict[str, Any]], Any],
        consumer_type: _pulsar.ConsumerType
    ):
        """Método interno para consumir de un tópico específico"""
        client = None
        consumer = None
        
        try:
            # Crear cliente con configuración básica
            client = await aiopulsar.connect(f'{settings.pulsar_url}')
            
            # Crear consumidor con parámetros básicos compatibles
            consumer = await client.subscribe(
                topic,
                consumer_type=consumer_type,
                subscription_name=subscription,
                initial_position=pulsar.InitialPosition.Earliest
            )
            
            logger.info(f"Successfully connected to topic: {topic} with subscription: {subscription}")
            
            while self.is_running:
                try:
                    # Recibir mensaje con timeout
                    message = await asyncio.wait_for(
                        consumer.receive(), 
                        timeout=30.0
                    )
                    
                    # Procesar el mensaje
                    await self._process_message(message, consumer, event_mapper)
                    
                except asyncio.TimeoutError:
                    continue
                    
                except Exception as e:
                    logger.error(f'Error processing message from {topic}: {e}')
                    continue
                    
        except Exception as e:
            logger.error(f'ERROR subscribing to topic {topic}: {e}')
            raise
            
        finally:
            # Limpiar recursos
            if consumer:
                try:
                    await consumer.close()
                except Exception:
                    logger.warning("Error closing consumer")
            
            if client:
                try:
                    await client.close()
                except Exception:
                    logger.warning("Error closing client")

    async def _process_message(self, message, consumer, event_mapper):
        """Procesa un mensaje individual con manejo de errores robusto"""
        try:
            # Extraer datos del mensaje
            raw_data = message.value()
            logger.debug(f'Raw event received: {raw_data}')
            
            # Mapear a evento de dominio
            domain_event = event_mapper(raw_data)
            
            if domain_event is None:
                logger.warning(f"Event mapper returned None for message: {raw_data}")
                await consumer.acknowledge(message)
                return
            
            # Enviar al handler de dominio
            await self._handle_domain_event(domain_event)
            
            # Confirmar procesamiento exitoso
            await consumer.acknowledge(message)
            logger.debug('Event processed successfully')
            
        except Exception as e:
            logger.error(f'Error processing message: {e}')
            traceback.print_exc()
            
            # Decidir si rechazar o reintentar
            if self._is_recoverable_error(e):
                await consumer.negative_acknowledge(message)
            else:
                logger.error(f"Non-recoverable error, acknowledging message: {e}")
                await consumer.acknowledge(message)

    async def _handle_domain_event(self, domain_event):
        """Maneja un evento de dominio"""
        try:
            if asyncio.iscoroutinefunction(self.event_handler):
                await self.event_handler(domain_event)
            else:
                # Para handlers síncronos, ejecutar en thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.event_handler, domain_event)
                
        except Exception as e:
            logger.error(f"Error in domain event handler: {e}")
            raise

    def _is_recoverable_error(self, error: Exception) -> bool:
        """Determina si un error es recuperable y amerita reintento"""
        recoverable_errors = (
            ConnectionError,
            TimeoutError,
            pulsar.ConnectError,
            asyncio.TimeoutError
        )
        
        non_recoverable_errors = (
            ValueError,
            KeyError,
            AttributeError
        )
        
        if isinstance(error, recoverable_errors):
            return True
        elif isinstance(error, non_recoverable_errors):
            return False
        else:
            return True