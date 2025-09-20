"""Fábricas base del seedwork

En este archivo se definen las fábricas base reutilizables

"""

from abc import ABC, abstractmethod
from typing import Any, Dict
 
class Fabrica(ABC):
    """Clase base para todas las fábricas"""
    
    @abstractmethod
    def crear(self, datos: Dict[str, Any]) -> Any:
        """Crea un objeto a partir de los datos proporcionados"""
        pass
    
    def validar_datos_requeridos(self, datos: Dict[str, Any], campos_requeridos: list) -> None:
        """Valida que todos los campos requeridos estén presentes"""
        for campo in campos_requeridos:
            if campo not in datos:
                raise ValueError(f"El campo '{campo}' es requerido para crear el objeto")
            if datos[campo] is None:
                raise ValueError(f"El campo '{campo}' no puede ser None")