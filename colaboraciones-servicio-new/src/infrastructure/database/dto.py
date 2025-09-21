"""Modelos SQLAlchemy para colaboraciones"""

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
from uuid import uuid4
from .sqlalchemy import Base


class CampaniaModel(Base):
    """Modelo de Campaña"""
    __tablename__ = "campanias"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nombre: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    marca: Mapped[str] = mapped_column(String(200), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="NUEVA")

    # Relaciones
    colaboraciones = relationship("ColaboracionModel", back_populates="campania")


class InfluencerModel(Base):
    """Modelo de Influencer"""
    __tablename__ = "influencers"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Relaciones
    colaboraciones = relationship("ColaboracionModel", back_populates="influencer")


class ContratoModel(Base):
    """Modelo de Contrato"""
    __tablename__ = "contratos"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    colaboracion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("colaboraciones.id"), nullable=False
    )
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")

    # Relaciones
    colaboracion = relationship("ColaboracionModel", back_populates="contrato")


class ColaboracionModel(Base):
    """Modelo de Colaboración (raíz de agregación)"""
    __tablename__ = "colaboraciones"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    campania_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campanias.id"), nullable=False
    )
    influencer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("influencers.id"), nullable=False
    )
    contrato_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contratos.id"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="VIGENTE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Campo JSONB para publicaciones
    publicaciones: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)

    # Relaciones
    campania = relationship("CampaniaModel", back_populates="colaboraciones")
    influencer = relationship("InfluencerModel", back_populates="colaboraciones")
    contrato = relationship("ContratoModel", back_populates="colaboracion")
