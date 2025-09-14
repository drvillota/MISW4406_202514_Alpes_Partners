"""Servicio Outbox para garantizar consistencia transaccional

Este servicio implementa el patrón outbox para garantizar que los eventos
se publiquen de manera consistente con las transacciones de base de datos.

"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..db.write.models import OutboxEvent
from .publisher import IntegracionPublisher

logger = logging.getLogger(__name__)

class OutboxService:
    """Servicio para procesar eventos del outbox pattern"""
    
    def __init__(self, session: Session, publisher: IntegracionPublisher):
        self.session = session
        self.publisher = publisher
        self.is_running = False
        self.processing_task = None
        
    async def start_processing(self, poll_interval: int = 5):
        """Inicia el procesamiento continuo de eventos outbox"""
        if self.is_running:
            logger.warning("Outbox processing is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting outbox processing with {poll_interval}s interval")
        
        self.processing_task = asyncio.create_task(
            self._process_outbox_loop(poll_interval)
        )
        
    async def stop_processing(self):
        """Detiene el procesamiento de eventos outbox"""
        logger.info("Stopping outbox processing...")
        self.is_running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Outbox processing stopped")
    
    async def _process_outbox_loop(self, poll_interval: int):
        """Bucle principal de procesamiento del outbox"""
        while self.is_running:
            try:
                # Procesar eventos pendientes
                processed_count = await self.process_pending_events()
                
                if processed_count > 0:
                    logger.info(f"Processed {processed_count} outbox events")
                
                # Limpiar eventos antiguos procesados
                await self.cleanup_processed_events()
                
                # Reintententer eventos fallidos
                await self.retry_failed_events()
                
                # Esperar antes del siguiente ciclo
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error in outbox processing loop: {e}")
                await asyncio.sleep(poll_interval * 2)  # Esperar más tiempo en caso de error
    
    async def process_pending_events(self, batch_size: int = 100) -> int:
        """Procesa eventos pendientes en el outbox"""
        try:
            # Obtener eventos pendientes ordenados por fecha
            pending_events = self.session.query(OutboxEvent).filter(
                OutboxEvent.status == 'pending'
            ).order_by(OutboxEvent.created_at).limit(batch_size).all()
            
            if not pending_events:
                return 0
            
            processed_count = 0
            
            for event in pending_events:
                try:
                    # Procesar el evento individual
                    success = await self._process_single_event(event)
                    
                    if success:
                        event.status = 'processed'
                        event.processed_at = datetime.utcnow()
                        processed_count += 1
                    else:
                        event.status = 'failed'
                        event.retry_count += 1
                    
                    self.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing outbox event {event.id}: {e}")
                    
                    # Marcar como fallido e incrementar contador
                    event.status = 'failed'
                    event.retry_count += 1
                    event.error_message = str(e)[:500]  # Limitar longitud del error
                    
                    try:
                        self.session.commit()
                    except Exception as commit_error:
                        logger.error(f"Error committing failed event status: {commit_error}")
                        self.session.rollback()
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error in process_pending_events: {e}")
            self.session.rollback()
            return 0
    
    async def _process_single_event(self, event: OutboxEvent) -> bool:
        """Procesa un evento individual del outbox"""
        try:
            # Deserializar los datos del evento
            event_data = json.loads(event.event_data)
            
            # Publicar el evento según su tipo
            success = await self._publish_event_by_type(
                event.aggregate_type,
                event.event_type,
                event_data
            )
            
            if success:
                logger.debug(f"Successfully published outbox event {event.id}: {event.event_type}")
                return True
            else:
                logger.warning(f"Failed to publish outbox event {event.id}: {event.event_type}")
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in outbox event {event.id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing outbox event {event.id}: {e}")
            return False
    
    async def _publish_event_by_type(self, aggregate_type: str, event_type: str, event_data: dict) -> bool:
        """Publica un evento según su tipo y agregado"""
        try:
            # Mapear agregados a tópicos de Pulsar
            topic_mapping = {
                'Afiliado': 'affiliate-events',
                'Conversion': 'conversion-events', 
                'Comision': 'commission-events'
            }
            
            topic = topic_mapping.get(aggregate_type)
            if not topic:
                logger.error(f"Unknown aggregate type: {aggregate_type}")
                return False
            
            # Preparar el payload para Pulsar
            pulsar_payload = {
                'event_type': event_type,
                'aggregate_type': aggregate_type,
                'aggregate_id': event_data.get('affiliate_id', event_data.get('commission_id', event_data.get('id'))),
                'timestamp': datetime.utcnow().isoformat(),
                'data': event_data
            }
            
            # Publicar usando el publisher de integración
            if hasattr(self.publisher, 'publish_to_topic'):
                success = await self.publisher.publish_to_topic(topic, pulsar_payload)
            else:
                # Fallback para compatibilidad
                success = await self._publish_generic_event(topic, pulsar_payload)
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}")
            return False
    
    async def _publish_generic_event(self, topic: str, payload: dict) -> bool:
        """Publicación genérica de eventos (fallback)"""
        try:
            # Aquí iría la lógica de publicación a Pulsar
            # Por ahora, simulamos una publicación exitosa
            logger.info(f"Publishing to {topic}: {payload}")
            
            # TODO: Implementar publicación real a Pulsar
            # await self.pulsar_client.send(topic, payload)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in generic event publishing: {e}")
            return False
    
    async def retry_failed_events(self, max_retries: int = 5):
        """Reintenta eventos fallidos que no han superado el límite de reintentos"""
        try:
            # Buscar eventos fallidos que pueden reintentarse
            retry_events = self.session.query(OutboxEvent).filter(
                and_(
                    OutboxEvent.status == 'failed',
                    OutboxEvent.retry_count < max_retries,
                    # Solo reintentar eventos que no sean demasiado antiguos
                    OutboxEvent.created_at > datetime.utcnow() - timedelta(days=1)
                )
            ).order_by(OutboxEvent.created_at).limit(50).all()
            
            for event in retry_events:
                # Calcular delay exponencial basado en retry_count
                delay = min(300, 2 ** event.retry_count)  # Max 5 minutos
                
                if event.created_at + timedelta(seconds=delay) <= datetime.utcnow():
                    # Es hora de reintentar
                    event.status = 'pending'
                    event.error_message = None
            
            if retry_events:
                self.session.commit()
                logger.info(f"Queued {len(retry_events)} events for retry")
                
        except Exception as e:
            logger.error(f"Error in retry_failed_events: {e}")
            self.session.rollback()
    
    async def cleanup_processed_events(self, retention_days: int = 7):
        """Limpia eventos procesados antiguos"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            deleted_count = self.session.query(OutboxEvent).filter(
                and_(
                    OutboxEvent.status == 'processed',
                    OutboxEvent.processed_at < cutoff_date
                )
            ).delete()
            
            if deleted_count > 0:
                self.session.commit()
                logger.info(f"Cleaned up {deleted_count} old processed events")
                
        except Exception as e:
            logger.error(f"Error in cleanup_processed_events: {e}")
            self.session.rollback()
    
    def get_outbox_metrics(self) -> dict:
        """Obtiene métricas del estado del outbox"""
        try:
            # Contar eventos por estado
            from sqlalchemy import func
            
            metrics = self.session.query(
                OutboxEvent.status,
                func.count(OutboxEvent.id).label('count')
            ).group_by(OutboxEvent.status).all()
            
            result = {status: count for status, count in metrics}
            
            # Agregar información adicional
            result.update({
                'oldest_pending': self._get_oldest_pending_event(),
                'processing_running': self.is_running
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting outbox metrics: {e}")
            return {'error': str(e)}
    
    def _get_oldest_pending_event(self) -> Optional[str]:
        """Obtiene la fecha del evento pendiente más antiguo"""
        try:
            oldest = self.session.query(OutboxEvent).filter(
                OutboxEvent.status == 'pending'
            ).order_by(OutboxEvent.created_at).first()
            
            return oldest.created_at.isoformat() if oldest else None
            
        except Exception as e:
            logger.error(f"Error getting oldest pending event: {e}")
            return None

class OutboxEventPublisher:
    """Publicador que usa el patrón outbox para garantizar consistencia"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def publish_domain_events(self, aggregate):
        """Publica los eventos de dominio de un agregado usando outbox pattern"""
        try:
            for event in aggregate.eventos:
                outbox_event = OutboxEvent(
                    aggregate_id=aggregate.id,
                    aggregate_type=aggregate.__class__.__name__,
                    event_type=event.name,
                    event_data=self._serialize_event(event),
                    status='pending'
                )
                
                self.session.add(outbox_event)
            
            # Los eventos se commitean junto con la transacción principal
            # Esto garantiza consistencia transaccional
            
        except Exception as e:
            logger.error(f"Error publishing domain events to outbox: {e}")
            raise
    
    def _serialize_event(self, event) -> str:
        """Serializa un evento de dominio a JSON"""
        try:
            # Convertir el evento a diccionario
            event_dict = {
                'name': event.name,
                'timestamp': event.timestamp.isoformat(),
                **{k: str(v) if hasattr(v, '__str__') else v 
                   for k, v in event.__dict__.items() 
                   if not k.startswith('_')}
            }
            
            return json.dumps(event_dict, default=str)
            
        except Exception as e:
            logger.error(f"Error serializing event {event}: {e}")
            raise