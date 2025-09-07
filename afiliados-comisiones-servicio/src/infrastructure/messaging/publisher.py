from __future__ import annotations
import asyncio
import json
import aio_pika
from ..config import RABBITMQ_URL

class IntegracionPublisher:
    def __init__(self) -> None:
        self._conn = None
        self._channel = None
        self._exchange_name = "comisiones"
        self._routing_key = "comisiones.creadas"

    async def _ensure(self):
        if not self._conn:
            self._conn = await aio_pika.connect_robust(RABBITMQ_URL)
            self._channel = await self._conn.channel()
            await self._channel.declare_exchange(self._exchange_name, type=aio_pika.ExchangeType.TOPIC, durable=True)

    def publicar_comision_creada(self, ev) -> None:
        # fire-and-forget (no bloquear FastAPI)
        asyncio.create_task(self._publish(ev))

    async def _publish(self, ev) -> None:
        await self._ensure()
        exchange = await self._channel.get_exchange(self._exchange_name)
        body = json.dumps({
            "type": ev.name,
            "commission_id": str(ev.commission_id),
            "affiliate_id": str(ev.affiliate_id),
            "valor": ev.valor,
            "moneda": ev.moneda,
            "occurred_on": ev.occurred_on.isoformat(),
        }).encode("utf-8")
        msg = aio_pika.Message(body, content_type="application/json")
        await exchange.publish(msg, routing_key=self._routing_key)
