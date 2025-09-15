"""Objetos valor base del seedwork

En este archivo se definen los objetos valor base reutilizables

"""

from dataclasses import dataclass
from abc import ABC
from typing import Any

@dataclass(frozen=True)
class ObjetoValor:
    """Clase base para todos los objetos de valor"""
    ...

@dataclass(frozen=True) 
class Identificador(ObjetoValor):
    """Objeto de valor para representar identificadores"""
    valor: str

@dataclass(frozen=True)
class Dinero(ObjetoValor):
    """Objeto de valor para representar cantidades monetarias"""
    monto: float
    moneda: str
    
    def __post_init__(self):
        if self.monto < 0:
            raise ValueError("El monto no puede ser negativo")
        if not self.moneda or len(self.moneda.strip()) == 0:
            raise ValueError("La moneda es requerida")
        if len(self.moneda) != 3:
            raise ValueError("La moneda debe ser un código de 3 caracteres (ISO 4217)")

@dataclass(frozen=True)
class Porcentaje(ObjetoValor):
    """Objeto de valor para representar porcentajes"""
    valor: float
    
    def __post_init__(self):
        if self.valor < 0 or self.valor > 100:
            raise ValueError("El porcentaje debe estar entre 0 y 100")

@dataclass(frozen=True)
class Email(ObjetoValor):
    """Objeto de valor para representar direcciones de email"""
    direccion: str
    
    def __post_init__(self):
        if "@" not in self.direccion:
            raise ValueError("Email debe contener @")

@dataclass(frozen=True)
class EstadoComision(ObjetoValor):
    """Objeto de valor para representar estados de comisión"""
    valor: str
    
    def __post_init__(self):
        estados_validos = ["pendiente", "pagada", "cancelada"]
        if self.valor not in estados_validos:
            raise ValueError(f"Estado debe ser uno de: {estados_validos}")