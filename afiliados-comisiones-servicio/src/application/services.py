"""Servicios de dominio simplificados para afiliados-comisiones"""

from uuid import UUID, uuid4
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from ..domain.entities import Affiliate, Commission, ConversionEvent
from ..infrastructure.db.repositories import AffiliateRepository, CommissionRepository, ConversionEventRepository

class AffiliateService:
    """Servicio de dominio para afiliados"""
    
    def __init__(self, session: Session):
        self.affiliate_repo = AffiliateRepository(session)
        self.conversion_repo = ConversionEventRepository(session)
        self.commission_repo = CommissionRepository(session)
    
    def register_affiliate(
        self, 
        name: str, 
        email: str, 
        commission_rate: Decimal
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

class ConversionService:
    """Servicio de dominio para conversiones y comisiones"""
    
    def __init__(self, session: Session):
        self.affiliate_repo = AffiliateRepository(session)
        self.conversion_repo = ConversionEventRepository(session)
        self.commission_repo = CommissionRepository(session)
    
    def process_conversion(
        self,
        affiliate_id: UUID,
        event_type: str,
        amount: Decimal,
        currency: str = "USD"
    ) -> tuple[ConversionEvent, Commission]:
        """Procesar conversión y calcular comisión automáticamente"""
        
        # Verificar que el afiliado existe y está activo
        affiliate = self.affiliate_repo.get_by_id(affiliate_id)
        if not affiliate:
            raise ValueError(f"Afiliado {affiliate_id} no encontrado")
        
        if not affiliate.active:
            raise ValueError(f"Afiliado {affiliate_id} no está activo")
        
        # Crear evento de conversión
        conversion = ConversionEvent(
            id=uuid4(),
            affiliate_id=affiliate_id,
            event_type=event_type,
            amount=amount,
            occurred_at=datetime.now(timezone.utc),
            currency=currency,
            processed=False
        )
        
        # Guardar conversión
        self.conversion_repo.save(conversion)
        
        # Calcular comisión
        commission_amount = affiliate.calculate_commission(amount)
        
        commission = Commission(
            id=uuid4(),
            affiliate_id=affiliate_id,
            conversion_id=conversion.id,
            amount=commission_amount,
            calculated_at=datetime.now(timezone.utc),
            currency=currency,
            status="pending"
        )
        
        # Guardar comisión
        self.commission_repo.save(commission)
        
        # Marcar conversión como procesada
        self.conversion_repo.mark_as_processed(conversion.id)
        
        # En una implementación completa, aquí se publicarían los eventos
        # ConversionProcessed y CommissionCalculated
        
        return conversion, commission
    
    def get_commissions_for_affiliate(
        self,
        affiliate_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Commission]:
        """Obtener comisiones de un afiliado"""
        return self.commission_repo.list_by_affiliate(
            affiliate_id, 
            start_date, 
            end_date
        )
    
    def mark_commission_as_paid(self, commission_id: UUID) -> None:
        """Marcar comisión como pagada"""
        commission = self.commission_repo.get_by_id(commission_id)
        if not commission:
            raise ValueError(f"Comisión {commission_id} no encontrada")
        
        self.commission_repo.update_status(commission_id, "paid")

# Factory para crear servicios
def create_services(session: Session):
    """Crear instancias de todos los servicios"""
    return {
        'affiliate_service': AffiliateService(session),
        'conversion_service': ConversionService(session)
    }