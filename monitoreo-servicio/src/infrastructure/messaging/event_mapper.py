from datetime import datetime
from uuid import UUID, uuid4
from typing import Any, Dict, Union
import logging
from ...domains.events.entities import Event, EventType

logger = logging.getLogger(__name__)

class PulsarEventMapper:
    """Mapper que crea entidades de dominio reales"""

    def map_conversion_event(self, pulsar_data: Union[Dict[str, Any], Any]) -> Event:
        """Mapear evento de conversión desde Pulsar schema o dict"""
        try:
            logger.debug(f"Mapping conversion event: {type(pulsar_data)} - {pulsar_data}")
            
            # Extraer datos dependiendo del tipo de objeto
            if hasattr(pulsar_data, '__dict__'):
                # Es un objeto schema de Pulsar
                affiliate_id = getattr(pulsar_data, 'affiliate_id', str(uuid4()))
                conversion_type = getattr(pulsar_data, 'conversion_type', 'unknown')
                amount = getattr(pulsar_data, 'amount', 0)
                currency = getattr(pulsar_data, 'currency', 'USD')
                occurred_at = getattr(pulsar_data, 'occurred_at', None)
                timestamp = getattr(pulsar_data, 'timestamp', None)
                event_type = getattr(pulsar_data, 'event_type', 'ConversionRequested')
                source_service = getattr(pulsar_data, 'source_service', 'affiliates-commissions')
            else:
                # Es un diccionario
                affiliate_id = pulsar_data.get('affiliate_id', str(uuid4()))
                conversion_type = pulsar_data.get('conversion_type', 'unknown')
                amount = pulsar_data.get('amount', 0)
                currency = pulsar_data.get('currency', 'USD')
                occurred_at = pulsar_data.get('occurred_at', None)
                timestamp = pulsar_data.get('timestamp', None)
                event_type = pulsar_data.get('event_type', 'ConversionRequested')
                source_service = pulsar_data.get('source_service', 'affiliates-commissions')
                
            return Event(
                id=uuid4(),
                event_type=EventType.CONVERSION,
                user_id=self._parse_uuid(affiliate_id),  # Usar affiliate_id como user_id
                session_id=f"conversion_{affiliate_id}_{int(datetime.now().timestamp())}",
                metadata={
                    'affiliate_id': str(affiliate_id),
                    'conversion_type': str(conversion_type),
                    'amount': float(amount) if amount else 0.0,
                    'currency': str(currency),
                    'event_type': str(event_type),
                    'source_service': str(source_service),
                    'occurred_at': str(occurred_at) if occurred_at else None
                },
                occurred_at=self._parse_timestamp(occurred_at or timestamp)
            )
        except Exception as e:
            logger.error(f"Error mapping conversion event: {e}")
            # Crear un evento por defecto en caso de error
            return self._create_default_event(EventType.CONVERSION, pulsar_data)

    def map_click_event(self, pulsar_data: Union[Dict[str, Any], Any]) -> Event:
        """Mapear evento de click desde Pulsar schema o dict"""
        try:
            logger.debug(f"Mapping click event: {type(pulsar_data)} - {pulsar_data}")
            
            # Extraer datos dependiendo del tipo de objeto
            if hasattr(pulsar_data, '__dict__'):
                # Es un objeto schema de Pulsar
                user_id = getattr(pulsar_data, 'user_id', str(uuid4()))
                session_id = getattr(pulsar_data, 'session_id', '')
                url = getattr(pulsar_data, 'url', '')
                timestamp = getattr(pulsar_data, 'timestamp', None)
            else:
                # Es un diccionario
                user_id = pulsar_data.get('user_id', str(uuid4()))
                session_id = pulsar_data.get('session_id', '')
                url = pulsar_data.get('url', '')
                timestamp = pulsar_data.get('timestamp', None)
                
            return Event(
                id=uuid4(),
                event_type=EventType.CLICK,
                user_id=self._parse_uuid(user_id),
                session_id=str(session_id),
                metadata={'url': str(url)},
                occurred_at=self._parse_timestamp(timestamp)
            )
        except Exception as e:
            logger.error(f"Error mapping click event: {e}")
            return self._create_default_event(EventType.CLICK, pulsar_data)

    def map_sale_event(self, pulsar_data: Union[Dict[str, Any], Any]) -> Event:
        """Mapear evento de venta desde Pulsar schema o dict"""
        try:
            logger.debug(f"Mapping sale event: {type(pulsar_data)} - {pulsar_data}")
            
            # Extraer datos dependiendo del tipo de objeto
            if hasattr(pulsar_data, '__dict__'):
                # Es un objeto schema de Pulsar
                user_id = getattr(pulsar_data, 'user_id', str(uuid4()))
                session_id = getattr(pulsar_data, 'session_id', '')
                order_id = getattr(pulsar_data, 'order_id', '')
                amount = getattr(pulsar_data, 'amount', 0)
                timestamp = getattr(pulsar_data, 'timestamp', None)
            else:
                # Es un diccionario
                user_id = pulsar_data.get('user_id', str(uuid4()))
                session_id = pulsar_data.get('session_id', '')
                order_id = pulsar_data.get('order_id', '')
                amount = pulsar_data.get('amount', 0)
                timestamp = pulsar_data.get('timestamp', None)
                
            return Event(
                id=uuid4(),
                event_type=EventType.SALE,
                user_id=self._parse_uuid(user_id),
                session_id=str(session_id),
                metadata={
                    'order_id': str(order_id),
                    'amount': float(amount) if amount else 0.0
                },
                occurred_at=self._parse_timestamp(timestamp)
            )
        except Exception as e:
            logger.error(f"Error mapping sale event: {e}")
            return self._create_default_event(EventType.SALE, pulsar_data)

    def map_publicacion_event(self, pulsar_data: Union[Dict[str, Any], Any]) -> Event:
        """Mapear evento de publicación registrada desde Pulsar"""
        try:
            logger.debug(f"Mapping publicacion event: {type(pulsar_data)} - {pulsar_data}")
            
            # Extraer datos dependiendo del tipo de objeto
            if hasattr(pulsar_data, '__dict__'):
                # Es un objeto schema de Pulsar
                colaboracion_id = getattr(pulsar_data, 'colaboracion_id', str(uuid4()))
                campania_id = getattr(pulsar_data, 'campania_id', str(uuid4()))
                influencer_id = getattr(pulsar_data, 'influencer_id', str(uuid4()))
                url = getattr(pulsar_data, 'url', '')
                red = getattr(pulsar_data, 'red', '')
                fecha = getattr(pulsar_data, 'fecha', None)
                timestamp = getattr(pulsar_data, 'timestamp', None)
            else:
                # Es un diccionario
                colaboracion_id = pulsar_data.get('colaboracion_id', str(uuid4()))
                campania_id = pulsar_data.get('campania_id', str(uuid4()))
                influencer_id = pulsar_data.get('influencer_id', str(uuid4()))
                url = pulsar_data.get('url', '')
                red = pulsar_data.get('red', '')
                fecha = pulsar_data.get('fecha', None)
                timestamp = pulsar_data.get('timestamp', None)
                
            return Event(
                id=uuid4(),
                event_type=EventType.PUBLICACION,  # Usar PUBLICACION específico para publicaciones
                user_id=self._parse_uuid(influencer_id),  # Usar influencer_id como user_id
                session_id=str(colaboracion_id),  # Usar colaboracion_id como session_id
                metadata={
                    'colaboracion_id': str(colaboracion_id),
                    'campania_id': str(campania_id),
                    'influencer_id': str(influencer_id),
                    'url': str(url),
                    'red': str(red),
                    'fecha': str(fecha) if fecha else None,
                    'event_type': 'PublicacionRegistrada',
                    'source_service': 'colaboraciones'
                },
                occurred_at=self._parse_timestamp(timestamp)
            )
        except Exception as e:
            logger.error(f"Error mapping publicacion event: {e}")
            return self._create_default_event(EventType.PUBLICACION, pulsar_data)

    def _parse_uuid(self, user_id: Any) -> UUID:
        """Parse UUID de manera segura"""
        try:
            if isinstance(user_id, str):
                return UUID(user_id)
            elif isinstance(user_id, UUID):
                return user_id
            else:
                return uuid4()
        except (ValueError, TypeError):
            logger.warning(f"Invalid UUID: {user_id}, generating new one")
            return uuid4()

    def _create_default_event(self, event_type: EventType, original_data: Any) -> Event:
        """Crear un evento por defecto cuando falla el mapeo"""
        return Event(
            id=uuid4(),
            event_type=event_type,
            user_id=uuid4(),
            session_id=f"error_session_{int(datetime.now().timestamp())}",
            metadata={'error': 'Failed to parse original data', 'raw_data': str(original_data)},
            occurred_at=datetime.now()
        )

    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp simplificado"""
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp / 1000 if timestamp > 10**10 else timestamp)
        return datetime.now()