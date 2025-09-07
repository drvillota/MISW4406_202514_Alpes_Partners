from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from .sqlalchemy import Base

class AfiliadoModel(Base):
    __tablename__ = "afiliados"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tasa_comision: Mapped[float] = mapped_column(Float, nullable=False)

class ConversionModel(Base):
    __tablename__ = "conversions"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    affiliate_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("afiliados.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    moneda: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

class ComisionModel(Base):
    __tablename__ = "comisiones"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    affiliate_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("afiliados.id"), nullable=False)
    conversion_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    moneda: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
