"""Objetos de valor específicos para el dominio de comisiones

En este archivo se definen los objetos de valor específicos para el dominio de comisiones

"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from ...core.seedwork.objetos_valor import ObjetoValor, Dinero, EstadoComision
from ..affiliates.objetos_valor import TipoEvento

@dataclass(frozen=True)
class ConversionId(ObjetoValor):
    """Objeto de valor que representa el identificador de una conversión"""
    id: UUID

@dataclass(frozen=True)
class ComisionId(ObjetoValor):
    """Objeto de valor que representa el identificador de una comisión"""
    id: UUID

@dataclass(frozen=True)
class MetadatosEvento(ObjetoValor):
    """Objeto de valor que representa los metadatos de un evento de conversión"""
    datos: Dict[str, Any]
    
    def obtener(self, clave: str, por_defecto: Any = None) -> Any:
        """Obtiene un valor de los metadatos"""
        return self.datos.get(clave, por_defecto)

@dataclass(frozen=True)
class FechaOcurrencia(ObjetoValor):
    """Objeto de valor que representa la fecha y hora de ocurrencia de un evento"""
    timestamp: datetime
    
    def es_anterior_a(self, otra_fecha: 'FechaOcurrencia') -> bool:
        """Verifica si esta fecha es anterior a otra"""
        return self.timestamp < otra_fecha.timestamp
    
    def diferencia_en_dias(self, otra_fecha: 'FechaOcurrencia') -> int:
        """Calcula la diferencia en días con otra fecha"""
        return (otra_fecha.timestamp - self.timestamp).days

@dataclass(frozen=True)
class RangoFechas(ObjetoValor):
    """Objeto de valor que representa un rango de fechas"""
    inicio: datetime
    fin: datetime
    
    def __post_init__(self):
        if self.inicio > self.fin:
            raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")
    
    def contiene(self, fecha: datetime) -> bool:
        """Verifica si una fecha está dentro del rango"""
        return self.inicio <= fecha <= self.fin
    
    def duracion_en_dias(self) -> int:
        """Calcula la duración del rango en días"""
        return (self.fin - self.inicio).days

@dataclass(frozen=True)
class CalculoComision(ObjetoValor):
    """Objeto de valor que representa el cálculo de una comisión"""
    monto_base: Dinero
    tasa_porcentaje: float
    monto_comision: Dinero
    
    def __post_init__(self):
        # Verificar que el cálculo sea correcto
        esperado = self.monto_base.monto * (self.tasa_porcentaje / 100)
        if abs(self.monto_comision.monto - esperado) > 0.01:  # Tolerancia para decimales
            raise ValueError("El cálculo de la comisión es incorrecto")
    
    @classmethod
    def calcular(cls, monto_base: Dinero, tasa: float) -> 'CalculoComision':
        """Factory method para crear un cálculo de comisión"""
        comision = monto_base.monto * (tasa / 100)
        monto_comision = Dinero(monto=comision, moneda=monto_base.moneda)
        return cls(monto_base=monto_base, tasa_porcentaje=tasa, monto_comision=monto_comision)

@dataclass(frozen=True)
class ConfiguracionComision(ObjetoValor):
    """Objeto de valor que representa la configuración de cálculo de comisiones"""
    tasa_base: float
    tasa_minima: Optional[float] = None
    tasa_maxima: Optional[float] = None
    requiere_aprobacion: bool = False
    
    def __post_init__(self):
        if self.tasa_base < 0 or self.tasa_base > 100:
            raise ValueError("La tasa base debe estar entre 0 y 100")
        if self.tasa_minima and (self.tasa_minima < 0 or self.tasa_minima > self.tasa_base):
            raise ValueError("La tasa mínima debe ser menor o igual a la tasa base")
        if self.tasa_maxima and (self.tasa_maxima > 100 or self.tasa_maxima < self.tasa_base):
            raise ValueError("La tasa máxima debe ser mayor o igual a la tasa base")
    
    def es_tasa_valida(self, tasa: float) -> bool:
        """Verifica si una tasa está dentro de los límites configurados"""
        if self.tasa_minima and tasa < self.tasa_minima:
            return False
        if self.tasa_maxima and tasa > self.tasa_maxima:
            return False
        return True