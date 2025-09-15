"""Modelos SQLAlchemy simplificados para afiliados-comisiones"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from .sqlalchemy import Base

class AffiliateModel(Base):
    """Modelo de Afiliado simplificado"""
    __tablename__ = "affiliates"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    commission_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # Permite 999.99%
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

class ConversionEventModel(Base):
    """Modelo de Evento de Conversión simplificado"""
    __tablename__ = "conversion_events"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    affiliate_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("affiliates.id"), 
        nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PURCHASE, SIGNUP, etc.
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

class CommissionModel(Base):
    """Modelo de Comisión simplificado"""
    __tablename__ = "commissions"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    affiliate_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("affiliates.id"), 
        nullable=False
    )
    conversion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("conversion_events.id"),
        nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, paid, cancelled
    calculated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
