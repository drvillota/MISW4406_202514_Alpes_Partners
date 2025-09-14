"""Fábricas para el dominio de comisiones

En este archivo se definen las fábricas para crear agregados y entidades del dominio de comisiones

"""

from typing import Dict, Any, Optional
from uuid import uuid4, UUID
from datetime import datetime
from ...core.seedwork.fabricas import Fabrica
from ...core.seedwork.objetos_valor import Dinero, EstadoComision
from .agregados import Conversion, Comision
from .objetos_valor import TipoEvento, MetadatosEvento, FechaOcurrencia, CalculoComision

class FabricaConversion(Fabrica):
    """Fábrica para crear agregados de Conversión"""
    
    def crear(self, datos: Dict[str, Any]) -> Conversion:
        """Crea un agregado Conversion a partir de los datos proporcionados"""
        campos_requeridos = ['affiliate_id', 'event_type', 'monto', 'moneda']
        self.validar_datos_requeridos(datos, campos_requeridos)
        
        # Crear objetos de valor
        tipo_evento = TipoEvento(datos['event_type'])
        monto = Dinero(datos['monto'], datos['moneda'])
        
        # Crear metadatos si se proporcionan
        metadatos = None
        if 'metadatos' in datos and datos['metadatos']:
            metadatos = MetadatosEvento(datos['metadatos'])
        
        # Crear fecha de ocurrencia
        fecha_ocurrencia = None
        if 'occurred_at' in datos:
            fecha_ocurrencia = FechaOcurrencia(datos['occurred_at'])
        
        # Crear el agregado
        conversion = Conversion(
            id=datos.get('id', uuid4()),
            affiliate_id=datos['affiliate_id'],
            tipo_evento=tipo_evento,
            monto=monto,
            metadatos=metadatos,
            fecha_ocurrencia=fecha_ocurrencia
        )
        
        return conversion
    
    def crear_desde_evento_externo(self, evento: Dict[str, Any]) -> Conversion:
        """Crea una Conversión desde un evento externo/integración"""
        # Mapear campos del evento externo al formato interno
        datos = {
            'affiliate_id': UUID(evento['affiliate_id']) if isinstance(evento['affiliate_id'], str) else evento['affiliate_id'],
            'event_type': evento.get('type', 'click'),
            'monto': float(evento.get('amount', 0.0)),
            'moneda': evento.get('currency', 'USD'),
            'metadatos': evento.get('metadata', {}),
            'occurred_at': datetime.fromisoformat(evento['timestamp']) if 'timestamp' in evento else datetime.utcnow()
        }
        
        return self.crear(datos)

class FabricaComision(Fabrica):
    """Fábrica para crear agregados de Comisión"""
    
    def crear(self, datos: Dict[str, Any]) -> Comision:
        """Crea un agregado Comision a partir de los datos proporcionados"""
        campos_requeridos = ['affiliate_id', 'conversion_id', 'monto_base', 'moneda', 'tasa_comision']
        self.validar_datos_requeridos(datos, campos_requeridos)
        
        # Crear el cálculo de comisión
        monto_base = Dinero(datos['monto_base'], datos['moneda'])
        calculo = CalculoComision.calcular(monto_base, datos['tasa_comision'])
        
        # Estado inicial
        estado = EstadoComision(datos.get('estado', 'pendiente'))
        
        # Crear el agregado
        comision = Comision(
            id=datos.get('id', uuid4()),
            affiliate_id=datos['affiliate_id'],
            conversion_id=datos['conversion_id'],
            calculo=calculo,
            estado=estado,
            fecha_pago=datos.get('fecha_pago'),
            fecha_cancelacion=datos.get('fecha_cancelacion'),
            observaciones=datos.get('observaciones')
        )
        
        return comision
    
    def crear_desde_conversion(self, conversion: Conversion, tasa_comision: float) -> Optional[Comision]:
        """Crea una Comisión a partir de una Conversión"""
        # Verificar si la conversión es elegible para comisión
        if not conversion.es_elegible_para_comision():
            return None
        
        datos = {
            'affiliate_id': conversion.affiliate_id,
            'conversion_id': conversion.id,
            'monto_base': conversion.monto.monto,
            'moneda': conversion.monto.moneda,
            'tasa_comision': tasa_comision
        }
        
        return self.crear(datos)
    
    def crear_comision_manual(self, affiliate_id: UUID, monto: float, moneda: str, tasa: float, observaciones: str = None) -> Comision:
        """Crea una comisión manual (no basada en conversión)"""
        datos = {
            'affiliate_id': affiliate_id,
            'conversion_id': uuid4(),  # ID ficticio para comisiones manuales
            'monto_base': monto,
            'moneda': moneda,
            'tasa_comision': tasa,
            'observaciones': observaciones or "Comisión manual"
        }
        
        return self.crear(datos)