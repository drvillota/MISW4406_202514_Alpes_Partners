"""Agregados base del seedwork

En este archivo se definen los agregados base reutilizables

"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from abc import ABC, abstractmethod
from typing import List
from .events import DomainEvent

class ReglaNegocio(ABC):
    """Clase base para reglas de negocio"""
    
    @abstractmethod
    def es_valida(self) -> bool:
        pass
    
    @abstractmethod
    def mensaje_error(self) -> str:
        pass

class ValidacionReglas:
    """Mixin para validación de reglas de negocio"""
    
    def validar_reglas(self, reglas: List[ReglaNegocio]) -> None:
        """Valida una lista de reglas de negocio"""
        for regla in reglas:
            if not regla.es_valida():
                raise ValueError(regla.mensaje_error())

@dataclass
class Entidad:
    """Clase base para todas las entidades"""
    id: UUID = field(default_factory=uuid4)
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
    
    def actualizar_timestamp(self):
        """Actualiza la fecha de modificación"""
        self.fecha_actualizacion = datetime.now()

@dataclass 
class AgregadoRaiz(Entidad, ValidacionReglas):
    """Clase base para todos los agregados raíz"""
    eventos: List[DomainEvent] = field(default_factory=list, init=False, repr=False)
    version: int = field(default=1, init=False, repr=False)
    
    def agregar_evento(self, evento: DomainEvent) -> None:
        """Agrega un evento de dominio al agregado"""
        self.eventos.append(evento)
        
    def limpiar_eventos(self) -> List[DomainEvent]:
        """Limpia y retorna los eventos del agregado"""
        eventos = self.eventos.copy()
        self.eventos.clear()
        return eventos
    
    def incrementar_version(self) -> None:
        """Incrementa la versión del agregado"""
        self.version += 1
        self.actualizar_timestamp()
    
    @abstractmethod
    def obtener_invariantes(self) -> List[ReglaNegocio]:
        """Retorna las reglas invariantes del agregado"""
        pass
    
    def validar_invariantes(self) -> None:
        """Valida todas las reglas invariantes del agregado"""
        invariantes = self.obtener_invariantes()
        self.validar_reglas(invariantes)