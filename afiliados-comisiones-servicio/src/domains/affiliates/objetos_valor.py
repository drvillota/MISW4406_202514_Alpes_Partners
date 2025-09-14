"""Objetos de valor específicos para el dominio de afiliados

En este archivo se definen los objetos de valor específicos para el dominio de afiliados

"""

from dataclasses import dataclass
from typing import Optional
from ...core.seedwork.objetos_valor import ObjetoValor, Identificador, Porcentaje, Email

@dataclass(frozen=True)
class NombreAfiliado(ObjetoValor):
    """Objeto de valor que representa el nombre de un afiliado"""
    nombre: str
    
    def __post_init__(self):
        if not self.nombre or len(self.nombre.strip()) == 0:
            raise ValueError("El nombre del afiliado no puede estar vacío")
        if len(self.nombre.strip()) < 3:
            raise ValueError("El nombre del afiliado debe tener al menos 3 caracteres")

@dataclass(frozen=True)
class TasaComision(ObjetoValor):
    """Objeto de valor que representa la tasa de comisión de un afiliado"""
    tasa: Porcentaje
    
    def calcular_comision(self, monto: float) -> float:
        """Calcula el valor de la comisión para un monto dado"""
        return monto * (self.tasa.valor / 100)

@dataclass(frozen=True)
class AfiliadoId(ObjetoValor):
    """Objeto de valor que representa el identificador de un afiliado"""
    id: str
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("El ID del afiliado es requerido")

@dataclass(frozen=True)
class TipoEvento(ObjetoValor):
    """Objeto de valor que representa el tipo de evento de conversión"""
    tipo: str
    
    def __post_init__(self):
        tipos_validos = ["click", "lead", "sale", "signup", "view"]
        if self.tipo not in tipos_validos:
            raise ValueError(f"El tipo de evento debe ser uno de: {tipos_validos}")

@dataclass(frozen=True)
class ContactoAfiliado(ObjetoValor):
    """Objeto de valor que representa la información de contacto de un afiliado"""
    email: Optional[Email] = None
    telefono: Optional[str] = None
    
    def __post_init__(self):
        if not self.email and not self.telefono:
            raise ValueError("Al menos un método de contacto es requerido")

@dataclass(frozen=True)
class MetricaAfiliado(ObjetoValor):
    """Objeto de valor que representa métricas de un afiliado"""
    total_conversiones: int = 0
    total_comisiones_pagadas: float = 0.0
    total_comisiones_pendientes: float = 0.0
    
    def __post_init__(self):
        if any(valor < 0 for valor in [self.total_conversiones, self.total_comisiones_pagadas, self.total_comisiones_pendientes]):
            raise ValueError("Las métricas no pueden ser negativas")