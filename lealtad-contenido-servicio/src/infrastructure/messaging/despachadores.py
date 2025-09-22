import logging
import pulsar
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class Despachador:
    """Despachador de eventos simplificado"""
    
    def __init__(self, broker_url: Optional[str] = None):
        self.broker_url = broker_url or 'pulsar://broker:6650'
        self._client = None
        self._connected = False
    
    def connect(self):
        """Conectar a Pulsar"""
        try:
            if not self._connected:
                self._client = pulsar.Client(self.broker_url)
                self._connected = True
                logger.info(f"Despachador conectado a {self.broker_url}")
                
                # Crear topics básicos al conectar
                self._ensure_topics_exist()

        except Exception as e:
            logger.error(f"Error conectando despachador: {e}")
            self._connected = False
            raise
    
    def _ensure_topics_exist(self):
        """Asegurar que los topics principales existan"""
        if not self._client:
            logger.warning("No hay cliente Pulsar disponible para crear topics")
            return
            
        essential_topics = [
            "persistent://public/default/comisiones.creadas",
            "persistent://public/default/commission-events"
        ]
        
        for topic in essential_topics:
            try:
                # Crear un productor temporal para asegurar que el topic existe
                producer = self._client.create_producer(topic)
                producer.close()
                logger.info(f"Topic verificado: {topic}")
            except Exception as e:
                logger.warning(f"No se pudo verificar topic {topic}: {e}")
    
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self._connected
    
    def publicar_evento(self, topico: str, evento: Dict[str, Any]):
        """Publicar evento simple en un tópico"""
        try:
            if not self._connected:
                self.connect()
            
            if not self._client:
                logger.error("Cliente Pulsar no disponible")
                return False
            
            # Crear el topic completo si no viene con el esquema
            if not topico.startswith("persistent://"):
                topico = f"persistent://public/default/{topico}"
            
            # Crear productor y enviar mensaje
            producer = self._client.create_producer(topico)
            mensaje_json = json.dumps(evento)
            
            producer.send(mensaje_json.encode('utf-8'))
            producer.close()
            
            logger.info(f"Evento enviado a '{topico}': {evento.get('event_type', 'Unknown')}")
            logger.debug(f"Datos: {json.dumps(evento, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error publicando evento: {e}")
            return False
    
    def close(self):
        """Cerrar conexiones"""
        try:
            if self._client:
                self._client.close()
            
            self._connected = False
            logger.info("Despachador cerrado")
            
        except Exception as e:
            logger.error(f"Error cerrando despachador: {e}")


class IntegracionPublisher:
    """
    Adaptador simple para mantener compatibilidad
    """
    
    def __init__(self):
        self.despachador = Despachador()
        self.despachador.connect()
    
    def publicar_comision_creada(self, evento_comision):
        """Publicar evento de comisión creada"""
        try:
            # Crear evento simplificado
            evento = {
                'event_type': 'CommissionCalculated',
                'commission_id': str(getattr(evento_comision, 'id', '')),
                'affiliate_id': str(getattr(evento_comision, 'affiliate_id', '')),
                'amount': float(getattr(evento_comision, 'valor', 0)),
                'currency': getattr(evento_comision, 'moneda', 'USD'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source_service': 'affiliates-commissions'
            }
            
            return self.despachador.publicar_evento('commission-events', evento)
            
        except Exception as e:
            logger.error(f"Error publicando comisión: {e}")
            return False
    
    def _publish(self, evento):
        """Método síncrono para compatibilidad"""
        return self.publicar_comision_creada(evento)
    
    def close(self):
        """Cerrar despachador"""
        self.despachador.close()
