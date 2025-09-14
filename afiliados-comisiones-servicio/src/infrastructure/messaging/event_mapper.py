"""Event Mapper para convertir eventos externos a eventos de dominio

En este archivo se definen los mappers para convertir eventos de Pulsar a eventos de dominio

"""

import logging
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any, Dict, Optional
from ...domains.affiliates.eventos import AfiliadoCreado, AfiliadoActivado, AfiliadoDesactivado, TasaComisionActualizada
from ...domains.commissions.events import ConversionRegistrada, ComisionCreada, ComisionPagada, ComisionCancelada

logger = logging.getLogger(__name__)

class EventMapper:
    """Mapper que convierte eventos de Pulsar a eventos de dominio"""

    def map_affiliate_event(self, pulsar_data: Dict[str, Any]) -> Optional[Any]:
        """Mapea eventos de afiliados desde Pulsar"""
        try:
            event_type = pulsar_data.get('event_type', pulsar_data.get('type', ''))
            
            if event_type == 'AfiliadoCreado' or event_type == 'affiliate_created':
                return AfiliadoCreado(
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    nombre=pulsar_data.get('nombre', pulsar_data.get('name', '')),
                    tasa_comision=float(pulsar_data.get('tasa_comision', pulsar_data.get('commission_rate', 0.0))),
                    fecha_registro=self._parse_timestamp(pulsar_data.get('fecha_registro', pulsar_data.get('created_at')))
                )
            
            elif event_type == 'AfiliadoActivado' or event_type == 'affiliate_activated':
                return AfiliadoActivado(
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    fecha_activacion=self._parse_timestamp(pulsar_data.get('fecha_activacion', pulsar_data.get('activated_at')))
                )
            
            elif event_type == 'AfiliadoDesactivado' or event_type == 'affiliate_deactivated':
                return AfiliadoDesactivado(
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    motivo=pulsar_data.get('motivo', pulsar_data.get('reason', 'No especificado')),
                    fecha_desactivacion=self._parse_timestamp(pulsar_data.get('fecha_desactivacion', pulsar_data.get('deactivated_at')))
                )
            
            elif event_type == 'TasaComisionActualizada' or event_type == 'commission_rate_updated':
                return TasaComisionActualizada(
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    tasa_anterior=float(pulsar_data.get('tasa_anterior', pulsar_data.get('old_rate', 0.0))),
                    nueva_tasa=float(pulsar_data.get('nueva_tasa', pulsar_data.get('new_rate', 0.0))),
                    fecha_cambio=self._parse_timestamp(pulsar_data.get('fecha_cambio', pulsar_data.get('updated_at')))
                )
            
            else:
                logger.warning(f"Unknown affiliate event type: {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error mapping affiliate event: {e}, data: {pulsar_data}")
            return None

    def map_conversion_event(self, pulsar_data: Dict[str, Any]) -> Optional[ConversionRegistrada]:
        """Mapea eventos de conversiones desde Pulsar"""
        try:
            return ConversionRegistrada(
                affiliate_id=UUID(pulsar_data['affiliate_id']),
                event_type=pulsar_data.get('event_type', pulsar_data.get('type', 'click')),
                monto=float(pulsar_data.get('monto', pulsar_data.get('amount', 0.0))),
                moneda=pulsar_data.get('moneda', pulsar_data.get('currency', 'USD')),
                occurred_at=self._parse_timestamp(pulsar_data.get('occurred_at', pulsar_data.get('timestamp')))
            )
            
        except Exception as e:
            logger.error(f"Error mapping conversion event: {e}, data: {pulsar_data}")
            return None

    def map_commission_event(self, pulsar_data: Dict[str, Any]) -> Optional[Any]:
        """Mapea eventos de comisiones desde Pulsar"""
        try:
            event_type = pulsar_data.get('event_type', pulsar_data.get('type', ''))
            
            if event_type == 'ComisionCreada' or event_type == 'commission_created':
                return ComisionCreada(
                    commission_id=UUID(pulsar_data['commission_id']),
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    valor=float(pulsar_data.get('valor', pulsar_data.get('amount', 0.0))),
                    moneda=pulsar_data.get('moneda', pulsar_data.get('currency', 'USD'))
                )
            
            elif event_type == 'ComisionPagada' or event_type == 'commission_paid':
                return ComisionPagada(
                    commission_id=UUID(pulsar_data['commission_id']),
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    valor=float(pulsar_data.get('valor', pulsar_data.get('amount', 0.0))),
                    fecha_pago=self._parse_timestamp(pulsar_data.get('fecha_pago', pulsar_data.get('paid_at')))
                )
            
            elif event_type == 'ComisionCancelada' or event_type == 'commission_cancelled':
                return ComisionCancelada(
                    commission_id=UUID(pulsar_data['commission_id']),
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    motivo=pulsar_data.get('motivo', pulsar_data.get('reason', 'No especificado')),
                    fecha_cancelacion=self._parse_timestamp(pulsar_data.get('fecha_cancelacion', pulsar_data.get('cancelled_at')))
                )
            
            else:
                logger.warning(f"Unknown commission event type: {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error mapping commission event: {e}, data: {pulsar_data}")
            return None

    def map_external_tracking_event(self, pulsar_data: Dict[str, Any]) -> Optional[ConversionRegistrada]:
        """Mapea eventos externos de tracking a eventos de conversión"""
        try:
            # Mapear diferentes formatos de eventos externos
            if 'click' in pulsar_data:
                return ConversionRegistrada(
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    event_type='click',
                    monto=0.0,  # Los clicks no tienen monto
                    moneda='USD',
                    occurred_at=self._parse_timestamp(pulsar_data.get('timestamp'))
                )
            
            elif 'sale' in pulsar_data or 'purchase' in pulsar_data:
                sale_data = pulsar_data.get('sale', pulsar_data.get('purchase', {}))
                return ConversionRegistrada(
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    event_type='sale',
                    monto=float(sale_data.get('amount', 0.0)),
                    moneda=sale_data.get('currency', 'USD'),
                    occurred_at=self._parse_timestamp(pulsar_data.get('timestamp'))
                )
            
            elif 'lead' in pulsar_data or 'signup' in pulsar_data:
                return ConversionRegistrada(
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    event_type='lead',
                    monto=float(pulsar_data.get('value', 0.0)),
                    moneda=pulsar_data.get('currency', 'USD'),
                    occurred_at=self._parse_timestamp(pulsar_data.get('timestamp'))
                )
            
            else:
                # Formato genérico
                return ConversionRegistrada(
                    affiliate_id=UUID(pulsar_data['affiliate_id']),
                    event_type=pulsar_data.get('action', 'view'),
                    monto=float(pulsar_data.get('amount', pulsar_data.get('value', 0.0))),
                    moneda=pulsar_data.get('currency', 'USD'),
                    occurred_at=self._parse_timestamp(pulsar_data.get('timestamp'))
                )
                
        except Exception as e:
            logger.error(f"Error mapping external tracking event: {e}, data: {pulsar_data}")
            return None

    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp en diferentes formatos"""
        if timestamp is None:
            return datetime.utcnow()
        
        try:
            # Si ya es datetime
            if isinstance(timestamp, datetime):
                return timestamp
            
            # Si es timestamp Unix (segundos)
            if isinstance(timestamp, (int, float)):
                # Detectar si está en milisegundos o segundos
                if timestamp > 10**10:  # Probablemente milisegundos
                    return datetime.fromtimestamp(timestamp / 1000)
                else:  # Segundos
                    return datetime.fromtimestamp(timestamp)
            
            # Si es string ISO
            if isinstance(timestamp, str):
                # Intentar parsear ISO format
                try:
                    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    # Intentar con formato estándar
                    return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.warning(f"Could not parse timestamp {timestamp}: {e}")
        
        # Fallback a tiempo actual
        return datetime.utcnow()

    def _safe_uuid(self, value: Any) -> UUID:
        """Convierte un valor a UUID de manera segura"""
        if isinstance(value, UUID):
            return value
        
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                logger.warning(f"Invalid UUID string: {value}")
                return uuid4()
        
        # Fallback a UUID aleatorio
        return uuid4()