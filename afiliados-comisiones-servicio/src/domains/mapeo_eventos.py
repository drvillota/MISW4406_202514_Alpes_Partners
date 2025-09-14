"""Mapeo de Eventos y Agregados

Este archivo documenta la relación entre agregados y los eventos que emiten,
proporcionando trazabilidad de negocio y verificabilidad de invariantes.

"""

from typing import Dict, List, Type
from dataclasses import dataclass
from ..domains.affiliates.agregados import Afiliado
from ..domains.commissions.agregados import Conversion, Comision
from ..domains.affiliates.eventos import (
    AfiliadoCreado, AfiliadoActivado, AfiliadoDesactivado, TasaComisionActualizada
)
from ..domains.commissions.events import (
    ConversionRegistrada, ComisionCreada, ComisionPagada, ComisionCancelada
)

@dataclass
class EventoInfo:
    """Información sobre un evento de dominio"""
    nombre: str
    descripcion: str
    agregado_emisor: str
    condiciones: List[str]
    invariantes_afectadas: List[str]
    casos_uso: List[str]

@dataclass
class AgregadoInfo:
    """Información sobre un agregado"""
    nombre: str
    descripcion: str
    invariantes: List[str]
    eventos_emitidos: List[str]
    reglas_negocio: List[str]

class InventarioDDD:
    """Inventario completo de artefactos DDD con mapeo evento↔agregado"""
    
    # Inventario de Agregados
    AGREGADOS: Dict[str, AgregadoInfo] = {
        'Afiliado': AgregadoInfo(
            nombre='Afiliado',
            descripcion='Agregado raíz que representa un participante del programa de afiliados',
            invariantes=[
                'La tasa de comisión debe estar entre 0% y 50%',
                'El afiliado debe estar activo para realizar operaciones',
                'El nombre del afiliado debe ser único',
                'Al menos un método de contacto debe estar presente'
            ],
            eventos_emitidos=[
                'AfiliadoCreado',
                'AfiliadoActivado', 
                'AfiliadoDesactivado',
                'TasaComisionActualizada'
            ],
            reglas_negocio=[
                'Solo afiliados activos pueden generar comisiones',
                'El cambio de tasa requiere que el afiliado esté activo',
                'La desactivación cancela comisiones pendientes'
            ]
        ),
        
        'Conversion': AgregadoInfo(
            nombre='Conversion',
            descripcion='Agregado que representa una acción de conversión realizada por un afiliado',
            invariantes=[
                'El monto de la conversión debe ser mayor a cero',
                'El tipo de evento debe ser válido',
                'La fecha de ocurrencia no puede ser futura'
            ],
            eventos_emitidos=[
                'ConversionRegistrada'
            ],
            reglas_negocio=[
                'Solo ciertos tipos de evento generan comisiones (sale, lead, signup)',
                'Las conversiones son inmutables una vez creadas',
                'Cada conversión debe estar asociada a un afiliado activo'
            ]
        ),
        
        'Comision': AgregadoInfo(
            nombre='Comision',
            descripcion='Agregado que representa una comisión calculada para un afiliado',
            invariantes=[
                'La comisión calculada debe ser mayor a cero',
                'El estado de la comisión debe permitir transiciones válidas',
                'Una comisión pagada no puede cambiar de estado',
                'El cálculo debe ser correcto según la tasa aplicada'
            ],
            eventos_emitidos=[
                'ComisionCreada',
                'ComisionPagada',
                'ComisionCancelada'
            ],
            reglas_negocio=[
                'Las transiciones de estado están controladas (pendiente→pagada/cancelada)',
                'Una comisión cancelada puede reactivarse',
                'El pago require validación de fondos',
                'Las comisiones manuales requieren justificación'
            ]
        )
    }
    
    # Inventario de Eventos
    EVENTOS: Dict[str, EventoInfo] = {
        'AfiliadoCreado': EventoInfo(
            nombre='AfiliadoCreado',
            descripcion='Se emite cuando se registra un nuevo afiliado en el sistema',
            agregado_emisor='Afiliado',
            condiciones=[
                'Los datos del afiliado son válidos',
                'No existe otro afiliado con el mismo nombre',
                'La tasa de comisión está dentro del rango permitido'
            ],
            invariantes_afectadas=[
                'Unicidad del nombre de afiliado',
                'Validez de la tasa de comisión'
            ],
            casos_uso=[
                'Registro de nuevo afiliado',
                'Onboarding automático',
                'Notificaciones de bienvenida'
            ]
        ),
        
        'AfiliadoActivado': EventoInfo(
            nombre='AfiliadoActivado',
            descripcion='Se emite cuando se activa un afiliado previamente desactivado',
            agregado_emisor='Afiliado',
            condiciones=[
                'El afiliado estaba previamente desactivado',
                'Los datos del afiliado siguen siendo válidos'
            ],
            invariantes_afectadas=[
                'Estado activo del afiliado'
            ],
            casos_uso=[
                'Reactivación de afiliado',
                'Rehabilitación después de suspensión',
                'Notificación de reactivación'
            ]
        ),
        
        'AfiliadoDesactivado': EventoInfo(
            nombre='AfiliadoDesactivado',
            descripcion='Se emite cuando se desactiva un afiliado',
            agregado_emisor='Afiliado',
            condiciones=[
                'El afiliado estaba activo',
                'Se proporciona un motivo de desactivación'
            ],
            invariantes_afectadas=[
                'Estado activo del afiliado',
                'Capacidad de generar comisiones'
            ],
            casos_uso=[
                'Suspensión por incumplimiento',
                'Desactivación voluntaria',
                'Cancelación de comisiones pendientes'
            ]
        ),
        
        'TasaComisionActualizada': EventoInfo(
            nombre='TasaComisionActualizada',
            descripcion='Se emite cuando se modifica la tasa de comisión de un afiliado',
            agregado_emisor='Afiliado',
            condiciones=[
                'El afiliado está activo',
                'La nueva tasa está dentro del rango permitido',
                'La tasa es diferente a la actual'
            ],
            invariantes_afectadas=[
                'Validez de la tasa de comisión',
                'Consistencia histórica de tasas'
            ],
            casos_uso=[
                'Ajuste de tasas por rendimiento',
                'Promociones especiales',
                'Recálculo de comisiones futuras'
            ]
        ),
        
        'ConversionRegistrada': EventoInfo(
            nombre='ConversionRegistrada',
            descripcion='Se emite cuando se registra una nueva conversión de afiliado',
            agregado_emisor='Conversion',
            condiciones=[
                'El afiliado existe y está activo',
                'El monto de conversión es mayor a cero',
                'El tipo de evento es válido'
            ],
            invariantes_afectadas=[
                'Validez del monto de conversión',
                'Asociación con afiliado activo'
            ],
            casos_uso=[
                'Tracking de conversiones',
                'Cálculo de comisiones',
                'Analytics y reportes'
            ]
        ),
        
        'ComisionCreada': EventoInfo(
            nombre='ComisionCreada',
            descripcion='Se emite cuando se crea una nueva comisión para un afiliado',
            agregado_emisor='Comision',
            condiciones=[
                'La conversión es elegible para comisión',
                'El cálculo de comisión es correcto',
                'El afiliado está activo'
            ],
            invariantes_afectadas=[
                'Correctitud del cálculo de comisión',
                'Estado inicial de la comisión'
            ],
            casos_uso=[
                'Generación automática de comisiones',
                'Notificación a afiliados',
                'Registro contable'
            ]
        ),
        
        'ComisionPagada': EventoInfo(
            nombre='ComisionPagada',
            descripcion='Se emite cuando se realiza el pago de una comisión',
            agregado_emisor='Comision',
            condiciones=[
                'La comisión estaba en estado pendiente',
                'Se tiene la autorización de pago',
                'Los fondos están disponibles'
            ],
            invariantes_afectadas=[
                'Estado de la comisión',
                'Inmutabilidad después del pago'
            ],
            casos_uso=[
                'Procesamiento de pagos',
                'Actualización de balances',
                'Notificaciones de pago'
            ]
        ),
        
        'ComisionCancelada': EventoInfo(
            nombre='ComisionCancelada',
            descripcion='Se emite cuando se cancela una comisión',
            agregado_emisor='Comision',
            condiciones=[
                'La comisión no está pagada',
                'Se proporciona un motivo de cancelación',
                'Se tiene autorización para cancelar'
            ],
            invariantes_afectadas=[
                'Estado de la comisión',
                'Posibilidad de reactivación'
            ],
            casos_uso=[
                'Reversión por fraude',
                'Cancelación por política',
                'Corrección de errores'
            ]
        )
    }
    
    # Mapeo Evento → Agregado
    EVENTO_A_AGREGADO: Dict[str, str] = {
        'AfiliadoCreado': 'Afiliado',
        'AfiliadoActivado': 'Afiliado',
        'AfiliadoDesactivado': 'Afiliado',
        'TasaComisionActualizada': 'Afiliado',
        'ConversionRegistrada': 'Conversion',
        'ComisionCreada': 'Comision',
        'ComisionPagada': 'Comision',
        'ComisionCancelada': 'Comision'
    }
    
    # Mapeo Agregado → Eventos
    AGREGADO_A_EVENTOS: Dict[str, List[str]] = {
        'Afiliado': ['AfiliadoCreado', 'AfiliadoActivado', 'AfiliadoDesactivado', 'TasaComisionActualizada'],
        'Conversion': ['ConversionRegistrada'],
        'Comision': ['ComisionCreada', 'ComisionPagada', 'ComisionCancelada']
    }
    
    @classmethod
    def obtener_eventos_por_agregado(cls, agregado: str) -> List[str]:
        """Obtiene los eventos que emite un agregado específico"""
        return cls.AGREGADO_A_EVENTOS.get(agregado, [])
    
    @classmethod
    def obtener_agregado_por_evento(cls, evento: str) -> str:
        """Obtiene el agregado que emite un evento específico"""
        return cls.EVENTO_A_AGREGADO.get(evento, 'Desconocido')
    
    @classmethod
    def obtener_info_evento(cls, evento: str) -> EventoInfo:
        """Obtiene información detallada de un evento"""
        return cls.EVENTOS.get(evento)
    
    @classmethod
    def obtener_info_agregado(cls, agregado: str) -> AgregadoInfo:
        """Obtiene información detallada de un agregado"""
        return cls.AGREGADOS.get(agregado)
    
    @classmethod
    def generar_matriz_trazabilidad(cls) -> Dict[str, Dict[str, List[str]]]:
        """Genera una matriz de trazabilidad para verificación de invariantes"""
        matriz = {}
        
        for agregado, info in cls.AGREGADOS.items():
            eventos_del_agregado = cls.obtener_eventos_por_agregado(agregado)
            matriz[agregado] = {
                'invariantes': info.invariantes,
                'eventos': eventos_del_agregado,
                'reglas_negocio': info.reglas_negocio
            }
        
        return matriz
    
    @classmethod
    def validar_consistencia(cls) -> List[str]:
        """Valida la consistencia del mapeo evento↔agregado"""
        errores = []
        
        # Verificar que todos los eventos tengan un agregado emisor
        for evento in cls.EVENTOS.keys():
            if evento not in cls.EVENTO_A_AGREGADO:
                errores.append(f"Evento {evento} no tiene agregado emisor definido")
        
        # Verificar que todos los agregados existan
        for agregado in cls.EVENTO_A_AGREGADO.values():
            if agregado not in cls.AGREGADOS:
                errores.append(f"Agregado {agregado} no está definido en el inventario")
        
        # Verificar consistencia bidireccional
        for agregado, eventos in cls.AGREGADO_A_EVENTOS.items():
            for evento in eventos:
                if cls.EVENTO_A_AGREGADO.get(evento) != agregado:
                    errores.append(f"Inconsistencia: evento {evento} mapeado a agregado {agregado}")
        
        return errores