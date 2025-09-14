"""Agregados del dominio de comisiones

En este archivo se definen los agregados raíz de Conversión y Comisión con sus invariantes

"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from ...core.seedwork.agregados import AgregadoRaiz, ReglaNegocio
from ...core.seedwork.objetos_valor import Dinero, EstadoComision
from .objetos_valor import ConversionId, ComisionId, TipoEvento, MetadatosEvento, FechaOcurrencia, CalculoComision
from .events import ConversionRegistrada, ComisionCreada, ComisionPagada, ComisionCancelada

class ConversionDebeSerValida(ReglaNegocio):
    def __init__(self, monto: Dinero, tipo_evento: TipoEvento):
        self.monto = monto
        self.tipo_evento = tipo_evento
    
    def es_valida(self) -> bool:
        return self.monto.monto > 0
    
    def mensaje_error(self) -> str:
        return "La conversión debe tener un monto mayor a cero"

class ComisionDebeSerPositiva(ReglaNegocio):
    def __init__(self, calculo: CalculoComision):
        self.calculo = calculo
    
    def es_valida(self) -> bool:
        return self.calculo.monto_comision.monto > 0
    
    def mensaje_error(self) -> str:
        return "La comisión calculada debe ser mayor a cero"

class EstadoComisionDebeSerValido(ReglaNegocio):
    def __init__(self, estado_actual: EstadoComision, nuevo_estado: EstadoComision):
        self.estado_actual = estado_actual
        self.nuevo_estado = nuevo_estado
    
    def es_valida(self) -> bool:
        # Definir transiciones válidas de estado
        transiciones_validas = {
            "pendiente": ["pagada", "cancelada"],
            "pagada": [],  # Una vez pagada no puede cambiar
            "cancelada": ["pendiente"]  # Puede reactivarse
        }
        return self.nuevo_estado.valor in transiciones_validas.get(self.estado_actual.valor, [])
    
    def mensaje_error(self) -> str:
        return f"No se puede cambiar el estado de '{self.estado_actual.valor}' a '{self.nuevo_estado.valor}'"

@dataclass
class Conversion(AgregadoRaiz):
    """Agregado raíz que representa una conversión de afiliado"""
    affiliate_id: Optional[UUID] = None
    tipo_evento: Optional[TipoEvento] = None
    monto: Optional[Dinero] = None
    metadatos: Optional[MetadatosEvento] = None
    fecha_ocurrencia: Optional[FechaOcurrencia] = None
    
    def __post_init__(self):
        """Post inicialización para validar invariantes"""
        # Validar campos requeridos
        if not self.affiliate_id:
            raise ValueError("affiliate_id es requerido")
        if not self.tipo_evento:
            raise ValueError("tipo_evento es requerido")  
        if not self.monto:
            raise ValueError("monto es requerido")
            
        if not self.fecha_ocurrencia:
            self.fecha_ocurrencia = FechaOcurrencia(datetime.now())
        if not self.metadatos:
            self.metadatos = MetadatosEvento({})
        
        self.validar_invariantes()
        
        # Emitir evento de conversión registrada
        if not hasattr(self, '_evento_creacion_emitido'):
            self.agregar_evento(ConversionRegistrada(
                affiliate_id=self.affiliate_id,
                event_type=self.tipo_evento.tipo,
                monto=self.monto.monto,
                moneda=self.monto.moneda,
                occurred_at=self.fecha_ocurrencia.timestamp
            ))
            self._evento_creacion_emitido = True
    
    def obtener_invariantes(self) -> List[ReglaNegocio]:
        """Retorna las reglas invariantes del agregado Conversion"""
        return [
            ConversionDebeSerValida(self.monto, self.tipo_evento)
        ]
    
    def es_elegible_para_comision(self) -> bool:
        """Verifica si esta conversión es elegible para generar comisión"""
        # Solo ciertos tipos de evento generan comisiones
        tipos_elegibles = ["sale", "lead", "signup"]
        return self.tipo_evento.tipo in tipos_elegibles and self.monto.monto > 0

@dataclass
class Comision(AgregadoRaiz):
    """Agregado raíz que representa una comisión de afiliado"""
    affiliate_id: Optional[UUID] = None
    conversion_id: Optional[UUID] = None
    calculo: Optional[CalculoComision] = None
    estado: Optional[EstadoComision] = None
    fecha_pago: Optional[datetime] = None
    fecha_cancelacion: Optional[datetime] = None
    observaciones: Optional[str] = None
    
    def __post_init__(self):
        """Post inicialización para validar invariantes"""
        # Validar campos requeridos
        if not self.affiliate_id:
            raise ValueError("affiliate_id es requerido")
        if not self.conversion_id:
            raise ValueError("conversion_id es requerido")
        if not self.calculo:
            raise ValueError("calculo es requerido")
        if not self.estado:
            raise ValueError("estado es requerido")
            
        if not hasattr(self, '_evento_creacion_emitido'):
            self.validar_invariantes()
            
            # Emitir evento de comisión creada
            self.agregar_evento(ComisionCreada(
                commission_id=self.id,
                affiliate_id=self.affiliate_id,
                valor=self.calculo.monto_comision.monto,
                moneda=self.calculo.monto_comision.moneda
            ))
            self._evento_creacion_emitido = True
    
    def obtener_invariantes(self) -> List[ReglaNegocio]:
        """Retorna las reglas invariantes del agregado Comision"""
        return [
            ComisionDebeSerPositiva(self.calculo)
        ]
    
    def marcar_como_pagada(self, fecha_pago: Optional[datetime] = None) -> None:
        """Marca la comisión como pagada"""
        nuevo_estado = EstadoComision("pagada")
        self.validar_reglas([
            EstadoComisionDebeSerValido(self.estado, nuevo_estado)
        ])
        
        self.estado = nuevo_estado
        self.fecha_pago = fecha_pago or datetime.now()
        self.incrementar_version()
        
        self.agregar_evento(ComisionPagada(
            commission_id=self.id,
            affiliate_id=self.affiliate_id,
            valor=self.calculo.monto_comision.monto,
            fecha_pago=self.fecha_pago
        ))
    
    def cancelar(self, motivo: str) -> None:
        """Cancela la comisión"""
        nuevo_estado = EstadoComision("cancelada")
        self.validar_reglas([
            EstadoComisionDebeSerValido(self.estado, nuevo_estado)
        ])
        
        self.estado = nuevo_estado
        self.fecha_cancelacion = datetime.now()
        self.observaciones = motivo
        self.incrementar_version()
        
        self.agregar_evento(ComisionCancelada(
            commission_id=self.id,
            affiliate_id=self.affiliate_id,
            motivo=motivo,
            fecha_cancelacion=self.fecha_cancelacion
        ))
    
    def reactivar(self) -> None:
        """Reactiva una comisión cancelada"""
        if self.estado.valor != "cancelada":
            raise ValueError("Solo se pueden reactivar comisiones canceladas")
        
        nuevo_estado = EstadoComision("pendiente")
        self.estado = nuevo_estado
        self.fecha_cancelacion = None
        self.observaciones = None
        self.incrementar_version()
    
    def esta_pagada(self) -> bool:
        """Verifica si la comisión está pagada"""
        return self.estado.valor == "pagada"
    
    def esta_pendiente(self) -> bool:
        """Verifica si la comisión está pendiente"""
        return self.estado.valor == "pendiente"