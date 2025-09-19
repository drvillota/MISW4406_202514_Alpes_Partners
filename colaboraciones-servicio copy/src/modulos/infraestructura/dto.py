# src/colaboraciones/modulos/infraestructura/dto.py
from sqlalchemy import Column, String, DateTime, Text
from config.db import Base
import datetime

class Colaboracion(Base):
    __tablename__ = "colaboraciones"

    id = Column(String(36), primary_key=True)
    id_campania = Column(String(100), nullable=False)
    id_influencer = Column(String(100), nullable=False)
    contrato_url = Column(Text, nullable=True)
    estado = Column(String(50), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)


class EventoColaboracion(Base):
    __tablename__ = "eventos_colaboracion"

    id = Column(String(36), primary_key=True)
    id_entidad = Column(String(36), nullable=False)
    fecha_evento = Column(DateTime, default=datetime.datetime.utcnow)
    version = Column(String(50))
    tipo_evento = Column(String(100))
    formato_contenido = Column(String(50))
    nombre_servicio = Column(String(100))
    contenido = Column(Text)
