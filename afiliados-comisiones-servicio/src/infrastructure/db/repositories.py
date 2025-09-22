"""Repositorios SQLAlchemy simplificados para afiliados-comisiones"""

from uuid import UUID
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

# Importar entidades de dominio simplificadas
from ...domain.entities import Affiliate, Commission, ConversionEvent

# Importar modelos de base de datos
from .models import AffiliateModel, CommissionModel, ConversionEventModel

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
                created_at=model.created_at,
                active=model.active
            )
            for model in models
        ]

class ConversionEventRepository:
    """Repositorio simplificado para Eventos de Conversión"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, conversion: ConversionEvent) -> None:
        """Guardar evento de conversión"""
        model = ConversionEventModel(
            id=conversion.id,
            affiliate_id=conversion.affiliate_id,
            event_type=conversion.event_type,
            amount=float(conversion.amount),
            currency=conversion.currency,
            occurred_at=conversion.occurred_at,
            processed=conversion.processed
        )
        self.session.add(model)
        self.session.commit()
    
    def get_by_id(self, conversion_id: UUID) -> Optional[ConversionEvent]:
        """Obtener conversión por ID"""
        model = self.session.get(ConversionEventModel, conversion_id)
        if not model:
            return None
            
        return ConversionEvent(
            id=UUID(str(model.id)) if isinstance(model.id, str) else model.id,
            affiliate_id=UUID(str(model.affiliate_id)) if isinstance(model.affiliate_id, str) else model.affiliate_id,
            event_type=model.event_type,
            amount=Decimal(str(model.amount)),
            occurred_at=model.occurred_at,
            currency=model.currency,
            processed=model.processed
        )
    
    def mark_as_processed(self, conversion_id: UUID) -> None:
        """Marcar conversión como procesada"""
        model = self.session.get(ConversionEventModel, conversion_id)
        if model:
            model.processed = True
            self.session.commit()

class CommissionRepository:
    """Repositorio simplificado para Comisiones"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, commission: Commission) -> None:
        """Guardar comisión"""
        model = CommissionModel(
            id=commission.id,
            affiliate_id=commission.affiliate_id,
            conversion_id=commission.conversion_id,
            amount=float(commission.amount),
            currency=commission.currency,
            status=commission.status,
            calculated_at=commission.calculated_at
        )
        self.session.add(model)
        self.session.commit()
    
    def get_by_id(self, commission_id: UUID) -> Optional[Commission]:
        """Obtener comisión por ID"""
        model = self.session.get(CommissionModel, commission_id)
        if not model:
            return None
            
        return Commission(
            id=UUID(str(model.id)) if isinstance(model.id, str) else model.id,
            affiliate_id=UUID(str(model.affiliate_id)) if isinstance(model.affiliate_id, str) else model.affiliate_id,
            conversion_id=UUID(str(model.conversion_id)) if isinstance(model.conversion_id, str) else model.conversion_id,
            amount=Decimal(str(model.amount)),
            calculated_at=model.calculated_at,
            currency=model.currency,
            status=model.status
        )
    
    def list_by_affiliate(
        self, 
        affiliate_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Commission]:
        """Listar comisiones por afiliado"""
        stmt = select(CommissionModel).where(CommissionModel.affiliate_id == affiliate_id)
        
        if start_date:
            stmt = stmt.where(CommissionModel.calculated_at >= start_date)
        if end_date:
            stmt = stmt.where(CommissionModel.calculated_at <= end_date)
            
        models = self.session.execute(stmt).scalars().all()
        
        return [
            Commission(
                id=UUID(str(model.id)) if isinstance(model.id, str) else model.id,
                affiliate_id=UUID(str(model.affiliate_id)) if isinstance(model.affiliate_id, str) else model.affiliate_id,
                conversion_id=UUID(str(model.conversion_id)) if isinstance(model.conversion_id, str) else model.conversion_id,
                amount=Decimal(str(model.amount)),
                calculated_at=model.calculated_at,
                currency=model.currency,
                status=model.status
            )
            for model in models
        ]
    
    def update_status(self, commission_id: UUID, status: str) -> None:
        """Actualizar estado de comisión"""
        model = self.session.get(CommissionModel, commission_id)
        if model:
            model.status = status
            self.session.commit()

# Factory para crear repositorios con sesión
def create_repositories(session: Session):
    """Crear instancias de todos los repositorios"""
    return {
        'affiliate_repo': AffiliateRepository(session),
        'conversion_repo': ConversionEventRepository(session),
        'commission_repo': CommissionRepository(session)
    }
