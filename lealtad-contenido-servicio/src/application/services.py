"""Servicios de dominio simplificados para afiliados-comisiones"""

from uuid import UUID, uuid4
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from ..domain.entities import Affiliate, Content
from ..infrastructure.db.repositories import AffiliateRepository, ContentRepository

class AffiliateService:
    """Servicio de dominio para afiliados"""
    
    def __init__(self, session: Session):
        self.affiliate_repo = AffiliateRepository(session)
        self.content_repo = ContentRepository(session)
    
    def register_affiliate(
        self, 
        name: str, 
        email: str, 
        commission_rate: Decimal,
        leal: str
    ) -> Affiliate:
        """Registrar nuevo afiliado"""
        
        # Verificar que no existe el email
        existing = self.affiliate_repo.get_by_email(email)
        if existing:
            raise ValueError(f"Ya existe un afiliado con email {email}")
        
        # Crear nuevo afiliado
        affiliate = Affiliate(
            id=uuid4(),
            name=name,
            email=email,
            commission_rate=commission_rate,
            leal=leal
            created_at=datetime.now(timezone.utc),
            active=True
        )
        
        # Guardar
        self.affiliate_repo.save(affiliate)
        
        # En una implementación completa, aquí se publicaría el evento AffiliateRegistered
        
        return affiliate
    
    def activate_affiliate(self, affiliate_id: UUID) -> None:
        """Activar afiliado"""
        affiliate = self.affiliate_repo.get_by_id(affiliate_id)
        if not affiliate:
            raise ValueError(f"Afiliado {affiliate_id} no encontrado")
        
        self.affiliate_repo.update_status(affiliate_id, True)
    
    def deactivate_affiliate(self, affiliate_id: UUID) -> None:
        """Desactivar afiliado"""
        affiliate = self.affiliate_repo.get_by_id(affiliate_id)
        if not affiliate:
            raise ValueError(f"Afiliado {affiliate_id} no encontrado")
        
        self.affiliate_repo.update_status(affiliate_id, False)
    
    def get_affiliate(self, affiliate_id: UUID) -> Optional[Affiliate]:
        """Obtener afiliado por ID"""
        return self.affiliate_repo.get_by_id(affiliate_id)
    
    def list_affiliates(self, active_only: bool = True) -> List[Affiliate]:
        """Listar afiliados"""
        return self.affiliate_repo.list_all(active_only)

class ContentService:
    """Servicio de dominio para contenidos"""
    
    def __init__(self, session: Session):
        self.affiliate_repo = AffiliateRepository(session)
        self.content_repo = ContentRepository(session)
    
    def register_content(
        self, 
        affiliate_id: UUID,
        titulo: str,
        contenido: str,
        tipo: str
    ) -> Content:
        """Registrar nuevo contenido"""
        
        # Verificar que el afiliado existe
        affiliate = self.affiliate_repo.get_by_id(affiliate_id)
        if not affiliate:
            raise ValueError(f"Afiliado {affiliate_id} no encontrado")
        
        # Crear nuevo contenido
        content = Content(
            id=uuid4(),
            affiliate_id=affiliate_id,
            titulo=titulo,
            contenido=contenido,
            tipo=tipo,
            publicar= str("No"),
            created_at=datetime.now(timezone.utc)
        )
        
        # Guardar
        self.content_repo.save(content)
        
        # En una implementación completa, aquí se publicaría el evento ContentRegistered
        
        return content

# Factory para crear servicios
def create_services(session: Session):
    """Crear instancias de todos los servicios"""
    return {
        'affiliate_service': AffiliateService(session),
        'content_service': ContentService(session)
    }