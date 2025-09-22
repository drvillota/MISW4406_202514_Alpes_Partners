"""Handlers para comandos y consultas en el microservicio de Colaboraciones"""

from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session

from .comandos import (
    IniciarColaboracionComando,
    FirmarContratoComando,
    CancelarContratoComando,
    FinalizarColaboracionComando,
    RegistrarPublicacionComando,
)
from .servicios import ColaboracionService, PublicacionService
from domain.entidades import Colaboracion, Publicacion
from .queries import ConsultarColaboracionQuery, ListarColaboracionesQuery


class CommandHandler:
    """Handler unificado para comandos (escritura)"""

    def __init__(self, session: Session):
        self.session = session
        self.colaboracion_service = ColaboracionService(session)
        self.publicacion_service = PublicacionService(session)

    def handle_iniciar_colaboracion(self, command: IniciarColaboracionComando) -> str:
        """Iniciar nueva colaboración usando contrato ya existente"""
        try:
            colaboracion = self.colaboracion_service.iniciar_colaboracion(
                campania_id=command.campania_id,
                influencer_id=command.influencer_id,
                contrato_id=command.contrato_id,   # 👈 ahora se pasa el contrato existente
            )
            return str(colaboracion.id)
        except Exception:
            self.session.rollback()
            raise

    def handle_firmar_contrato(self, command: FirmarContratoComando) -> None:
        """Firmar contrato en colaboración"""
        try:
            self.colaboracion_service.firmar_contrato(command.colaboracion_id)
        except Exception:
            self.session.rollback()
            raise

    def handle_cancelar_contrato(self, command: CancelarContratoComando) -> None:
        """Cancelar contrato en colaboración"""
        try:
            self.colaboracion_service.cancelar_contrato(
                command.colaboracion_id, motivo=command.motivo
            )
        except Exception:
            self.session.rollback()
            raise

    def handle_finalizar_colaboracion(self, command: FinalizarColaboracionComando) -> None:
        """Finalizar colaboración"""
        try:
            self.colaboracion_service.finalizar_colaboracion(command.colaboracion_id)
        except Exception:
            self.session.rollback()
            raise

    def handle_registrar_publicacion(self, command: RegistrarPublicacionComando) -> dict:
        """Registrar publicación en colaboración"""
        try:
            publicacion = self.publicacion_service.registrar_publicacion(
                colaboracion_id=command.colaboracion_id,
                url=command.url,
                red=command.red,
                fecha=command.fecha,
            )
            return {
                "colaboracion_id": str(command.colaboracion_id),
                "url": publicacion.url,
                "red": publicacion.red,
                "fecha": publicacion.fecha.isoformat(),
            }
        except Exception:
            self.session.rollback()
            raise


class QueryHandler:
    """Handler unificado para consultas (lectura)"""

    def __init__(self, session: Session):
        self.session = session
        self.colaboracion_service = ColaboracionService(session)

    def handle_consultar_colaboracion(
        self, query: ConsultarColaboracionQuery
    ) -> Optional[Colaboracion]:
        """Obtener colaboración por ID"""
        return self.colaboracion_service.obtener_colaboracion(query.colaboracion_id)

    def handle_listar_colaboraciones(
        self, query: ListarColaboracionesQuery
    ) -> List[Colaboracion]:
        """Listar colaboraciones con filtros opcionales"""
        return self.colaboracion_service.listar_colaboraciones()


# Factory para crear handlers
def create_handlers(session: Session):
    """Crear instancias de handlers con sesión"""
    return {
        "command_handler": CommandHandler(session),
        "query_handler": QueryHandler(session),
    }
