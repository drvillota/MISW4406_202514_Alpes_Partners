"""Agregado de Afiliado

En este archivo se define el agregado raíz de Afiliado con sus invariantes de negocio

"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from ...core.seedwork.agregados import AgregadoRaiz, ReglaNegocio
from .objetos_valor import NombreAfiliado, TasaComision, AfiliadoId, ContactoAfiliado, MetricaAfiliado
from .eventos import AfiliadoCreado, AfiliadoActivado, AfiliadoDesactivado, TasaComisionActualizada

class AfiliadoDebeEstarActivo(ReglaNegocio):
    def __init__(self, activo: bool):
        self.activo = activo
    
    def es_valida(self) -> bool:
        return self.activo
    
    def mensaje_error(self) -> str:
        return "El afiliado debe estar activo para realizar operaciones"

class TasaComisionDebeSerValida(ReglaNegocio):
    def __init__(self, tasa: TasaComision):
        self.tasa = tasa
    
    def es_valida(self) -> bool:
        return 0 <= self.tasa.tasa.valor <= 50  # Máximo 50% de comisión
    
    def mensaje_error(self) -> str:
        return "La tasa de comisión debe estar entre 0% y 50%"

class AfiliadoDebeSerUnico(ReglaNegocio):
    def __init__(self, nombre: NombreAfiliado, existe: bool = False):
        self.nombre = nombre
        self.existe = existe
    
    def es_valida(self) -> bool:
        return not self.existe
    
    def mensaje_error(self) -> str:
        return f"Ya existe un afiliado con el nombre: {self.nombre.nombre}"

@dataclass
class Afiliado(AgregadoRaiz):
    """Agregado raíz que representa un afiliado del programa"""
    nombre: Optional[NombreAfiliado] = None
    tasa_comision: Optional[TasaComision] = None
    fecha_registro: Optional[datetime] = None
    contacto: Optional[ContactoAfiliado] = None
    metricas: Optional[MetricaAfiliado] = None
    activo: bool = True
    
    def __post_init__(self):
        """Post inicialización para validar invariantes"""
        # Validar campos requeridos
        if not self.nombre:
            raise ValueError("nombre es requerido")
        if not self.tasa_comision:
            raise ValueError("tasa_comision es requerido")
            
        if not self.fecha_registro:
            self.fecha_registro = datetime.now()
        if not self.metricas:
            self.metricas = MetricaAfiliado()
        
        self.validar_invariantes()
        
        # Si es una nueva creación, agregar evento
        if not hasattr(self, '_evento_creacion_emitido'):
            self.agregar_evento(AfiliadoCreado(
                affiliate_id=self.id,
                nombre=self.nombre.nombre,
                tasa_comision=self.tasa_comision.tasa.valor,
                fecha_registro=self.fecha_registro
            ))
            self._evento_creacion_emitido = True
    
    def obtener_invariantes(self) -> List[ReglaNegocio]:
        """Retorna las reglas invariantes del agregado Afiliado"""
        return [
            TasaComisionDebeSerValida(self.tasa_comision)
        ]
    
    def cambiar_tasa_comision(self, nueva_tasa: TasaComision) -> None:
        """Cambia la tasa de comisión del afiliado"""
        # Validar reglas de negocio
        self.validar_reglas([
            AfiliadoDebeEstarActivo(self.activo),
            TasaComisionDebeSerValida(nueva_tasa)
        ])
        
        tasa_anterior = self.tasa_comision
        self.tasa_comision = nueva_tasa
        self.incrementar_version()
        
        # Emitir evento
        self.agregar_evento(TasaComisionActualizada(
            affiliate_id=self.id,
            tasa_anterior=tasa_anterior.tasa.valor,
            nueva_tasa=nueva_tasa.tasa.valor,
            fecha_cambio=datetime.now()
        ))
    
    def activar(self) -> None:
        """Activa el afiliado"""
        if self.activo:
            return  # Ya está activo
        
        self.activo = True
        self.incrementar_version()
        
        self.agregar_evento(AfiliadoActivado(
            affiliate_id=self.id,
            fecha_activacion=datetime.now()
        ))
    
    def desactivar(self, motivo: Optional[str] = None) -> None:
        """Desactiva el afiliado"""
        if not self.activo:
            return  # Ya está desactivado
        
        self.activo = False
        self.incrementar_version()
        
        self.agregar_evento(AfiliadoDesactivado(
            affiliate_id=self.id,
            motivo=motivo or "Desactivación manual",
            fecha_desactivacion=datetime.now()
        ))
    
    def actualizar_contacto(self, contacto: ContactoAfiliado) -> None:
        """Actualiza la información de contacto"""
        self.validar_reglas([AfiliadoDebeEstarActivo(self.activo)])
        
        self.contacto = contacto
        self.incrementar_version()
    
    def puede_generar_comisiones(self) -> bool:
        """Verifica si el afiliado puede generar comisiones"""
        return self.activo and self.tasa_comision.tasa.valor > 0
    
    def calcular_comision_para_monto(self, monto: float) -> float:
        """Calcula la comisión para un monto específico"""
        if not self.puede_generar_comisiones():
            return 0.0
        
        return self.tasa_comision.calcular_comision(monto)
    
    def actualizar_metricas(self, metricas: MetricaAfiliado) -> None:
        """Actualiza las métricas del afiliado"""
        self.metricas = metricas
        self.actualizar_timestamp()