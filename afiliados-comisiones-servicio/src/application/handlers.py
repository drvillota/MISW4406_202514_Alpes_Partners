"""Handlers simplificados para comandos y consultas usando servicios de dominio"""

from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .commands import (
    RegisterAffiliateCommand,
    ActivateAffiliateCommand,
    DeactivateAffiliateCommand,
    ProcessConversionCommand,
    RegistrarConversionCommand,
    GetAffiliateQuery,
    ListCommissionsQuery,
    ListAffiliatesQuery,
    ConsultarComisionesPorAfiliadoQuery
)
from .services import AffiliateService, ConversionService
from ..domain.entities import Affiliate, Commission, ConversionEvent

class CommandHandler:
    """Handler unificado para comandos (escritura)"""
    
    def __init__(self, session: Session):
        self.session = session
        self.affiliate_service = AffiliateService(session)
        self.conversion_service = ConversionService(session)
    
    def handle_register_affiliate(self, command: RegisterAffiliateCommand) -> str:
        """Registrar nuevo afiliado"""
        try:
            affiliate = self.affiliate_service.register_affiliate(
                name=command.name,
                email=command.email,
                commission_rate=command.commission_rate
            )
            return str(affiliate.id)
        except Exception:
            self.session.rollback()
            raise
    
    def handle_activate_affiliate(self, command: ActivateAffiliateCommand) -> None:
        """Activar afiliado"""
        try:
            self.affiliate_service.activate_affiliate(command.affiliate_id)
        except Exception:
            self.session.rollback()
            raise
    
    def handle_deactivate_affiliate(self, command: DeactivateAffiliateCommand) -> None:
        """Desactivar afiliado"""
        try:
            self.affiliate_service.deactivate_affiliate(command.affiliate_id)
        except Exception:
            self.session.rollback()
            raise
    
    def handle_process_conversion(self, command: ProcessConversionCommand) -> dict:
        """Procesar conversión y calcular comisión"""
        try:
            conversion, commission = self.conversion_service.process_conversion(
                affiliate_id=command.affiliate_id,
                event_type=command.event_type,
                amount=command.amount,
                currency=command.currency
            )
            
            return {
                "conversion_id": str(conversion.id),
                "commission_id": str(commission.id),
                "commission_amount": float(commission.amount)
            }
        except Exception:
            self.session.rollback()
            raise
    
    def handle_registrar_conversion(self, command: RegistrarConversionCommand) -> dict:
        """Registrar conversión (compatibilidad con routes.py)"""
        try:
            # Convertir comando de compatibilidad a procesamiento estándar
            from decimal import Decimal
            conversion, commission = self.conversion_service.process_conversion(
                affiliate_id=command.affiliate_id,
                event_type=command.event_type,
                amount=Decimal(str(command.monto)),
                currency=command.moneda
            )
            
            return {
                "conversion_id": str(conversion.id),
                "commission_id": str(commission.id),
                "commission_amount": float(commission.amount),
                "affiliate_id": str(command.affiliate_id),
                "event_type": command.event_type,
                "amount": command.monto,
                "currency": command.moneda,
                "timestamp": command.occurred_at.isoformat() if command.occurred_at else None
            }
        except Exception:
            self.session.rollback()
            raise

class QueryHandler:
    """Handler unificado para consultas (lectura)"""
    
    def __init__(self, session: Session):
        self.session = session
        self.affiliate_service = AffiliateService(session)
        self.conversion_service = ConversionService(session)
    
    def handle_get_affiliate(self, query: GetAffiliateQuery) -> Optional[Affiliate]:
        """Obtener afiliado por ID"""
        return self.affiliate_service.get_affiliate(query.affiliate_id)
    
    def handle_list_affiliates(self, query: ListAffiliatesQuery) -> List[Affiliate]:
        """Listar afiliados"""
        return self.affiliate_service.list_affiliates(query.active_only)
    
    def handle_list_commissions(self, query: ListCommissionsQuery) -> List[Commission]:
        """Listar comisiones de un afiliado"""
        return self.conversion_service.get_commissions_for_affiliate(
            affiliate_id=query.affiliate_id,
            start_date=query.start_date,
            end_date=query.end_date
        )
    
    def handle_consultar_comisiones_por_afiliado(self, query: ConsultarComisionesPorAfiliadoQuery) -> List[dict]:
        """Consultar comisiones por afiliado (compatibilidad con routes.py)"""
        commissions = self.conversion_service.get_commissions_for_affiliate(
            affiliate_id=query.affiliate_id,
            start_date=query.desde,
            end_date=query.hasta
        )
        
        # Convertir a formato JSON serializable
        return [
            {
                "commission_id": str(commission.id),
                "affiliate_id": str(commission.affiliate_id),
                "amount": float(commission.amount),
                "currency": commission.currency,
                "status": commission.status
            }
            for commission in commissions
        ]

# Factory para crear handlers
def create_handlers(session: Session):
    """Crear instancias de handlers con sesión"""
    return {
        'command_handler': CommandHandler(session),
        'query_handler': QueryHandler(session)
    }