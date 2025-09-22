from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class EventType(Enum):
    CONVERSION = "conversion"
    CLICK = "click"
    SALE = "sale"
    PUBLICACION = "publicacion"

@dataclass
class Event:
    id: UUID
    event_type: EventType
    user_id: UUID
    session_id: str
    metadata: dict
    occurred_at: datetime
    
    def is_conversion(self) -> bool:
        return self.event_type == EventType.CONVERSION
    
    def is_click(self) -> bool:
        return self.event_type == EventType.CLICK
        
    def is_sale(self) -> bool:
        return self.event_type == EventType.SALE
    
    def is_publicacion(self) -> bool:
        return self.event_type == EventType.PUBLICACION

# Factory functions siguiendo
def nuevo_evento_conversion(user_id: UUID, session_id: str, metadata: dict, occurred_at: datetime) -> Event:
    return Event(
        id=uuid4(), 
        event_type=EventType.CONVERSION,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
        occurred_at=occurred_at
    )

def nuevo_evento_click(user_id: UUID, session_id: str, metadata: dict, occurred_at: datetime) -> Event:
    return Event(
        id=uuid4(),
        event_type=EventType.CLICK,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
        occurred_at=occurred_at
    )

def nuevo_evento_venta(user_id: UUID, session_id: str, metadata: dict, occurred_at: datetime) -> Event:
    return Event(
        id=uuid4(),
        event_type=EventType.SALE,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
        occurred_at=occurred_at
    )

def nuevo_evento_publicacion(user_id: UUID, session_id: str, metadata: dict, occurred_at: datetime) -> Event:
    return Event(
        id=uuid4(),
        event_type=EventType.PUBLICACION,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
        occurred_at=occurred_at
    )