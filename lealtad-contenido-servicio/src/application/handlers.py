"""Handlers simplificados para comandos y consultas usando servicios de dominio"""

from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .commands import (
    RegisterAffiliateCommand,
    ActivateAffiliateCommand,
    DeactivateAffiliateCommand,
    RegistrarContentCommand,
    GetAffiliateQuery,
    ListContentsQuery,
    ListAffiliatesQuery,
    ConsultarContenidosPorAfiliadoQuery
)
from .services import AffiliateService, ContentService
from ..domain.entities import Affiliate, Content

class CommandHandler:
    """Handler unificado para comandos (escritura)"""
    
    def __init__(self, session: Session):
        self.session = session
        self.affiliate_service = AffiliateService(session)
        self.content_service = ContentService(session)
    
    def handle_register_affiliate(self, command: RegisterAffiliateCommand) -> str:
        """Registrar nuevo afiliado"""
        try:
            affiliate = self.affiliate_service.register_affiliate(
                name=command.name,
                email=command.email,
                commission_rate=command.commission_rate
                leal=command.leal
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

    def handle_registrar_contenido(self, command: RegistrarContentCommand) -> dict:
        """Registrar contenido (compatibilidad con routes.py)"""
        try:
            # Convertir comando de compatibilidad a procesamiento estándar
            from decimal import Decimal
            contenido = self.content_service.register_content(
                affiliate_id=command.affiliate_id,
                titulo=command.titulo,
                contenido=command.contenido,
                tipo=command.tipo
            )
            return {
                "contenido_id": str(contenido.id),
                "affiliate_id": str(command.affiliate_id),
                "titulo": command.titulo,
                "contenido": command.contenido,
                "tipo": command.tipo
            }
        except Exception:
            self.session.rollback()
            raise

class QueryHandler:
    """Handler unificado para consultas (lectura)"""
    
    def __init__(self, session: Session):
        self.session = session
        self.affiliate_service = AffiliateService(session)
        self.content_service = ContentService(session)
    
    def handle_get_affiliate(self, query: GetAffiliateQuery) -> Optional[Affiliate]:
        """Obtener afiliado por ID"""
        return self.affiliate_service.get_affiliate(query.affiliate_id)
    
    def handle_list_affiliates(self, query: ListAffiliatesQuery) -> List[Affiliate]:
        """Listar afiliados"""
        return self.affiliate_service.list_affiliates(query.active_only)

    def handle_list_contents(self, query: ListContentsQuery) -> List[Content]:
        """Listar contenidos de un afiliado"""
        return self.content_service.list_contents_for_affiliate(
            affiliate_id=query.affiliate_id,
            start_date=query.start_date,
            end_date=query.end_date
        )
    
    def handle_consultar_contenidos_por_afiliado(self, query: ConsultarContenidosPorAfiliadoQuery) -> List[dict]:
        """Consultar contenidos por afiliado (compatibilidad con routes.py)"""
        contents = self.content_service.list_contents_for_affiliate(
            affiliate_id=query.affiliate_id,
            start_date=query.desde,
            end_date=query.hasta
        )
        
        # Convertir a formato JSON serializable
        return [
            {
                "affiliate_id": str(content.affiliate_id),
                "titulo": content.titulo,
                "contenido": content.contenido,
                "tipo": content.tipo
            }
            for content in contents
        ]

# Factory para crear handlers
def create_handlers(session: Session):
    """Crear instancias de handlers con sesión"""
    return {
        'command_handler': CommandHandler(session),
        'query_handler': QueryHandler(session)
    }