"""
Saga Log Repository - Sistema de seguimiento de transacciones distribuidas
"""
import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from enum import Enum
from uuid import UUID
from dataclasses import dataclass, asdict
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class SagaStatus(Enum):
    STARTED = "STARTED"
    STEP_COMPLETED = "STEP_COMPLETED"
    COMPENSATING = "COMPENSATING"
    COMPLETED = "COMPLETED" 
    FAILED = "FAILED"


@dataclass
class SagaStep:
    step_name: str
    status: str
    payload: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None
    compensation_data: Optional[Dict[str, Any]] = None


@dataclass
class SagaTransaction:
    id: str
    saga_type: str
    status: SagaStatus
    steps: List[SagaStep]
    created_at: datetime
    updated_at: datetime
    correlation_id: Optional[str] = None
    saga_metadata: Optional[Dict[str, Any]] = None


class SagaLogModel(Base):
    __tablename__ = "saga_logs"
    
    id = Column(String, primary_key=True)
    saga_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    steps = Column(JSONB, nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    correlation_id = Column(String, nullable=True)
    saga_metadata = Column(JSONB, nullable=True)


class SagaLogRepository:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        
    async def init_database(self):
        """Inicializar base de datos para saga log"""
        try:
            self.engine = create_engine(settings.database_url)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Crear tablas si no existen
            Base.metadata.create_all(bind=self.engine)
            logger.info("Saga Log database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing saga database: {e}")
            # Para desarrollo, usar SQLite como fallback
            fallback_url = "sqlite:///./saga_logs.db"
            self.engine = create_engine(fallback_url)
            self.SessionLocal = sessionmaker(bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            logger.warning(f"Using SQLite fallback: {fallback_url}")
    
    def _get_session(self) -> Session:
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call init_database() first.")
        return self.SessionLocal()
    
    async def start_saga(self, saga_id: str, saga_type: str, correlation_id: Optional[str] = None, 
                        saga_metadata: Optional[Dict[str, Any]] = None) -> SagaTransaction:
        """Iniciar nueva saga"""
        session = self._get_session()
        try:
            now = datetime.now(timezone.utc)
            saga_model = SagaLogModel(
                id=saga_id,
                saga_type=saga_type,
                status=SagaStatus.STARTED.value,
                steps=[],
                created_at=now,
                updated_at=now,
                correlation_id=correlation_id,
                saga_metadata=saga_metadata or {}
            )
            
            session.add(saga_model)
            session.commit()
            
            saga_transaction = SagaTransaction(
                id=saga_id,
                saga_type=saga_type,
                status=SagaStatus.STARTED,
                steps=[],
                created_at=now,
                updated_at=now,
                correlation_id=correlation_id,
                saga_metadata=saga_metadata
            )
            
            logger.info(f"Saga iniciada: {saga_id} - {saga_type}")
            return saga_transaction
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error starting saga {saga_id}: {e}")
            raise
        finally:
            session.close()
    
    async def log_step(self, saga_id: str, step_name: str, status: str, 
                      payload: Dict[str, Any], error_message: Optional[str] = None) -> None:
        """Registrar paso completado en la saga"""
        session = self._get_session()
        try:
            saga_model = session.query(SagaLogModel).filter_by(id=saga_id).first()
            if not saga_model:
                raise ValueError(f"Saga {saga_id} not found")
            
            step = SagaStep(
                step_name=step_name,
                status=status,
                payload=payload,
                timestamp=datetime.now(timezone.utc),
                error_message=error_message
            )
            
            # Agregar paso a la lista
            current_steps = saga_model.steps or []
            current_steps.append(asdict(step))
            saga_model.steps = current_steps
            saga_model.updated_at = datetime.now(timezone.utc)
            
            # Actualizar status general si es necesario
            if status == "FAILED":
                saga_model.status = SagaStatus.FAILED.value
            elif status == "COMPLETED" and step_name.endswith("_final"):
                saga_model.status = SagaStatus.COMPLETED.value
            elif status == "COMPENSATING":
                saga_model.status = SagaStatus.COMPENSATING.value
            else:
                saga_model.status = SagaStatus.STEP_COMPLETED.value
            
            session.commit()
            logger.info(f"📝 Step logged: {saga_id} - {step_name} - {status}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging step for saga {saga_id}: {e}")
            raise
        finally:
            session.close()
    
    async def log_compensation(self, saga_id: str, step_name: str, error: str, 
                              compensation_data: Optional[Dict[str, Any]] = None) -> None:
        """Registrar compensación"""
        await self.log_step(
            saga_id, 
            f"compensate_{step_name}", 
            "COMPENSATING", 
            compensation_data or {}, 
            error
        )
    
    async def get_saga(self, saga_id: str) -> Optional[SagaTransaction]:
        """Obtener saga por ID"""
        session = self._get_session()
        try:
            saga_model = session.query(SagaLogModel).filter_by(id=saga_id).first()
            if not saga_model:
                return None
            
            steps = [
                SagaStep(**step_data) 
                for step_data in (saga_model.steps or [])
            ]
            
            return SagaTransaction(
                id=saga_model.id,
                saga_type=saga_model.saga_type,
                status=SagaStatus(saga_model.status),
                steps=steps,
                created_at=saga_model.created_at,
                updated_at=saga_model.updated_at,
                correlation_id=saga_model.correlation_id,
                saga_metadata=saga_model.saga_metadata
            )
            
        except Exception as e:
            logger.error(f"Error getting saga {saga_id}: {e}")
            return None
        finally:
            session.close()
    
    async def list_sagas(self, limit: int = 100, saga_type: Optional[str] = None,
                        status: Optional[SagaStatus] = None) -> List[SagaTransaction]:
        """Listar sagas con filtros opcionales"""
        session = self._get_session()
        try:
            query = session.query(SagaLogModel).order_by(SagaLogModel.created_at.desc())
            
            if saga_type:
                query = query.filter_by(saga_type=saga_type)
            if status:
                query = query.filter_by(status=status.value)
            
            saga_models = query.limit(limit).all()
            
            sagas = []
            for saga_model in saga_models:
                steps = [
                    SagaStep(**step_data) 
                    for step_data in (saga_model.steps or [])
                ]
                
                sagas.append(SagaTransaction(
                    id=saga_model.id,
                    saga_type=saga_model.saga_type,
                    status=SagaStatus(saga_model.status),
                    steps=steps,
                    created_at=saga_model.created_at,
                    updated_at=saga_model.updated_at,
                    correlation_id=saga_model.correlation_id,
                    saga_metadata=saga_model.saga_metadata
                ))
            
            return sagas
            
        except Exception as e:
            logger.error(f"Error listing sagas: {e}")
            return []
        finally:
            session.close()
    
    async def get_saga_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de sagas"""
        session = self._get_session()
        try:
            # Contar por status
            status_counts = {}
            for status in SagaStatus:
                count = session.query(SagaLogModel).filter_by(status=status.value).count()
                status_counts[status.value] = count
            
            # Contar por tipo
            type_counts = {}
            results = session.query(SagaLogModel.saga_type, 
                                  session.query(SagaLogModel).filter_by(saga_type=SagaLogModel.saga_type).count().label('count')
                                  ).group_by(SagaLogModel.saga_type).all()
            
            for saga_type, count in results:
                type_counts[saga_type] = count
            
            total_count = session.query(SagaLogModel).count()
            
            return {
                "total_sagas": total_count,
                "by_status": status_counts,
                "by_type": type_counts,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting saga statistics: {e}")
            return {"error": str(e)}
        finally:
            session.close()