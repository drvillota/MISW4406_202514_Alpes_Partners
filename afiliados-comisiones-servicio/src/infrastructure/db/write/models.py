"""Modelos de escritura para el dominio de afiliados y comisiones

En este archivo se definen los modelos optimizados para escritura/comandos

"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

WriteBase = declarative_base()

class AfiliadoWrite(WriteBase):
    """Modelo de escritura para Afiliado - optimizado para comandos"""
    __tablename__ = 'afiliados_write'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    tasa_comision = Column(Float, nullable=False)
    email = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Relaciones para comandos
    conversiones = relationship("ConversionWrite", back_populates="afiliado")
    comisiones = relationship("ComisionWrite", back_populates="afiliado")
    
    # Índices optimizados para escritura
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )

class ConversionWrite(WriteBase):
    """Modelo de escritura para Conversión - optimizado para comandos"""
    __tablename__ = 'conversiones_write'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id = Column(UUID(as_uuid=True), ForeignKey('afiliados_write.id'), nullable=False)
    event_type = Column(String(50), nullable=False)
    monto = Column(Float, nullable=False)
    moneda = Column(String(3), nullable=False)
    metadatos = Column(Text, nullable=True)  # JSON serializado
    occurred_at = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Relaciones
    afiliado = relationship("AfiliadoWrite", back_populates="conversiones")
    comisiones = relationship("ComisionWrite", back_populates="conversion")
    
    # Índices para escritura eficiente
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )

class ComisionWrite(WriteBase):
    """Modelo de escritura para Comisión - optimizado para comandos"""
    __tablename__ = 'comisiones_write'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id = Column(UUID(as_uuid=True), ForeignKey('afiliados_write.id'), nullable=False)
    conversion_id = Column(UUID(as_uuid=True), ForeignKey('conversiones_write.id'), nullable=True)
    monto_base = Column(Float, nullable=False)
    tasa_comision = Column(Float, nullable=False)
    valor_comision = Column(Float, nullable=False)
    moneda = Column(String(3), nullable=False)
    estado = Column(String(20), nullable=False, default='pendiente')
    fecha_pago = Column(DateTime, nullable=True)
    fecha_cancelacion = Column(DateTime, nullable=True)
    observaciones = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Relaciones
    afiliado = relationship("AfiliadoWrite", back_populates="comisiones")
    conversion = relationship("ConversionWrite", back_populates="comisiones")
    
    # Índices para escritura
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )

class OutboxEvent(WriteBase):
    """Modelo para outbox pattern - garantiza consistencia transaccional"""
    __tablename__ = 'outbox_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    aggregate_type = Column(String(50), nullable=False)  # 'Afiliado', 'Comision', etc.
    event_type = Column(String(100), nullable=False)     # 'AfiliadoCreado', 'ComisionPagada', etc.
    event_data = Column(Text, nullable=False)            # JSON del evento
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending')       # 'pending', 'processed', 'failed'
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Índices para eficiencia en outbox pattern
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )