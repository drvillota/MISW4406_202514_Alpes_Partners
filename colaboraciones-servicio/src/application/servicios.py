from uuid import UUID
from typing import Optional, List
from datetime import date

from domain.eventos import PublicacionRegistrada
from domain.entidades import Colaboracion, Contrato, Influencer, Campania
from core.seedworks.objetos_valor import (
    Identificador,
    EstadoColaboracion,
    EstadoContrato,
    Periodo,
    Publicacion,
)
from infrastructure.database.repositories import (
    ColaboracionRepository,
    ContratoModel,
    CampaniaModel,
    InfluencerModel,
)
from core.seedworks.message_bus import bus

class ColaboracionService:
    """Servicio de dominio para colaboraciones"""

    def __init__(self, session):
        self.session = session
        self.colaboracion_repo = ColaboracionRepository(session)

    def iniciar_colaboracion(
        self,
        campania_id: UUID,
        influencer_id: UUID,
        contrato_id: UUID,
    ) -> Colaboracion:
        """Iniciar colaboración con contrato, campaña e influencer existentes"""

        # Validar contrato
        contrato_model = self.session.get(ContratoModel, contrato_id)
        if not contrato_model:
            raise ValueError(f"Contrato {contrato_id} no existe")

        contrato = Contrato(
            id=Identificador(contrato_model.id),
            periodo=Periodo(
                inicio=contrato_model.fecha_inicio,
                fin=contrato_model.fecha_fin,
            ),
            estado=EstadoContrato(contrato_model.estado),
        )

        # Validar campaña
        campania_model = self.session.get(CampaniaModel, campania_id)
        if not campania_model:
            raise ValueError(f"Campaña {campania_id} no existe")

        campania = Campania(
            id=Identificador(campania_model.id),
            nombre=campania_model.nombre,
            marca=campania_model.marca,
            fecha_inicio=campania_model.fecha_inicio,
            fecha_fin=campania_model.fecha_fin,
            estado=campania_model.estado,
        )

        # Validar influencer
        influencer_model = self.session.get(InfluencerModel, influencer_id)
        if not influencer_model:
            raise ValueError(f"Influencer {influencer_id} no existe")

        influencer = Influencer(
            id=Identificador(influencer_model.id),
            nombre=influencer_model.nombre,
            email=influencer_model.email,
        )

        # Crear la colaboración
        colaboracion = Colaboracion(
            id=Identificador.nuevo(),
            campania=campania,
            influencer=influencer,
            contrato=contrato,
            estado=EstadoColaboracion("VIGENTE"),
        )

        self.colaboracion_repo.agregar(colaboracion)
        return colaboracion

    # … firmar_contrato, cancelar_contrato, finalizar_colaboracion, etc.


class PublicacionService:
    """Servicio de dominio para publicaciones"""

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

        evento = PublicacionRegistrada(
            colaboracion_id=colaboracion_id,
            url=url,
            red=red,
            fecha=fecha
        )
        bus.handle_event(evento)
        
        return publicacion


# Factory
def create_services(session):
    return {
        "colaboracion_service": ColaboracionService(session),
        "publicacion_service": PublicacionService(session),
    }
