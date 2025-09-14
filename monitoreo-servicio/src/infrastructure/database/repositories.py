from __future__ import annotations
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from ...domains.events.entities import Event, EventType
from ...domains.events.repository import EventRepository, EventQueryRepository
from .models import EventModel, EventTypeEnum
from .connection import get_db

class EventRepositorySQL(EventRepository):
    """Implementación SQL del repositorio de eventos"""
    
    def __init__(self, session: Session):
        self.session = session

    def add(self, entity: Event) -> None:
        event_model = EventModel(
            id=entity.id,
            event_type=EventTypeEnum(entity.event_type.value),
            user_id=entity.user_id,
            session_id=entity.session_id,
            event_data=entity.metadata,  # Cambié metadata por event_data
            occurred_at=entity.occurred_at
        )
        self.session.add(event_model)

    def get(self, entity_id: UUID) -> Optional[Event]:
        model = self.session.get(EventModel, entity_id)
        if not model:
            return None
        
        return Event(
            id=model.id,
            event_type=EventType(model.event_type.value),
            user_id=model.user_id,
            session_id=model.session_id,
            metadata=model.event_data,  # Cambié model.metadata por model.event_data
            occurred_at=model.occurred_at
        )

    def exists(self, entity_id: UUID) -> bool:
        return self.session.query(
            self.session.query(EventModel).filter_by(id=entity_id).exists()
        ).scalar()

    def delete_older_than(self, cutoff_date: datetime) -> int:
        result = self.session.query(EventModel).filter(
            EventModel.occurred_at < cutoff_date
        ).delete(synchronize_session=False)
        return result


class EventQueryRepositorySQL(EventQueryRepository):
    """Implementación SQL especializada para consultas analíticas"""
    
    def __init__(self, session: Session):
        self.session = session

    def get_by_period(self, start: datetime, end: datetime) -> List[Event]:
        query = select(EventModel).where(
            and_(
                EventModel.occurred_at >= start,
                EventModel.occurred_at <= end
            )
        ).order_by(EventModel.occurred_at.asc())
        
        models = self.session.execute(query).scalars().all()
        return self._models_to_entities(models)

    def get_by_type_and_period(self, event_type: EventType, start: datetime, end: datetime) -> List[Event]:
        query = select(EventModel).where(
            and_(
                EventModel.event_type == EventTypeEnum(event_type.value),
                EventModel.occurred_at >= start,
                EventModel.occurred_at <= end
            )
        ).order_by(EventModel.occurred_at.asc())
        
        models = self.session.execute(query).scalars().all()
        return self._models_to_entities(models)

    def count_by_type(self, event_type: EventType, start: datetime, end: datetime) -> int:
        query = select(func.count(EventModel.id)).where(
            and_(
                EventModel.event_type == EventTypeEnum(event_type.value),
                EventModel.occurred_at >= start,
                EventModel.occurred_at <= end
            )
        )
        return self.session.execute(query).scalar() or 0

    def get_user_journey(self, user_id: UUID, start: datetime, end: datetime) -> List[Event]:
        query = select(EventModel).where(
            and_(
                EventModel.user_id == user_id,
                EventModel.occurred_at >= start,
                EventModel.occurred_at <= end
            )
        ).order_by(EventModel.occurred_at.asc())
        
        models = self.session.execute(query).scalars().all()
        return self._models_to_entities(models)

    def get_conversion_rate(self, start: datetime, end: datetime) -> float:
        """Calcula la tasa de conversión (conversiones/clicks) para el período"""
        click_count = self.count_by_type(EventType.CLICK, start, end)
        conversion_count = self.count_by_type(EventType.CONVERSION, start, end)
        
        if click_count == 0:
            return 0.0
        
        return (conversion_count / click_count) * 100

    def _models_to_entities(self, models: List[EventModel]) -> List[Event]:
        """Convierte modelos de base de datos a entidades de dominio"""
        return [
            Event(
                id=model.id,
                event_type=EventType(model.event_type.value),
                user_id=model.user_id,
                session_id=model.session_id,
                metadata=model.metadata,
                occurred_at=model.occurred_at
            )
            for model in models
        ]