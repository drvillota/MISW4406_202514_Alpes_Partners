"""Modelos SQLAlchemy para colaboraciones"""

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
from uuid import uuid4
from infrastructure.database.connection import Base


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
    __tablename__ = "contratos"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")

    colaboracion = relationship("ColaboracionModel", back_populates="contrato", uselist=False)

class ColaboracionModel(Base):
    __tablename__ = "colaboraciones"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    campania_id = mapped_column(UUID(as_uuid=True), ForeignKey("campanias.id"), nullable=False)
    influencer_id = mapped_column(UUID(as_uuid=True), ForeignKey("influencers.id"), nullable=False)
    contrato_id = mapped_column(UUID(as_uuid=True), ForeignKey("contratos.id"), nullable=False)
    estado = mapped_column(String(20), nullable=False, default="VIGENTE")
    created_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    publicaciones = mapped_column(JSON, nullable=False, default=list)

    campania = relationship("CampaniaModel", back_populates="colaboraciones")
    influencer = relationship("InfluencerModel", back_populates="colaboraciones")
    contrato = relationship("ContratoModel", back_populates="colaboracion", uselist=False)
