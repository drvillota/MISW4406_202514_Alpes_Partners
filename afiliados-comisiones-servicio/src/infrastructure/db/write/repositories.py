"""Repositorios de comandos - optimizados para escritura

En este archivo se definen los repositorios optimizados para comandos/escritura

"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..write.models import AfiliadoWrite, ConversionWrite, ComisionWrite, OutboxEvent
from ...domains.affiliates.repository import AfiliadoRepository as IAfiliadoRepository
from ...domains.commissions.repository import ConversionRepository as IConversionRepository
from ...domains.commissions.repository import ComisionRepository as IComisionRepository

class AfiliadoCommandRepository(IAfiliadoRepository):
    """Repositorio de comandos para Afiliado - optimizado para escritura"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, afiliado) -> None:
        """Agrega un nuevo afiliado"""
        afiliado_model = AfiliadoWrite(
            id=afiliado.id,
            nombre=afiliado.nombre.nombre,
            tasa_comision=afiliado.tasa_comision.tasa.valor,
            email=afiliado.contacto.email.direccion if afiliado.contacto and afiliado.contacto.email else None,
            telefono=afiliado.contacto.telefono if afiliado.contacto else None,
            activo=afiliado.activo,
            fecha_registro=afiliado.fecha_registro,
            version=afiliado.version
        )
        
        self.session.add(afiliado_model)
        self._save_events_to_outbox(afiliado)
    
    def get_by_id(self, affiliate_id: UUID):
        """Obtiene un afiliado por ID para comandos"""
        afiliado_model = self.session.query(AfiliadoWrite).filter(
            AfiliadoWrite.id == affiliate_id
        ).first()
        
        if not afiliado_model:
            return None
        
        # Reconstruir el agregado desde el modelo
        return self._to_aggregate(afiliado_model)
    
    def update(self, afiliado) -> None:
        """Actualiza un afiliado existente"""
        afiliado_model = self.session.query(AfiliadoWrite).filter(
            and_(AfiliadoWrite.id == afiliado.id, AfiliadoWrite.version == afiliado.version - 1)
        ).first()
        
        if not afiliado_model:
            raise ValueError(f"Afiliado {afiliado.id} no encontrado o conflicto de concurrencia")
        
        # Actualizar campos
        afiliado_model.nombre = afiliado.nombre.nombre
        afiliado_model.tasa_comision = afiliado.tasa_comision.tasa.valor
        afiliado_model.activo = afiliado.activo
        afiliado_model.version = afiliado.version
        
        if afiliado.contacto:
            afiliado_model.email = afiliado.contacto.email.direccion if afiliado.contacto.email else None
            afiliado_model.telefono = afiliado.contacto.telefono
        
        self._save_events_to_outbox(afiliado)
    
    def delete(self, affiliate_id: UUID) -> None:
        """Elimina un afiliado (soft delete)"""
        afiliado_model = self.session.query(AfiliadoWrite).filter(
            AfiliadoWrite.id == affiliate_id
        ).first()
        
        if afiliado_model:
            afiliado_model.activo = False
    
    def _save_events_to_outbox(self, afiliado) -> None:
        """Guarda los eventos del agregado en la tabla outbox"""
        for event in afiliado.eventos:
            outbox_event = OutboxEvent(
                aggregate_id=afiliado.id,
                aggregate_type='Afiliado',
                event_type=event.name,
                event_data=self._serialize_event(event)
            )
            self.session.add(outbox_event)
    
    def _serialize_event(self, event) -> str:
        """Serializa un evento a JSON"""
        import json
        return json.dumps(event.__dict__, default=str)
    
    def _to_aggregate(self, model):
        """Convierte un modelo de BD al agregado de dominio"""
        # Aquí iría la lógica de reconstrucción del agregado
        # Por brevedad, se omite la implementación completa
        pass

class ConversionCommandRepository(IConversionRepository):
    """Repositorio de comandos para Conversion - optimizado para escritura"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, conversion) -> None:
        """Agrega una nueva conversión"""
        conversion_model = ConversionWrite(
            id=conversion.id,
            affiliate_id=conversion.affiliate_id,
            event_type=conversion.tipo_evento.tipo,
            monto=conversion.monto.monto,
            moneda=conversion.monto.moneda,
            metadatos=self._serialize_metadata(conversion.metadatos),
            occurred_at=conversion.fecha_ocurrencia.timestamp,
            version=conversion.version
        )
        
        self.session.add(conversion_model)
        self._save_events_to_outbox(conversion)
    
    def get_by_id(self, conversion_id: UUID):
        """Obtiene una conversión por ID"""
        conversion_model = self.session.query(ConversionWrite).filter(
            ConversionWrite.id == conversion_id
        ).first()
        
        if not conversion_model:
            return None
        
        return self._to_aggregate(conversion_model)
    
    def list_by_affiliate(self, affiliate_id: UUID, limit: int = 100):
        """Lista conversiones por afiliado"""
        conversions = self.session.query(ConversionWrite).filter(
            ConversionWrite.affiliate_id == affiliate_id
        ).limit(limit).all()
        
        return [self._to_aggregate(c) for c in conversions]
    
    def _serialize_metadata(self, metadatos):
        """Serializa metadatos a JSON"""
        if not metadatos:
            return None
        import json
        return json.dumps(metadatos.datos)
    
    def _save_events_to_outbox(self, conversion) -> None:
        """Guarda los eventos del agregado en la tabla outbox"""
        for event in conversion.eventos:
            outbox_event = OutboxEvent(
                aggregate_id=conversion.id,
                aggregate_type='Conversion',
                event_type=event.name,
                event_data=self._serialize_event(event)
            )
            self.session.add(outbox_event)
    
    def _serialize_event(self, event) -> str:
        """Serializa un evento a JSON"""
        import json
        return json.dumps(event.__dict__, default=str)
    
    def _to_aggregate(self, model):
        """Convierte un modelo de BD al agregado de dominio"""
        # Implementación de reconstrucción del agregado
        pass

class ComisionCommandRepository(IComisionRepository):
    """Repositorio de comandos para Comision - optimizado para escritura"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, comision) -> None:
        """Agrega una nueva comisión"""
        comision_model = ComisionWrite(
            id=comision.id,
            affiliate_id=comision.affiliate_id,
            conversion_id=comision.conversion_id,
            monto_base=comision.calculo.monto_base.monto,
            tasa_comision=comision.calculo.tasa_porcentaje,
            valor_comision=comision.calculo.monto_comision.monto,
            moneda=comision.calculo.monto_comision.moneda,
            estado=comision.estado.valor,
            fecha_pago=comision.fecha_pago,
            fecha_cancelacion=comision.fecha_cancelacion,
            observaciones=comision.observaciones,
            version=comision.version
        )
        
        self.session.add(comision_model)
        self._save_events_to_outbox(comision)
    
    def get_by_id(self, commission_id: UUID):
        """Obtiene una comisión por ID"""
        comision_model = self.session.query(ComisionWrite).filter(
            ComisionWrite.id == commission_id
        ).first()
        
        if not comision_model:
            return None
        
        return self._to_aggregate(comision_model)
    
    def update(self, comision) -> None:
        """Actualiza una comisión existente"""
        comision_model = self.session.query(ComisionWrite).filter(
            and_(ComisionWrite.id == comision.id, ComisionWrite.version == comision.version - 1)
        ).first()
        
        if not comision_model:
            raise ValueError(f"Comisión {comision.id} no encontrada o conflicto de concurrencia")
        
        # Actualizar campos
        comision_model.estado = comision.estado.valor
        comision_model.fecha_pago = comision.fecha_pago
        comision_model.fecha_cancelacion = comision.fecha_cancelacion
        comision_model.observaciones = comision.observaciones
        comision_model.version = comision.version
        
        self._save_events_to_outbox(comision)
    
    def list_by_affiliate(self, affiliate_id: UUID, desde: str = None, hasta: str = None):
        """Lista comisiones por afiliado con filtros de fecha"""
        query = self.session.query(ComisionWrite).filter(
            ComisionWrite.affiliate_id == affiliate_id
        )
        
        if desde:
            from datetime import datetime
            query = query.filter(ComisionWrite.fecha_creacion >= datetime.fromisoformat(desde))
        
        if hasta:
            from datetime import datetime
            query = query.filter(ComisionWrite.fecha_creacion <= datetime.fromisoformat(hasta))
        
        comisiones = query.all()
        return [self._to_aggregate(c) for c in comisiones]
    
    def _save_events_to_outbox(self, comision) -> None:
        """Guarda los eventos del agregado en la tabla outbox"""
        for event in comision.eventos:
            outbox_event = OutboxEvent(
                aggregate_id=comision.id,
                aggregate_type='Comision',
                event_type=event.name,
                event_data=self._serialize_event(event)
            )
            self.session.add(outbox_event)
    
    def _serialize_event(self, event) -> str:
        """Serializa un evento a JSON"""
        import json
        return json.dumps(event.__dict__, default=str)
    
    def _to_aggregate(self, model):
        """Convierte un modelo de BD al agregado de dominio"""
        # Implementación de reconstrucción del agregado
        pass