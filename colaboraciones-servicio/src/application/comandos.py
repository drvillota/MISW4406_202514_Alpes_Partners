"""Comandos CQS para el microservicio de Colaboraciones"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID
from typing import Optional
from core.seedworks.comandos import Comando


# -------------------------------
# COMANDOS: Colaboraciones
# -------------------------------

@dataclass
class IniciarColaboracionComando(Comando):
    """Comando: Crear una nueva colaboración usando un contrato existente"""
    colaboracion_id: UUID
    campania_id: UUID
    influencer_id: UUID
    contrato_id: UUID   # 🔑 ahora obligatorio, ya debe existir en BD


@dataclass
class FirmarContratoComando(Comando):
    """Comando: Firmar un contrato existente en una colaboración"""
    contrato_id: UUID
    colaboracion_id: UUID


@dataclass
class CancelarContratoComando(Comando):
    """Comando: Cancelar un contrato existente en una colaboración"""
    contrato_id: UUID
    colaboracion_id: UUID
    motivo: Optional[str] = None


@dataclass
class FinalizarColaboracionComando(Comando):
    """Comando: Marcar una colaboración como finalizada"""
    colaboracion_id: UUID


# -------------------------------
# COMANDOS: Publicaciones
# -------------------------------

@dataclass
class RegistrarPublicacionComando(Comando):
    """Comando: Registrar una publicación hecha por un influencer en una colaboración"""
    colaboracion_id: UUID
    url: str
    red: str
    fecha: date
