"""Event Mapper para convertir eventos externos a eventos de dominio de Colaboraciones"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from ...domain.eventos import (
    ColaboracionIniciada,
    ContratoFirmado,
    ContratoCancelado,
    ColaboracionFinalizada,
    PublicacionRegistrada,
)

logger = logging.getLogger(__name__)


class EventMapper:
    """Mapper que convierte eventos de Pulsar a eventos de dominio"""

    def map_colaboracion_event(self, pulsar_data: Dict[str, Any]) -> Optional[Any]:
        """Mapea eventos relacionados con colaboraciones"""
        try:
            event_type = pulsar_data.get("event_type", pulsar_data.get("type", ""))

            if event_type == "ColaboracionIniciada":
                return ColaboracionIniciada(
                    colaboracion_id=str(pulsar_data["colaboracion_id"]),
                    campania_id=str(pulsar_data.get("campania_id", "")),
                    influencer_id=str(pulsar_data.get("influencer_id", "")),
                    contrato_id=str(pulsar_data.get("contrato_id", "")),
                    fecha_inicio=pulsar_data.get("fecha_inicio"),
                    fecha_fin=pulsar_data.get("fecha_fin"),
                    timestamp=self._convert_to_unix_timestamp(
                        pulsar_data.get("timestamp")
                    ),
                )

            elif event_type == "ContratoFirmado":
                return ContratoFirmado(
                    contrato_id=str(pulsar_data["contrato_id"]),
                    colaboracion_id=str(pulsar_data.get("colaboracion_id", "")),
                    timestamp=self._convert_to_unix_timestamp(
                        pulsar_data.get("timestamp")
                    ),
                )

            elif event_type == "ContratoCancelado":
                return ContratoCancelado(
                    contrato_id=str(pulsar_data["contrato_id"]),
                    colaboracion_id=str(pulsar_data.get("colaboracion_id", "")),
                    motivo=pulsar_data.get("motivo", "No especificado"),
                    timestamp=self._convert_to_unix_timestamp(
                        pulsar_data.get("timestamp")
                    ),
                )

            elif event_type == "ColaboracionFinalizada":
                return ColaboracionFinalizada(
                    colaboracion_id=str(pulsar_data["colaboracion_id"]),
                    timestamp=self._convert_to_unix_timestamp(
                        pulsar_data.get("timestamp")
                    ),
                )

            elif event_type == "PublicacionRegistrada":
                return PublicacionRegistrada(
                    colaboracion_id=str(pulsar_data["colaboracion_id"]),
                    url=pulsar_data.get("url", ""),
                    red=pulsar_data.get("red", ""),
                    fecha=pulsar_data.get("fecha"),
                    timestamp=self._convert_to_unix_timestamp(
                        pulsar_data.get("timestamp")
                    ),
                )

            else:
                logger.warning(f"Unknown colaboracion event type: {event_type}")
                return None

        except Exception as e:
            logger.error(f"Error mapping colaboracion event: {e}, data: {pulsar_data}")
            return None

    def _convert_to_unix_timestamp(self, timestamp: Any) -> int:
        """Convierte timestamp a Unix timestamp (segundos)"""
        if timestamp is None:
            return int(datetime.now().timestamp())

        try:
            if isinstance(timestamp, int):
                return timestamp if timestamp < 10**10 else timestamp // 1000
            if isinstance(timestamp, float):
                return int(timestamp)
            if isinstance(timestamp, datetime):
                return int(timestamp.timestamp())
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    return int(dt.timestamp())
                except ValueError:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    return int(dt.timestamp())
        except Exception as e:
            logger.warning(f"Could not parse timestamp {timestamp}: {e}")

        return int(datetime.now().timestamp())