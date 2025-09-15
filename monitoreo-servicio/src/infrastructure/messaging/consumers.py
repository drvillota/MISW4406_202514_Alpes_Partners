import logging
import traceback
import pulsar, _pulsar
import asyncio
from typing import Callable, Any, Awaitable, Type
import aiopulsar
from pulsar.schema import AvroSchema, Record
from ..schemas.event_schema import ConversionEventSchema, ClickEventSchema, SaleEventSchema
from ..config.settings import get_settings
from .event_mapper import PulsarEventMapper

logger = logging.getLogger(__name__)
settings = get_settings()

class EventConsumerService:
    """Servicio para consumir eventos de las colas de Pulsar"""
    
    def __init__(self, event_handler: Callable[[Any], Awaitable[Any]]):
        self.event_handler = event_handler
        self.mapper = PulsarEventMapper()

    async def start_all_consumers(self):
        """Inicia todos los consumidores concurrentemente"""
        try:
            tasks = [
                self.consume_conversions(),
                self.consume_clicks(),
                self.consume_sales()
            ]
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error starting consumers: {e}")
            traceback.print_exc()

    async def consume_conversions(self):
        """Consume eventos de conversiones"""
        await self._consume_topic(
            topic="conversions",
            subscription="monitor-conversions",
            schema=ConversionEventSchema,
            event_mapper=self.mapper.map_conversion_event
        )

    async def consume_clicks(self):
        """Consume eventos de clicks"""
        await self._consume_topic(
            topic="clicks", 
            subscription="monitor-clicks",
            schema=ClickEventSchema,
            event_mapper=self.mapper.map_click_event
        )

    async def consume_sales(self):
        """Consume eventos de ventas"""
        await self._consume_topic(
            topic="sales",
            subscription="monitor-sales", 
            schema=SaleEventSchema,
            event_mapper=self.mapper.map_sale_event
        )

    async def _consume_topic(
        self, 
        topic: str, 
        subscription: str, 
        schema: Type[Record],
        event_mapper: Callable[[Any], Any]
    ):
        """Método genérico para consumir de un tópico específico"""
        try:
            async with aiopulsar.connect(f'{settings.pulsar_url}') as client:
                async with client.subscribe(
                    topic,
                    consumer_type=_pulsar.ConsumerType.Shared,
                    subscription_name=subscription,
                    schema=AvroSchema(schema)
                ) as consumer:
                    logger.info(f"Started consuming from topic: {topic}")
                    
                    while True:
                        try:
                            message = await consumer.receive()
                            
                            # Procesar el mensaje
                            raw_data = message.value()
                            logger.debug(f'Raw event received from {topic}: {raw_data}')
                            
                            # Mapear a entidad de dominio
                            domain_event = event_mapper(raw_data)
                            
                            # Enviar al handler
                            await self.event_handler(domain_event)
                            
                            # Confirmar procesamiento
                            await consumer.acknowledge(message)
                            logger.debug(f'Event processed successfully from {topic}')
                            
                        except Exception as e:
                            logger.error(f'Error processing message from {topic}: {e}')
                            # En caso de error, rechazar el mensaje para reintento
                            await consumer.negative_acknowledge(message)
                            
        except Exception as e:
            logger.error(f'ERROR subscribing to topic {topic}: {e}')
            traceback.print_exc()
            # Reintento después de un delay
            await asyncio.sleep(5)
            # Recursión para reconectar
            await self._consume_topic(topic, subscription, schema, event_mapper)