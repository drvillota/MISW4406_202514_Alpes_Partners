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
            # En una implementación real, aquí se conectaría a Pulsar:
            # import pulsar
            self._client = pulsar.Client(self.broker_url)
            
            # Por ahora, simular conexión
            self._connected = True
            logger.info("Despachador conectado")

        except Exception as e:
            logger.error(f"Error conectando despachador: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self._connected
    
    def publicar_evento(self, topico: str, evento: Dict[str, Any]):
        """Publicar evento simple en un tópico"""
        try:
            if not self._connected:
                self.connect()
            
            # En una implementación real, enviar a Pulsar
            # producer.send(json.dumps(evento))
            
            # Por ahora, solo logear
            logger.info(f"Evento enviado a '{topico}': {evento.get('event_type', 'Unknown')}")
            logger.debug(f"Datos: {json.dumps(evento, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publicando evento: {e}")
            return False
    
    def close(self):
        """Cerrar conexiones"""
        try:
            if self._client:
                # En implementación real, cerrar cliente Pulsar:
                # self._client.close()
                pass
            
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
