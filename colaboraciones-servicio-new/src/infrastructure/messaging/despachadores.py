"""Despachador de eventos para el microservicio de Colaboraciones"""

import logging
import pulsar
import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class Despachador:
    """Despachador genérico para publicar eventos en Pulsar"""

    def __init__(self, broker_url: Optional[str] = None):
        self.broker_url = broker_url or "pulsar://broker:6650"
        self._client = None
        self._connected = False

    def connect(self):
        """Conectar a Pulsar"""
        try:
            if not self._connected:
                self._client = pulsar.Client(self.broker_url)
                self._connected = True
                logger.info(f"Despachador conectado a {self.broker_url}")
        except Exception as e:
            logger.error(f"Error conectando despachador: {e}")
            self._connected = False
            raise

    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self._connected

    def publicar_evento(self, topico: str, evento: Dict[str, Any]) -> bool:
        """Publicar evento simple en un tópico"""
        try:
            if not self._connected:
                self.connect()

            if not self._client:
                logger.error("Cliente Pulsar no disponible")
                return False

            if not topico.startswith("persistent://"):
                topico = f"persistent://public/default/{topico}"

            producer = self._client.create_producer(topico)
            mensaje_json = json.dumps(evento)

            producer.send(mensaje_json.encode("utf-8"))
            producer.close()

            logger.info(
                f"✅ Evento enviado a '{topico}': {evento.get('event_type', 'Unknown')}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error publicando evento: {e}")
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


class ColaboracionPublisher:
    """
    Adaptador para publicar eventos específicos del micro de Colaboraciones
    """

    def __init__(self):
        self.despachador = Despachador()
        self.despachador.connect()

    def publicar_colaboracion_iniciada(self, colaboracion):
        """Publicar evento ColaboracionIniciada"""
        evento = {
            "event_type": "ColaboracionIniciada",
            "colaboracion_id": str(colaboracion.id.codigo),
            "campania_id": str(colaboracion.campania.id.codigo),
            "influencer_id": str(colaboracion.influencer.id.codigo),
            "contrato_id": str(colaboracion.contrato.id.codigo),
            "fecha_inicio": colaboracion.contrato.periodo.inicio.isoformat(),
            "fecha_fin": colaboracion.contrato.periodo.fin.isoformat(),
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "source_service": "colaboraciones",
        }
        return self.despachador.publicar_evento("colaboracion-eventos", evento)

    def publicar_contrato_firmado(self, contrato_id: str, colaboracion):
        """Publicar evento ContratoFirmado"""
        evento = {
            "event_type": "ContratoFirmado",
            "contrato_id": contrato_id,
            "colaboracion_id": str(colaboracion.id.codigo),
            "campania_id": str(colaboracion.campania.id.codigo),
            "influencer_id": str(colaboracion.influencer.id.codigo),
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "source_service": "colaboraciones",
        }
        return self.despachador.publicar_evento("colaboracion-eventos", evento)

    def publicar_contrato_cancelado(self, contrato_id: str, colaboracion, motivo: str):
        """Publicar evento ContratoCancelado"""
        evento = {
            "event_type": "ContratoCancelado",
            "contrato_id": contrato_id,
            "colaboracion_id": str(colaboracion.id.codigo),
            "campania_id": str(colaboracion.campania.id.codigo),
            "influencer_id": str(colaboracion.influencer.id.codigo),
            "motivo": motivo,
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "source_service": "colaboraciones",
        }
        return self.despachador.publicar_evento("colaboracion-eventos", evento)

    def publicar_colaboracion_finalizada(self, colaboracion):
        """Publicar evento ColaboracionFinalizada"""
        evento = {
            "event_type": "ColaboracionFinalizada",
            "colaboracion_id": str(colaboracion.id.codigo),
            "campania_id": str(colaboracion.campania.id.codigo),
            "influencer_id": str(colaboracion.influencer.id.codigo),
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "source_service": "colaboraciones",
        }
        return self.despachador.publicar_evento("colaboracion-eventos", evento)

    def publicar_publicacion_registrada(self, colaboracion, publicacion):
        """Publicar evento PublicacionRegistrada"""
        evento = {
            "event_type": "PublicacionRegistrada",
            "colaboracion_id": str(colaboracion.id.codigo),
            "campania_id": str(colaboracion.campania.id.codigo),
            "influencer_id": str(colaboracion.influencer.id.codigo),
            "url": publicacion.url,
            "red": publicacion.red,
            "fecha": publicacion.fecha.isoformat(),
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "source_service": "colaboraciones",
        }
        return self.despachador.publicar_evento("publicaciones-registradas", evento)

    def close(self):
        """Cerrar despachador"""
        self.despachador.close()
