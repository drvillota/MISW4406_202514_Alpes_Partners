"""Event Mapper para convertir eventos externos a eventos de dominio

En este archivo se definen los mappers para convertir eventos de Pulsar a eventos de dominio
actualizados según la estructura simplificada de events.py
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from ...domain.events import (
    AffiliateRegistered, 
    AffiliateActivated, 
    AffiliateDeactivated, 
    CommissionCalculated,
    ConversionRegistered
)

logger = logging.getLogger(__name__)

class EventMapper:
    """Mapper que convierte eventos de Pulsar a eventos de dominio simplificados"""

    def map_affiliate_event(self, pulsar_data: Dict[str, Any]) -> Optional[Any]:
        """Mapea eventos de afiliados desde Pulsar"""
        try:
            event_type = pulsar_data.get('event_type', pulsar_data.get('type', ''))
            
            if event_type == 'AffiliateRegistered' or event_type == 'affiliate_registered':
                return AffiliateRegistered(
                    affiliate_id=str(pulsar_data['affiliate_id']),
                    name=pulsar_data.get('name', ''),
                    email=pulsar_data.get('email', ''),
                    commission_rate=float(pulsar_data.get('commission_rate', 0.0)),
                    timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
                )
            
            elif event_type == 'AffiliateActivated' or event_type == 'affiliate_activated':
                return AffiliateActivated(
                    affiliate_id=str(pulsar_data['affiliate_id']),
                    timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
                )
            
            elif event_type == 'AffiliateDeactivated' or event_type == 'affiliate_deactivated':
                return AffiliateDeactivated(
                    affiliate_id=str(pulsar_data['affiliate_id']),
                    reason=pulsar_data.get('reason', 'No especificado'),
                    timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
                )
            
            else:
                logger.warning(f"Unknown affiliate event type: {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error mapping affiliate event: {e}, data: {pulsar_data}")
            return None

    def map_conversion_event(self, pulsar_data: Dict[str, Any]) -> Optional[ConversionRegistered]:
        """Mapea eventos de conversiones desde Pulsar"""
        try:
            return ConversionRegistered(
                conversion_id=str(pulsar_data.get('conversion_id', '')),
                affiliate_id=str(pulsar_data['affiliate_id']),
                user_id=str(pulsar_data.get('user_id', '')),
                amount=float(pulsar_data.get('amount', 0.0)),
                currency=pulsar_data.get('currency', 'USD'),
                timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
            )
            
        except Exception as e:
            logger.error(f"Error mapping conversion event: {e}, data: {pulsar_data}")
            return None

    def map_commission_event(self, pulsar_data: Dict[str, Any]) -> Optional[CommissionCalculated]:
        """Mapea eventos de comisiones desde Pulsar"""
        try:
            event_type = pulsar_data.get('event_type', pulsar_data.get('type', ''))
            
            if event_type == 'CommissionCalculated' or event_type == 'commission_calculated':
                return CommissionCalculated(
                    commission_id=str(pulsar_data['commission_id']),
                    affiliate_id=str(pulsar_data['affiliate_id']),
                    conversion_id=str(pulsar_data.get('conversion_id', '')),
                    amount=float(pulsar_data.get('amount', 0.0)),
                    currency=pulsar_data.get('currency', 'USD'),
                    timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
                )
            
            else:
                logger.warning(f"Unknown commission event type: {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error mapping commission event: {e}, data: {pulsar_data}")
            return None

    def map_external_tracking_event(self, pulsar_data: Dict[str, Any]) -> Optional[ConversionRegistered]:
        """Mapea eventos externos de tracking a eventos de conversión"""
        try:
            # Mapear diferentes formatos de eventos externos
            if 'click' in pulsar_data:
                return ConversionRegistered(
                    conversion_id=str(pulsar_data.get('conversion_id', f"click_{pulsar_data['affiliate_id']}")),
                    affiliate_id=str(pulsar_data['affiliate_id']),
                    user_id=str(pulsar_data.get('user_id', '')),
                    amount=0.0,  # Los clicks no tienen monto
                    currency='USD',
                    timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
                )
            
            elif 'sale' in pulsar_data or 'purchase' in pulsar_data:
                sale_data = pulsar_data.get('sale', pulsar_data.get('purchase', {}))
                return ConversionRegistered(
                    conversion_id=str(pulsar_data.get('conversion_id', f"sale_{pulsar_data['affiliate_id']}")),
                    affiliate_id=str(pulsar_data['affiliate_id']),
                    user_id=str(pulsar_data.get('user_id', '')),
                    amount=float(sale_data.get('amount', 0.0)),
                    currency=sale_data.get('currency', 'USD'),
                    timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
                )
            
            elif 'lead' in pulsar_data or 'signup' in pulsar_data:
                return ConversionRegistered(
                    conversion_id=str(pulsar_data.get('conversion_id', f"lead_{pulsar_data['affiliate_id']}")),
                    affiliate_id=str(pulsar_data['affiliate_id']),
                    user_id=str(pulsar_data.get('user_id', '')),
                    amount=float(pulsar_data.get('value', 0.0)),
                    currency=pulsar_data.get('currency', 'USD'),
                    timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
                )
            
            else:
                # Formato genérico
                return ConversionRegistered(
                    conversion_id=str(pulsar_data.get('conversion_id', f"generic_{pulsar_data['affiliate_id']}")),
                    affiliate_id=str(pulsar_data['affiliate_id']),
                    user_id=str(pulsar_data.get('user_id', '')),
                    amount=float(pulsar_data.get('amount', pulsar_data.get('value', 0.0))),
                    currency=pulsar_data.get('currency', 'USD'),
                    timestamp=self._convert_to_unix_timestamp(pulsar_data.get('timestamp'))
                )
                
        except Exception as e:
            logger.error(f"Error mapping external tracking event: {e}, data: {pulsar_data}")
            return None

    def _convert_to_unix_timestamp(self, timestamp: Any) -> int:
        """Convierte timestamp a Unix timestamp (segundos)"""
        if timestamp is None:
            return int(datetime.now().timestamp())
        
        try:
            # Si ya es timestamp Unix
            if isinstance(timestamp, int):
                # Si está en milisegundos, convertir a segundos
                if timestamp > 10**10:
                    return timestamp // 1000
                return timestamp
            
            # Si es float (segundos con decimales)
            if isinstance(timestamp, float):
                return int(timestamp)
            
            # Si es datetime
            if isinstance(timestamp, datetime):
                return int(timestamp.timestamp())
            
            # Si es string ISO
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return int(dt.timestamp())
                except ValueError:
                    # Intentar con formato estándar
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    return int(dt.timestamp())
            
        except Exception as e:
            logger.warning(f"Could not parse timestamp {timestamp}: {e}")
        
        # Fallback a tiempo actual
        return int(datetime.now().timestamp())