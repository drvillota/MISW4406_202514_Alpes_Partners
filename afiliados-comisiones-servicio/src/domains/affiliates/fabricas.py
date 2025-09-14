"""Fábricas para el dominio de afiliados

En este archivo se definen las fábricas para crear agregados y entidades del dominio de afiliados

"""

from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
from ...core.seedwork.fabricas import Fabrica
from ...core.seedwork.objetos_valor import Email, Porcentaje
from .agregados import Afiliado
from .objetos_valor import NombreAfiliado, TasaComision, ContactoAfiliado, MetricaAfiliado

class FabricaAfiliado(Fabrica):
    """Fábrica para crear agregados de Afiliado"""
    
    def crear(self, datos: Dict[str, Any]) -> Afiliado:
        """Crea un agregado Afiliado a partir de los datos proporcionados"""
        campos_requeridos = ['nombre', 'tasa_comision']
        self.validar_datos_requeridos(datos, campos_requeridos)
        
        # Crear objetos de valor
        nombre = NombreAfiliado(datos['nombre'])
        tasa = TasaComision(Porcentaje(datos['tasa_comision']))
        
        # Crear contacto si se proporciona
        contacto = None
        if 'email' in datos or 'telefono' in datos:
            email = Email(datos['email']) if datos.get('email') else None
            telefono = datos.get('telefono')
            contacto = ContactoAfiliado(email=email, telefono=telefono)
        
        # Crear métricas iniciales
        metricas = MetricaAfiliado(
            total_conversiones=datos.get('total_conversiones', 0),
            total_comisiones_pagadas=datos.get('total_comisiones_pagadas', 0.0),
            total_comisiones_pendientes=datos.get('total_comisiones_pendientes', 0.0)
        )
        
        # Crear el agregado
        afiliado = Afiliado(
            id=datos.get('id', uuid4()),
            nombre=nombre,
            tasa_comision=tasa,
            contacto=contacto,
            metricas=metricas,
            activo=datos.get('activo', True),
            fecha_registro=datos.get('fecha_registro', datetime.now())
        )
        
        return afiliado
    
    def crear_afiliado_basico(self, nombre: str, tasa_comision: float, email: Optional[str] = None) -> Afiliado:
        """Método de conveniencia para crear un afiliado básico"""
        datos = {
            'nombre': nombre,
            'tasa_comision': tasa_comision
        }
        
        if email:
            datos['email'] = email
        
        return self.crear(datos)
    
    def crear_desde_entidad_legado(self, entidad_legado: Any) -> Afiliado:
        """Crea un Afiliado desde una entidad del sistema legado"""
        # Mapear campos de la entidad legado
        datos = {
            'id': getattr(entidad_legado, 'id', uuid4()),
            'nombre': getattr(entidad_legado, 'nombre', 'Sin Nombre'),
            'tasa_comision': getattr(entidad_legado, 'tasa_comision', 0.0),
            'activo': getattr(entidad_legado, 'activo', True),
            'fecha_registro': getattr(entidad_legado, 'fecha_creacion', datetime.now())
        }
        
        return self.crear(datos)