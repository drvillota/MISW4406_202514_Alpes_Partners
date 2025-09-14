"""Repositorios de consultas - optimizados para lectura

En este archivo se definen los repositorios optimizados para queries/lectura

"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from ..read.models import (
    AfiliadoRead, ConversionRead, ComisionRead, 
    AfiliadoMetricasDiarias, ComisionesReporte
)

class AfiliadoQueryRepository:
    """Repositorio de consultas para Afiliado - optimizado para lectura"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, affiliate_id: UUID) -> Optional[Dict[str, Any]]:
        """Obtiene un afiliado por ID para consultas"""
        afiliado = self.session.query(AfiliadoRead).filter(
            AfiliadoRead.id == affiliate_id
        ).first()
        
        if not afiliado:
            return None
        
        return self._to_dict(afiliado)
    
    def get_all_active(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtiene todos los afiliados activos"""
        afiliados = self.session.query(AfiliadoRead).filter(
            AfiliadoRead.activo == True
        ).offset(offset).limit(limit).all()
        
        return [self._to_dict(a) for a in afiliados]
    
    def search_by_name(self, nombre_parcial: str) -> List[Dict[str, Any]]:
        """Busca afiliados por nombre parcial"""
        afiliados = self.session.query(AfiliadoRead).filter(
            AfiliadoRead.nombre.ilike(f'%{nombre_parcial}%')
        ).all()
        
        return [self._to_dict(a) for a in afiliados]
    
    def get_top_performers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene los afiliados con mejor rendimiento"""
        afiliados = self.session.query(AfiliadoRead).filter(
            AfiliadoRead.activo == True
        ).order_by(
            desc(AfiliadoRead.total_comisiones_pagadas)
        ).limit(limit).all()
        
        return [self._to_dict(a) for a in afiliados]
    
    def get_with_pending_commissions(self) -> List[Dict[str, Any]]:
        """Obtiene afiliados con comisiones pendientes"""
        afiliados = self.session.query(AfiliadoRead).filter(
            and_(
                AfiliadoRead.activo == True,
                AfiliadoRead.total_comisiones_pendientes > 0
            )
        ).all()
        
        return [self._to_dict(a) for a in afiliados]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de métricas globales de afiliados"""
        resultado = self.session.query(
            func.count(AfiliadoRead.id).label('total_afiliados'),
            func.count().filter(AfiliadoRead.activo == True).label('afiliados_activos'),
            func.avg(AfiliadoRead.tasa_comision).label('tasa_promedio'),
            func.sum(AfiliadoRead.total_comisiones_pagadas).label('total_comisiones_pagadas'),
            func.sum(AfiliadoRead.total_comisiones_pendientes).label('total_comisiones_pendientes')
        ).first()
        
        return {
            'total_afiliados': resultado.total_afiliados or 0,
            'afiliados_activos': resultado.afiliados_activos or 0,
            'tasa_comision_promedio': float(resultado.tasa_promedio or 0),
            'total_comisiones_pagadas': float(resultado.total_comisiones_pagadas or 0),
            'total_comisiones_pendientes': float(resultado.total_comisiones_pendientes or 0)
        }
    
    def _to_dict(self, afiliado: AfiliadoRead) -> Dict[str, Any]:
        """Convierte un modelo de lectura a diccionario"""
        return {
            'id': str(afiliado.id),
            'nombre': afiliado.nombre,
            'tasa_comision': afiliado.tasa_comision,
            'email': afiliado.email,
            'telefono': afiliado.telefono,
            'activo': afiliado.activo,
            'fecha_registro': afiliado.fecha_registro.isoformat() if afiliado.fecha_registro else None,
            'total_conversiones': afiliado.total_conversiones,
            'total_comisiones_pagadas': afiliado.total_comisiones_pagadas,
            'total_comisiones_pendientes': afiliado.total_comisiones_pendientes,
            'total_ingresos_generados': afiliado.total_ingresos_generados,
            'ultima_conversion': afiliado.ultima_conversion.isoformat() if afiliado.ultima_conversion else None,
            'ultima_comision_pagada': afiliado.ultima_comision_pagada.isoformat() if afiliado.ultima_comision_pagada else None
        }

class ConversionQueryRepository:
    """Repositorio de consultas para Conversion - optimizado para lectura"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_affiliate(self, affiliate_id: UUID, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtiene conversiones por afiliado"""
        conversiones = self.session.query(ConversionRead).filter(
            ConversionRead.affiliate_id == affiliate_id
        ).order_by(desc(ConversionRead.occurred_at)).offset(offset).limit(limit).all()
        
        return [self._to_dict(c) for c in conversiones]
    
    def get_by_date_range(self, desde: datetime, hasta: datetime) -> List[Dict[str, Any]]:
        """Obtiene conversiones en un rango de fechas"""
        conversiones = self.session.query(ConversionRead).filter(
            and_(
                ConversionRead.occurred_at >= desde,
                ConversionRead.occurred_at <= hasta
            )
        ).order_by(desc(ConversionRead.occurred_at)).all()
        
        return [self._to_dict(c) for c in conversiones]
    
    def get_analytics_by_type(self) -> List[Dict[str, Any]]:
        """Obtiene analytics por tipo de evento"""
        resultado = self.session.query(
            ConversionRead.event_type,
            func.count(ConversionRead.id).label('total_conversiones'),
            func.sum(ConversionRead.monto).label('monto_total'),
            func.avg(ConversionRead.monto).label('monto_promedio'),
            func.sum(ConversionRead.comision_generada).label('comisiones_generadas')
        ).group_by(ConversionRead.event_type).all()
        
        return [
            {
                'event_type': r.event_type,
                'total_conversiones': r.total_conversiones,
                'monto_total': float(r.monto_total or 0),
                'monto_promedio': float(r.monto_promedio or 0),
                'comisiones_generadas': float(r.comisiones_generadas or 0)
            }
            for r in resultado
        ]
    
    def _to_dict(self, conversion: ConversionRead) -> Dict[str, Any]:
        """Convierte una conversión de lectura a diccionario"""
        return {
            'id': str(conversion.id),
            'affiliate_id': str(conversion.affiliate_id),
            'affiliate_name': conversion.affiliate_name,
            'event_type': conversion.event_type,
            'monto': conversion.monto,
            'moneda': conversion.moneda,
            'occurred_at': conversion.occurred_at.isoformat(),
            'comision_generada': conversion.comision_generada,
            'comision_pagada': conversion.comision_pagada
        }

class ComisionQueryRepository:
    """Repositorio de consultas para Comision - optimizado para lectura"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_affiliate(self, affiliate_id: UUID, desde: str = None, hasta: str = None) -> List[Dict[str, Any]]:
        """Obtiene comisiones por afiliado con filtros opcionales"""
        query = self.session.query(ComisionRead).filter(
            ComisionRead.affiliate_id == affiliate_id
        )
        
        if desde:
            query = query.filter(ComisionRead.fecha_creacion >= datetime.fromisoformat(desde))
        
        if hasta:
            query = query.filter(ComisionRead.fecha_creacion <= datetime.fromisoformat(hasta))
        
        comisiones = query.order_by(desc(ComisionRead.fecha_creacion)).all()
        return [self._to_dict(c) for c in comisiones]
    
    def get_pending_commissions(self) -> List[Dict[str, Any]]:
        """Obtiene todas las comisiones pendientes"""
        comisiones = self.session.query(ComisionRead).filter(
            ComisionRead.estado == 'pendiente'
        ).order_by(ComisionRead.fecha_creacion).all()
        
        return [self._to_dict(c) for c in comisiones]
    
    def get_monthly_report(self, año: int, mes: int) -> List[Dict[str, Any]]:
        """Genera reporte mensual de comisiones"""
        resultado = self.session.query(
            ComisionesReporte.affiliate_id,
            ComisionesReporte.affiliate_name,
            func.count(ComisionesReporte.id).label('total_comisiones'),
            func.sum(ComisionesReporte.valor_comision).label('total_valor'),
            func.sum().filter(ComisionesReporte.estado == 'pagada').label('comisiones_pagadas'),
            func.sum(ComisionesReporte.valor_comision).filter(ComisionesReporte.estado == 'pagada').label('valor_pagado')
        ).filter(
            and_(
                ComisionesReporte.año == año,
                ComisionesReporte.mes == mes
            )
        ).group_by(
            ComisionesReporte.affiliate_id,
            ComisionesReporte.affiliate_name
        ).all()
        
        return [
            {
                'affiliate_id': str(r.affiliate_id),
                'affiliate_name': r.affiliate_name,
                'total_comisiones': r.total_comisiones,
                'total_valor': float(r.total_valor or 0),
                'comisiones_pagadas': r.comisiones_pagadas or 0,
                'valor_pagado': float(r.valor_pagado or 0),
                'valor_pendiente': float((r.total_valor or 0) - (r.valor_pagado or 0))
            }
            for r in resultado
        ]
    
    def get_payment_analytics(self) -> Dict[str, Any]:
        """Obtiene analytics de pagos"""
        resultado = self.session.query(
            func.count(ComisionRead.id).label('total_comisiones'),
            func.sum(ComisionRead.valor_comision).label('valor_total'),
            func.count().filter(ComisionRead.estado == 'pagada').label('comisiones_pagadas'),
            func.sum(ComisionRead.valor_comision).filter(ComisionRead.estado == 'pagada').label('valor_pagado'),
            func.count().filter(ComisionRead.estado == 'pendiente').label('comisiones_pendientes'),
            func.sum(ComisionRead.valor_comision).filter(ComisionRead.estado == 'pendiente').label('valor_pendiente')
        ).first()
        
        return {
            'total_comisiones': resultado.total_comisiones or 0,
            'valor_total': float(resultado.valor_total or 0),
            'comisiones_pagadas': resultado.comisiones_pagadas or 0,
            'valor_pagado': float(resultado.valor_pagado or 0),
            'comisiones_pendientes': resultado.comisiones_pendientes or 0,
            'valor_pendiente': float(resultado.valor_pendiente or 0)
        }
    
    def _to_dict(self, comision: ComisionRead) -> Dict[str, Any]:
        """Convierte una comisión de lectura a diccionario"""
        return {
            'commission_id': str(comision.id),
            'affiliate_id': str(comision.affiliate_id),
            'affiliate_name': comision.affiliate_name,
            'valor': comision.valor_comision,
            'moneda': comision.moneda,
            'estado': comision.estado,
            'created_at': comision.fecha_creacion.isoformat(),
            'fecha_pago': comision.fecha_pago.isoformat() if comision.fecha_pago else None
        }