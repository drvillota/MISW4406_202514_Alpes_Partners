from __future__ import annotations
import logging
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from .commands import RecordEventCommand
from .queries import GetMetricsQuery, GetEventsQuery
from ..domains.events.entities import Event, EventType
from ..domains.events.repository import EventRepository, EventQueryRepository

logger = logging.getLogger(__name__)

class EventHandler:
    """Handler que usa repositorios SQL para persistencia"""
    
    def __init__(self, event_repo: EventRepository, query_repo: EventQueryRepository):
        self.event_repo = event_repo
        self.query_repo = query_repo
        
    async def handle_record_event(self, command: RecordEventCommand) -> dict:
        """Procesa comando de registro de evento usando PostgreSQL"""
        try:
            # Crear entidad de dominio con conversiones seguras
            event = Event(
                id=uuid4(),
                event_type=EventType(command.event_type),
                user_id=UUID(command.user_id) if isinstance(command.user_id, str) else command.user_id,
                session_id=command.session_id,
                metadata=command.metadata,
                occurred_at=command.occurred_at
            )
            
            # Persistir en PostgreSQL
            self.event_repo.add(event)
            logger.info(f"Event recorded in DB: {event.id} - {event.event_type.value}")
            
            return {"event_id": str(event.id), "status": "recorded"}
            
        except Exception as e:
            logger.error(f"Error recording event: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def handle_get_metrics(self, query: GetMetricsQuery) -> dict:
        """Procesa query de métricas usando PostgreSQL"""
        # Calcular ventana de tiempo
        end_time = query.end_date or datetime.utcnow()
        
        if query.period == "1h":
            start_time = end_time - timedelta(hours=1)
        elif query.period == "7d":
            start_time = end_time - timedelta(days=7)
        else:  # "24h" por defecto
            start_time = end_time - timedelta(hours=24)
            
        if query.start_date:
            start_time = query.start_date
            
        # Consultar métricas desde PostgreSQL
        clicks = self.query_repo.count_by_type(EventType.CLICK, start_time, end_time)
        conversions = self.query_repo.count_by_type(EventType.CONVERSION, start_time, end_time)
        sales = self.query_repo.count_by_type(EventType.SALE, start_time, end_time)
        
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0.0
        
        return {
            "total_clicks": clicks,
            "total_conversions": conversions, 
            "total_sales": sales,
            "conversion_rate": round(conversion_rate, 2)
        }
    
    async def handle_get_events(self, query: GetEventsQuery) -> dict:
        """Procesa query de eventos usando PostgreSQL"""
        if query.event_type and query.start_date and query.end_date:
            # Consulta específica por tipo y período
            events = self.query_repo.get_by_type_and_period(
                EventType(query.event_type), 
                query.start_date, 
                query.end_date
            )
        elif query.start_date and query.end_date:
            # Consulta por período
            events = self.query_repo.get_by_period(query.start_date, query.end_date)
        else:
            # Consulta general (últimas 24h por defecto)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            events = self.query_repo.get_by_period(start_time, end_time)
        
        # Aplicar límite
        events = events[:query.limit]
        
        # Convertir entidades a dict para JSON
        events_dict = [
            {
                'id': str(e.id),
                'type': e.event_type.value,
                'user_id': str(e.user_id),
                'session_id': e.session_id,
                'metadata': e.metadata,
                'occurred_at': e.occurred_at
            }
            for e in events
        ]
        
        return {
            "events": events_dict,
            "total_count": len(events_dict)
        }
