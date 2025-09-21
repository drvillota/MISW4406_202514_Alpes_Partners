"""Consumidor de eventos para el microservicio de Colaboraciones"""

import logging
import traceback
import asyncio
import pulsar
import _pulsar
import aiopulsar
from pulsar.schema import AvroSchema, Record
from typing import Callable, Any, Dict
from ..schemas.schemas import (
    ColaboracionIniciadaSchema,
    PublicacionRegistradaSchema,
)
from ..schemas.utils import broker_host  # asumiendo que ya lo tienes

logger = logging.getLogger(__name__)


class ColaboracionEventConsumer:
    """Servicio para consumir eventos de Pulsar relacionados con colaboraciones"""

    def __init__(self, event_handler: Callable[[Any], None]):
        self.event_handler = event_handler
        self.is_running = False
        self.consumer_tasks = []

    async def start_all_consumers(self):
        """Inicia consumidores necesarios para este micro"""
        self.is_running = True
        try:
            self.consumer_tasks = [
                asyncio.create_task(self.consume_publicacion_registrada()),
                # Si más adelante necesitas escuchar a "colaboracion-iniciada"
                # puedes agregar otro consumer aquí.
            ]

            logger.info("ColaboracionEventConsumer: iniciando consumers…")
            await asyncio.gather(*self.consumer_tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error starting consumers: {e}")
            traceback.print_exc()
            await self.stop_all_consumers()

    async def stop_all_consumers(self):
        """Detiene todos los consumidores"""
        logger.info("ColaboracionEventConsumer: deteniendo consumers…")
        self.is_running = False
        for task in self.consumer_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info("Consumer task cancelled during shutdown")

    async def consume_publicacion_registrada(self):
        """Consume eventos PublicacionRegistrada (ej. para monitoreo)"""
        await self._consume_topic_with_retry(
            topic="publicaciones-registradas",
            subscription="colaboraciones-publicaciones",
            schema=PublicacionRegistradaSchema,
        )

    async def _consume_topic_with_retry(
        self,
        topic: str,
        subscription: str,
        schema: Record,
        consumer_type: _pulsar.ConsumerType = _pulsar.ConsumerType.Shared,
        max_retries: int = 5,
    ):
        """Consumidor con reintentos automáticos"""
        retry_count = 0
        while self.is_running and retry_count < max_retries:
            try:
                await self._consume_topic(topic, subscription, schema, consumer_type)
                break
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error consuming {topic} (attempt {retry_count}/{max_retries}): {e}"
                )
                if retry_count < max_retries:
                    wait_time = min(30, 2**retry_count)
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max retries exceeded for {topic}")
                    break

    async def _consume_topic(
        self,
        topic: str,
        subscription: str,
        schema: Record,
        consumer_type: _pulsar.ConsumerType,
    ):
        """Suscripción real a un tópico"""
        client = None
        consumer = None
        try:
            client = await aiopulsar.connect(f"pulsar://{broker_host()}:6650")
            consumer = await client.subscribe(
                topic,
                schema=AvroSchema(schema),
                subscription_name=subscription,
                consumer_type=consumer_type,
                initial_position=pulsar.InitialPosition.Earliest,
            )

            logger.info(f"Conectado a {topic} con subscription {subscription}")

            while self.is_running:
                try:
                    message = await asyncio.wait_for(consumer.receive(), timeout=20.0)
                    event = message.value()
                    await self._handle_event(event)
                    await consumer.acknowledge(message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error procesando mensaje de {topic}: {e}")
                    traceback.print_exc()

        finally:
            if consumer:
                await consumer.close()
            if client:
                await client.close()

    async def _handle_event(self, event: Any):
        """Envía el evento al handler de dominio"""
        try:
            if asyncio.iscoroutinefunction(self.event_handler):
                await self.event_handler(event)
            else:
                self.event_handler(event)
        except Exception as e:
            logger.error(f"Error en event_handler: {e}")
