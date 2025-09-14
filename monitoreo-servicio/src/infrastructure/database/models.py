from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
import enum
from .connection import Base

class EventTypeEnum(enum.Enum):
    CONVERSION = "conversion"
    CLICK = "click"
    SALE = "sale"

class EventModel(Base):
    """Modelo unificado para todos los tipos de eventos de monitoreo"""
    __tablename__ = "events"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[EventTypeEnum] = mapped_column(Enum(EventTypeEnum), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<EventModel(id={self.id}, type={self.event_type.value}, user_id={self.user_id})>"