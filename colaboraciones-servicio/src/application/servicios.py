"""Servicios de dominio para colaboraciones e influencers"""

from uuid import UUID
from typing import Optional, List
from datetime import date, datetime, timezone

from ..domain.entidades import Colaboracion, Contrato, Influencer, Campania
from ..core.seedworks.objetos_valor import (
    Identificador,
    EstadoColaboracion,
    EstadoContrato,
    Periodo,
    Publicacion,
)
from ..infrastructure.database.repositories import ColaboracionRepository


class ColaboracionService:
    """Servicio de dominio para colaboraciones"""

    def __init__(self, session):
        self.colaboracion_repo = ColaboracionRepository(session)

    def iniciar_colaboracion(
        self,
        campania: Campania,
        influencer: Influencer,
        contrato_periodo: Periodo,
    ) -> Colaboracion:
        """Iniciar una nueva colaboración"""

        colaboracion = Colaboracion(
            id=Identificador.nuevo(),
            campania=campania,
            influencer=influencer,
            contrato=Contrato(
                id=Identificador.nuevo(),
                periodo=contrato_periodo,
                estado=EstadoContrato("PENDIENTE"),
            ),
            estado=EstadoColaboracion("VIGENTE"),
        )

        self.colaboracion_repo.agregar(colaboracion)

        # Aquí se publicaría ColaboracionIniciada a Pulsar
        return colaboracion

    def firmar_contrato(self, colaboracion_id: UUID) -> None:
        """Firmar contrato en colaboración"""
        colaboracion = self.colaboracion_repo.obtener_por_id(colaboracion_id)
        if not colaboracion:
            raise ValueError(f"Colaboración {colaboracion_id} no encontrada")

        colaboracion.firmar_contrato()
        self.colaboracion_repo.actualizar(colaboracion)

        # Publicar ContratoFirmado a Pulsar

    def cancelar_contrato(
        self, colaboracion_id: UUID, motivo: Optional[str] = None
    ) -> None:
        """Cancelar contrato en colaboración"""
        colaboracion = self.colaboracion_repo.obtener_por_id(colaboracion_id)
        if not colaboracion:
            raise ValueError(f"Colaboración {colaboracion_id} no encontrada")

        colaboracion.cancelar()
        self.colaboracion_repo.actualizar(colaboracion)

        # Publicar ContratoCancelado a Pulsar

    def finalizar_colaboracion(self, colaboracion_id: UUID) -> None:
        """Finalizar colaboración"""
        colaboracion = self.colaboracion_repo.obtener_por_id(colaboracion_id)
        if not colaboracion:
            raise ValueError(f"Colaboración {colaboracion_id} no encontrada")

        colaboracion.finalizar()
        self.colaboracion_repo.actualizar(colaboracion)

        # Publicar ColaboracionFinalizada a Pulsar

    def obtener_colaboracion(self, colaboracion_id: UUID) -> Optional[Colaboracion]:
        """Obtener colaboración por ID"""
        return self.colaboracion_repo.obtener_por_id(colaboracion_id)

    def listar_colaboraciones(self) -> List[Colaboracion]:
        """Listar colaboraciones"""
        return self.colaboracion_repo.obtener_todos()


class PublicacionService:
    """Servicio de dominio para publicaciones dentro de colaboraciones"""

    def __init__(self, session):
        self.colaboracion_repo = ColaboracionRepository(session)

    def registrar_publicacion(
        self, colaboracion_id: UUID, url: str, red: str, fecha: date
    ) -> Publicacion:
        """Registrar publicación en colaboración"""
        colaboracion = self.colaboracion_repo.obtener_por_id(colaboracion_id)
        if not colaboracion:
            raise ValueError(f"Colaboración {colaboracion_id} no encontrada")

        publicacion = Publicacion(url=url, red=red, fecha=fecha)
        colaboracion.registrar_publicacion(publicacion)

        self.colaboracion_repo.actualizar(colaboracion)

        # Publicar PublicacionRegistrada a Pulsar
        return publicacion


# Factory para crear servicios
def create_services(session):
    """Crear instancias de los servicios de dominio"""
    return {
        "colaboracion_service": ColaboracionService(session),
        "publicacion_service": PublicacionService(session),
    }
