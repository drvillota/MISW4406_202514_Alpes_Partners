from datetime import datetime
from uuid import UUID, uuid4
from typing import Any, Dict
from ...domains.events.entities import Event, EventType

class PulsarEventMapper:
    """Mapper que crea entidades de dominio reales"""

    def map_conversion_event(self, pulsar_data: Dict[str, Any]) -> Event:
        return Event(
            id=uuid4(),
            event_type=EventType.CONVERSION,
            user_id=UUID(pulsar_data.get('user_id', str(uuid4()))),
            session_id=pulsar_data.get('session_id', ''),
            metadata={'amount': pulsar_data.get('amount', 0)},
            occurred_at=self._parse_timestamp(pulsar_data.get('timestamp'))
        )

    def map_click_event(self, pulsar_data: Dict[str, Any]) -> Event:
        return Event(
            id=uuid4(),
            event_type=EventType.CLICK,
            user_id=UUID(pulsar_data.get('user_id', str(uuid4()))),
            session_id=pulsar_data.get('session_id', ''),
            metadata={'url': pulsar_data.get('url', '')},
            occurred_at=self._parse_timestamp(pulsar_data.get('timestamp'))
        )

    def map_sale_event(self, pulsar_data: Dict[str, Any]) -> Event:
        return Event(
            id=uuid4(),
            event_type=EventType.SALE,
            user_id=UUID(pulsar_data.get('user_id', str(uuid4()))),
            session_id=pulsar_data.get('session_id', ''),
            metadata={
                'order_id': pulsar_data.get('order_id', ''),
                'amount': pulsar_data.get('amount', 0)
            },
            occurred_at=self._parse_timestamp(pulsar_data.get('timestamp'))
        )

    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp simplificado"""
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp / 1000 if timestamp > 10**10 else timestamp)
        return datetime.now()