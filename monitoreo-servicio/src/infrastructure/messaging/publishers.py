import logging
import json
import pulsar
from typing import Dict, Any
from ..config.settings import get_settings
from ..schemas.event_schema import ClickEventSchema, ConversionEventSchema, SaleEventSchema
from pulsar.schema import AvroSchema

logger = logging.getLogger(__name__)
settings = get_settings()

class EventPublisher:
    """Publisher para publicar eventos de prueba en Pulsar"""
    
    def __init__(self):
        self.client = None
        self.producers = {}
        
    def connect(self):
        """Conectar al broker de Pulsar"""
        try:
            self.client = pulsar.Client(settings.pulsar_url)
            logger.info(f"Connected to Pulsar: {settings.pulsar_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Pulsar: {e}")
            raise
            
    def close(self):
        """Cerrar conexión y productores"""
        try:
            for producer in self.producers.values():
                producer.close()
            if self.client:
                self.client.close()
            logger.info("Pulsar connection closed")
        except Exception as e:
            logger.error(f"Error closing Pulsar connection: {e}")
    
    def _get_producer(self, topic: str, schema_class=None):
        """Obtener o crear un producer para un topic específico"""
        if topic not in self.producers:
            try:
                if not self.client:
                    self.connect()
                    
                if schema_class:
                    # Producer con schema Avro - ignorar type hints para compatibilidad
                    self.producers[topic] = self.client.create_producer(  # type: ignore
                        topic,
                        schema=AvroSchema(schema_class)  # type: ignore
                    )
                else:
                    # Producer básico para JSON
                    self.producers[topic] = self.client.create_producer(topic)  # type: ignore
                    
                logger.info(f"Created producer for topic: {topic}")
            except Exception as e:
                logger.error(f"Failed to create producer for topic {topic}: {e}")
                raise
                
        return self.producers[topic]
    
    def publish_click_event(self, click_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publicar evento de click con schema Avro"""
        try:
            if not self.client:
                self.connect()
                
            # Crear el record con schema
            click_record = ClickEventSchema(
                user_id=click_data.get('user_id', ''),
                session_id=click_data.get('session_id', ''),
                url=click_data.get('url', ''),
                timestamp=click_data.get('timestamp', 0)
            )
            
            producer = self._get_producer('clicks', ClickEventSchema)
            message_id = producer.send(click_record)
            
            result = {
                "status": "published",
                "topic": "clicks",
                "message_id": str(message_id),
                "data": click_data
            }
            
            logger.info(f"Click event published: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error publishing click event: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "data": click_data
            }
    
    def publish_conversion_event(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publicar evento de conversión con schema Avro"""
        try:
            if not self.client:
                self.connect()
                
            conversion_record = ConversionEventSchema(
                user_id=conversion_data.get('user_id', ''),
                session_id=conversion_data.get('session_id', ''),
                amount=conversion_data.get('amount', 0.0),
                timestamp=conversion_data.get('timestamp', 0)
            )
            
            producer = self._get_producer('conversions', ConversionEventSchema)
            message_id = producer.send(conversion_record)
            
            result = {
                "status": "published",
                "topic": "conversions", 
                "message_id": str(message_id),
                "data": conversion_data
            }
            
            logger.info(f"Conversion event published: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error publishing conversion event: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data": conversion_data
            }
    
    def publish_sale_event(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publicar evento de venta con schema Avro"""
        try:
            if not self.client:
                self.connect()
                
            sale_record = SaleEventSchema(
                user_id=sale_data.get('user_id', ''),
                session_id=sale_data.get('session_id', ''),
                order_id=sale_data.get('order_id', ''),
                amount=sale_data.get('amount', 0.0),
                timestamp=sale_data.get('timestamp', 0)
            )
            
            producer = self._get_producer('sales', SaleEventSchema)
            message_id = producer.send(sale_record)
            
            result = {
                "status": "published",
                "topic": "sales",
                "message_id": str(message_id), 
                "data": sale_data
            }
            
            logger.info(f"Sale event published: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error publishing sale event: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data": sale_data
            }

# Instancia global para reutilizar
_publisher_instance = None

def get_event_publisher() -> EventPublisher:
    """Factory para obtener una instancia del publisher"""
    global _publisher_instance
    if _publisher_instance is None:
        _publisher_instance = EventPublisher()
    return _publisher_instance