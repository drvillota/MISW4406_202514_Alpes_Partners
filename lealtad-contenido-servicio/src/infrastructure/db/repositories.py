"""Repositorios SQLAlchemy simplificados para afiliados-contenidos"""

from uuid import UUID
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

# Importar entidades de dominio simplificadas
from ...domain.entities import Affiliate, Content

# Importar modelos de base de datos
from .models import AffiliateModel, ContentModel

class AffiliateRepository:
    """Repositorio simplificado para Afiliados"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, affiliate: Affiliate) -> None:
        """Guardar afiliado"""
        model = AffiliateModel(
            id=affiliate.id,
            name=affiliate.name,
            email=affiliate.email,            
            commission_rate=float(affiliate.commission_rate),
            leal=affiliate.leal,
            active=affiliate.active,
            created_at=affiliate.created_at
        )
        self.session.add(model)
        self.session.commit()
    
    def get_by_id(self, affiliate_id: UUID) -> Optional[Affiliate]:
        """Obtener afiliado por ID"""
        model = self.session.get(AffiliateModel, affiliate_id)
        if not model:
            return None
            
        return Affiliate(
            id=UUID(str(model.id)) if isinstance(model.id, str) else model.id,
            name=model.name,
            email=model.email,
            commission_rate=Decimal(str(model.commission_rate)),
            leal=model.leal,
            created_at=model.created_at,
            active=model.active
        )
    
    def get_by_email(self, email: str) -> Optional[Affiliate]:
        """Obtener afiliado por email"""
        stmt = select(AffiliateModel).where(AffiliateModel.email == email)
        model = self.session.execute(stmt).scalar_one_or_none()
        
        if not model:
            return None
            
        return Affiliate(
            id=UUID(str(model.id)) if isinstance(model.id, str) else model.id,
            name=model.name,
            email=model.email,
            commission_rate=Decimal(str(model.commission_rate)),
            leal=model.leal,
            created_at=model.created_at,
            active=model.active
        )
    
    def list_all(self, active_only: bool = False) -> List[Affiliate]:
        """Listar afiliados"""
        stmt = select(AffiliateModel)
        if active_only:
            stmt = stmt.where(AffiliateModel.active == True)
            
        models = self.session.execute(stmt).scalars().all()
        
        return [
            Affiliate(
                id=UUID(str(model.id)) if isinstance(model.id, str) else model.id,
                name=model.name,
                email=model.email,
                commission_rate=Decimal(str(model.commission_rate)),
                leal=model.leal,
                created_at=model.created_at,
                active=model.active
            )
            for model in models
        ]
    
    def update_status(self, affiliate_id: UUID, active: bool) -> None:
        """Actualizar estado del afiliado"""
        model = self.session.get(AffiliateModel, affiliate_id)
        if model:
            model.active = active
            self.session.commit()

class ContentRepository:
    """Repositorio simplificado para Contenidos"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, content: Content) -> None:
        """Guardar contenido"""
        model = ContentModel(
            id=content.id,
            affiliate_id=content.affiliate_id,
            titulo=content.titulo,
            contenido=content.contenido,
            tipo=content.tipo,
            publicar=content.publicar,
            created_at=content.created_at
        )
        self.session.add(model)
        self.session.commit()
    
    def get_by_id(self, content_id: UUID) -> Optional[Content]:
        """Obtener contenido por ID"""
        model = self.session.get(ContentModel, content_id)
        if not model:
            return None
            
        return Content(
            id=UUID(str(model.id)) if isinstance(model.id, str) else model.id,
            affiliate_id=UUID(str(model.affiliate_id)) if isinstance(model.affiliate_id, str) else model.affiliate_id,
            titulo=model.titulo,
            contenido=model.contenido,
            tipo=model.tipo,
            publicar=model.publicar,
            created_at=model.created_at
        )
    
    def list_by_affiliate(
        self, 
        affiliate_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Content]:
        """Listar contenidos por afiliado"""
        stmt = select(ContentModel).where(ContentModel.affiliate_id == affiliate_id)

        if start_date:
            stmt = stmt.where(ContentModel.created_at >= start_date)
        if end_date:
            stmt = stmt.where(ContentModel.created_at <= end_date)

        models = self.session.execute(stmt).scalars().all()
        
        return [
            Content(
                id=UUID(str(model.id)) if isinstance(model.id, str) else model.id,
                affiliate_id=UUID(str(model.affiliate_id)) if isinstance(model.affiliate_id, str) else model.affiliate_id,
                titulo=model.titulo,
                contenido=model.contenido,
                tipo=model.tipo,
                publicar=model.publicar,
                created_at=model.created_at
            )
            for model in models
        ]
    
    def update_status(self, content_id: UUID, status: str) -> None:
        """Actualizar estado de contenido"""
        model = self.session.get(ContentModel, content_id)
        if model:
            model.publicar = status
            self.session.commit()

# Factory para crear repositorios con sesión
def create_repositories(session: Session):
    """Crear instancias de todos los repositorios"""
    return {
        'affiliate_repo': AffiliateRepository(session),
        'content_repo': ContentRepository(session)
    }
