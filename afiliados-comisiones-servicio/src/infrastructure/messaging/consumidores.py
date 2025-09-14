"""Consumidores de eventos mejorados basados en monitoreo-servicio

En este archivo se definen los consumidores optimizados con mejor manejo de errores,
reconexión automática y mapeo de eventos.

"""

import logging
import traceback
import pulsar
import _pulsar
import asyncio
from typing import Callable, Any, Dict
import aiopulsar
from pulsar.schema import AvroSchema, Record
from ..schema.utils import broker_host
from .event_mapper import EventMapper

logger = logging.getLogger(__name__)

class EventConsumerService:
    """Servicio mejorado para consumir eventos de las colas de Pulsar"""
    
    def __init__(self, event_handler: Callable[[Any], None]):
        self.event_handler = event_handler
        self.event_mapper = EventMapper()
        self.is_running = False
        self.consumer_tasks = []

    async def start_all_consumers(self):
        """Inicia todos los consumidores concurrentemente"""
        try:
            self.is_running = True
            self.consumer_tasks = [
                asyncio.create_task(self.consume_affiliate_events()),
                asyncio.create_task(self.consume_conversion_events()),
                asyncio.create_task(self.consume_commission_events())
            ]
            
            logger.info("Starting all event consumers...")
            await asyncio.gather(*self.consumer_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error starting consumers: {e}")
            traceback.print_exc()
            await self.stop_all_consumers()

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
                    pass

    async def consume_affiliate_events(self):
        """Consume eventos relacionados con afiliados"""
        await self._consume_topic_with_retry(
            topic="affiliate-events",
            subscription="afiliados-comisiones-affiliates",
            event_mapper=self.event_mapper.map_affiliate_event,
            consumer_type=_pulsar.ConsumerType.Shared
        )

    async def consume_conversion_events(self):
        """Consume eventos de conversiones"""
        await self._consume_topic_with_retry(
            topic="conversion-events", 
            subscription="afiliados-comisiones-conversions",
            event_mapper=self.event_mapper.map_conversion_event,
            consumer_type=_pulsar.ConsumerType.Shared
        )

    async def consume_commission_events(self):
        """Consume eventos de comisiones (para otros servicios)"""
        await self._consume_topic_with_retry(
            topic="commission-events",
            subscription="afiliados-comisiones-commissions",
            event_mapper=self.event_mapper.map_commission_event,
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
                # Si llegamos aquí, la conexión se cerró normalmente
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error consuming from topic {topic} (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    # Espera exponencial antes del reintento
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
            # Crear cliente con configuración optimizada
            client = await aiopulsar.connect(
                f'pulsar://{broker_host()}:6650',
                connection_timeout_ms=5000,
                operation_timeout_ms=30000
            )
            
            # Crear consumidor con configuración robusta
            consumer = await client.subscribe(
                topic,
                consumer_type=consumer_type,
                subscription_name=subscription,
                # schema=AvroSchema(schema),  # Se puede agregar schema aquí
                initial_position=pulsar.InitialPosition.Earliest,
                consumer_name=f"{subscription}-{asyncio.current_task().get_name()}",
                receive_queue_size=1000
            )
            
            logger.info(f"Successfully connected to topic: {topic} with subscription: {subscription}")
            
            while self.is_running:
                try:
                    # Recibir mensaje con timeout
                    message = await asyncio.wait_for(
                        consumer.receive(), 
                        timeout=30.0  # 30 segundos de timeout
                    )
                    
                    # Procesar el mensaje
                    await self._process_message(message, consumer, event_mapper)
                    
                except asyncio.TimeoutError:
                    # Timeout normal, continuar
                    continue
                    
                except Exception as e:
                    logger.error(f'Error processing message from {topic}: {e}')
                    # En caso de error de procesamiento, continuar con el siguiente mensaje
                    continue
                    
        except Exception as e:
            logger.error(f'ERROR subscribing to topic {topic}: {e}')
            raise
            
        finally:
            # Limpiar recursos
            if consumer:
                try:
                    await consumer.close()
                except:
                    pass
            
            if client:
                try:
                    await client.close()
                except:
                    pass

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
            logger.debug(f'Event processed successfully')
            
        except Exception as e:
            logger.error(f'Error processing message: {e}')
            traceback.print_exc()
            
            # Decidir si rechazar o reintentarh
            if self._is_recoverable_error(e):
                # Rechazar para reintento
                await consumer.negative_acknowledge(message)
            else:
                # Error no recuperable, confirmar para no reintentarlo
                logger.error(f"Non-recoverable error, acknowledging message: {e}")
                await consumer.acknowledge(message)

    async def _handle_domain_event(self, domain_event):
        """Maneja un evento de dominio"""
        try:
            if asyncio.iscoroutinefunction(self.event_handler):
                await self.event_handler(domain_event)
            else:
                self.event_handler(domain_event)
                
        except Exception as e:
            logger.error(f"Error in domain event handler: {e}")
            raise

    def _is_recoverable_error(self, error: Exception) -> bool:
        """Determina si un error es recuperable y amerita reintento"""
        # Errores de conectividad o temporales
        recoverable_errors = (
            ConnectionError,
            TimeoutError,
            pulsar.ConnectError,
            pulsar.TimeoutError
        )
        
        # Errores de validación o lógica de negocio no son recuperables
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
            # Por defecto, considerar recuperable para evitar pérdida de mensajes
            return True


# Función de conveniencia para suscribirse a un tópico (mantener compatibilidad)
async def suscribirse_a_topico(
    topico: str, 
    suscripcion: str, 
    schema: Record, 
    tipo_consumidor: _pulsar.ConsumerType = _pulsar.ConsumerType.Shared
):
    """Función legacy para mantener compatibilidad"""
    logger.warning("Using legacy suscribirse_a_topico function. Consider migrating to EventConsumerService")
    
    try:
        async with aiopulsar.connect(f'pulsar://{broker_host()}:6650') as cliente:
            async with cliente.subscribe(
                topico, 
                consumer_type=tipo_consumidor,
                subscription_name=suscripcion, 
                schema=AvroSchema(schema)
            ) as consumidor:
                while True:
                    mensaje = await consumidor.receive()
                    print(mensaje)
                    datos = mensaje.value()
                    print(f'Evento recibido: {datos}')
                    await consumidor.acknowledge(mensaje)    

    except Exception as e:
        logging.error(f'ERROR: Suscribiendose al tópico! {topico}, {suscripcion}, {schema}: {e}')
        traceback.print_exc()