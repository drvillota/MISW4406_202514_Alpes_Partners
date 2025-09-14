"""Modelos de lectura para consultas optimizadas

En este archivo se definen los modelos optimizados para lectura/queries

"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

ReadBase = declarative_base()

class AfiliadoRead(ReadBase):
    """Modelo de lectura para Afiliado - optimizado para consultas"""
    __tablename__ = 'afiliados_read'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    nombre = Column(String(255), nullable=False)
    tasa_comision = Column(Float, nullable=False)
    email = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, nullable=False)
    
    # Métricas desnormalizadas para consultas rápidas
    total_conversiones = Column(Integer, default=0)
    total_comisiones_pagadas = Column(Float, default=0.0)
    total_comisiones_pendientes = Column(Float, default=0.0)
    total_ingresos_generados = Column(Float, default=0.0)
    ultima_conversion = Column(DateTime, nullable=True)
    ultima_comision_pagada = Column(DateTime, nullable=True)
    
    # Campos para auditoría
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow)
    
    # Índices optimizados para consultas
    __table_args__ = (
        Index('idx_afiliado_activo', 'activo'),
        Index('idx_afiliado_nombre', 'nombre'),
        Index('idx_afiliado_tasa', 'tasa_comision'),
        Index('idx_afiliado_fecha_registro', 'fecha_registro'),
        {'mysql_engine': 'MyISAM'},  # Optimizado para lecturas
    )

class ConversionRead(ReadBase):
    """Modelo de lectura para Conversión - optimizado para consultas"""
    __tablename__ = 'conversiones_read'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    affiliate_id = Column(UUID(as_uuid=True), nullable=False)
    affiliate_name = Column(String(255), nullable=False)  # Desnormalizado
    event_type = Column(String(50), nullable=False)
    monto = Column(Float, nullable=False)
    moneda = Column(String(3), nullable=False)
    occurred_at = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False)
    
    # Campos calculados/desnormalizados
    comision_generada = Column(Float, default=0.0)
    comision_pagada = Column(Boolean, default=False)
    
    # Índices optimizados para consultas analíticas
    __table_args__ = (
        Index('idx_conversion_affiliate', 'affiliate_id'),
        Index('idx_conversion_date', 'occurred_at'),
        Index('idx_conversion_type', 'event_type'),
        Index('idx_conversion_monto', 'monto'),
        Index('idx_conversion_affiliate_date', 'affiliate_id', 'occurred_at'),
        {'mysql_engine': 'MyISAM'},
    )

class ComisionRead(ReadBase):
    """Modelo de lectura para Comisión - optimizado para consultas"""
    __tablename__ = 'comisiones_read'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    affiliate_id = Column(UUID(as_uuid=True), nullable=False)
    affiliate_name = Column(String(255), nullable=False)  # Desnormalizado
    conversion_id = Column(UUID(as_uuid=True), nullable=True)
    monto_base = Column(Float, nullable=False)
    tasa_comision = Column(Float, nullable=False)
    valor_comision = Column(Float, nullable=False)
    moneda = Column(String(3), nullable=False)
    estado = Column(String(20), nullable=False)
    fecha_pago = Column(DateTime, nullable=True)
    fecha_cancelacion = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, nullable=False)
    
    # Campos para reportes
    año_creacion = Column(Integer, nullable=False)
    mes_creacion = Column(Integer, nullable=False)
    trimestre_creacion = Column(Integer, nullable=False)
    
    # Índices optimizados para reportes
    __table_args__ = (
        Index('idx_comision_affiliate', 'affiliate_id'),
        Index('idx_comision_estado', 'estado'),
        Index('idx_comision_fecha_creacion', 'fecha_creacion'),
        Index('idx_comision_fecha_pago', 'fecha_pago'),
        Index('idx_comision_año_mes', 'año_creacion', 'mes_creacion'),
        Index('idx_comision_affiliate_estado', 'affiliate_id', 'estado'),
        Index('idx_comision_reporte', 'affiliate_id', 'estado', 'fecha_creacion'),
        {'mysql_engine': 'MyISAM'},
    )

class AfiliadoMetricasDiarias(ReadBase):
    """Vista materializada para métricas diarias de afiliados"""
    __tablename__ = 'afiliado_metricas_diarias'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id = Column(UUID(as_uuid=True), nullable=False)
    affiliate_name = Column(String(255), nullable=False)
    fecha = Column(DateTime, nullable=False)
    
    # Métricas del día
    conversiones_del_dia = Column(Integer, default=0)
    ingresos_del_dia = Column(Float, default=0.0)
    comisiones_generadas_del_dia = Column(Float, default=0.0)
    comisiones_pagadas_del_dia = Column(Float, default=0.0)
    
    # Métricas acumuladas
    conversiones_acumuladas = Column(Integer, default=0)
    ingresos_acumulados = Column(Float, default=0.0)
    comisiones_acumuladas = Column(Float, default=0.0)
    
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow)
    
    # Índices para consultas de reportes temporales
    __table_args__ = (
        Index('idx_metricas_affiliate_fecha', 'affiliate_id', 'fecha'),
        Index('idx_metricas_fecha', 'fecha'),
        {'mysql_engine': 'MyISAM'},
    )

class ComisionesReporte(ReadBase):
    """Vista desnormalizada para reportes de comisiones"""
    __tablename__ = 'comisiones_reporte'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    
    # Datos del afiliado
    affiliate_id = Column(UUID(as_uuid=True), nullable=False)
    affiliate_name = Column(String(255), nullable=False)
    affiliate_email = Column(String(255), nullable=True)
    affiliate_tasa = Column(Float, nullable=False)
    
    # Datos de la comisión
    valor_comision = Column(Float, nullable=False)
    moneda = Column(String(3), nullable=False)
    estado = Column(String(20), nullable=False)
    fecha_creacion = Column(DateTime, nullable=False)
    fecha_pago = Column(DateTime, nullable=True)
    
    # Datos de la conversión
    conversion_type = Column(String(50), nullable=True)
    conversion_monto = Column(Float, nullable=True)
    
    # Campos para agrupación en reportes
    año = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    semana_año = Column(Integer, nullable=False)
    
    # Índices para reportes complejos
    __table_args__ = (
        Index('idx_reporte_affiliate_periodo', 'affiliate_id', 'año', 'mes'),
        Index('idx_reporte_estado_fecha', 'estado', 'fecha_creacion'),
        Index('idx_reporte_periodo', 'año', 'mes', 'trimestre'),
        {'mysql_engine': 'MyISAM'},
    )