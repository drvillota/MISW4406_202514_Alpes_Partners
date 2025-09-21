"""Repositorios SQLAlchemy para Colaboraciones"""

from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

# Entidades de dominio
from ...domain.entidades import Colaboracion, Campania, Influencer, Contrato
from ...core.seedworks.objetos_valor import (
    Identificador,
    EstadoColaboracion,
    EstadoCampania,
    EstadoContrato,
    Periodo,
    Email,
    Publicacion,
)

# Modelos de infraestructura
from .dto import ColaboracionModel, CampaniaModel, InfluencerModel, ContratoModel

class ColaboracionRepository:
    """Repositorio simplificado para la raíz de agregación Colaboracion"""

    def __init__(self, session: Session):
        self.session = session

    def agregar(self, colaboracion: Colaboracion) -> None:
        """Guardar nueva colaboración, usando campaña e influencer existentes si aplica"""

        # Buscar campaña existente
        campania_model = self.session.get(CampaniaModel, colaboracion.campania.id.codigo)
        if not campania_model:
            campania_model = CampaniaModel(
                id=colaboracion.campania.id.codigo,
                nombre=colaboracion.campania.nombre.valor,
                marca=colaboracion.campania.marca,
                fecha_inicio=colaboracion.campania.periodo.inicio,
                fecha_fin=colaboracion.campania.periodo.fin,
                estado=colaboracion.campania.estado.valor,
            )
            self.session.add(campania_model)

        # Buscar influencer existente
        influencer_model = self.session.get(InfluencerModel, colaboracion.influencer.id.codigo)
        if not influencer_model:
            influencer_model = InfluencerModel(
                id=colaboracion.influencer.id.codigo,
                nombre=colaboracion.influencer.nombre,
                email=colaboracion.influencer.email.direccion,
            )
            self.session.add(influencer_model)

        # Crear contrato
        contrato_model = ContratoModel(
            id=colaboracion.contrato.id.codigo,
            colaboracion_id=colaboracion.id.codigo,
            fecha_inicio=colaboracion.contrato.periodo.inicio,
            fecha_fin=colaboracion.contrato.periodo.fin,
            estado=colaboracion.contrato.estado.valor,
        )
        self.session.add(contrato_model)

        # Crear colaboración
        colaboracion_model = ColaboracionModel(
            id=colaboracion.id.codigo,
            campania_id=campania_model.id,
            influencer_id=influencer_model.id,
            contrato_id=contrato_model.id,
            estado=colaboracion.estado.valor,
            publicaciones=[]  # siempre empieza vacío
        )
        self.session.add(colaboracion_model)
        self.session.commit()

    def obtener_por_id(self, colaboracion_id: UUID) -> Optional[Colaboracion]:
        """Obtener colaboración por ID"""
        model = self.session.get(ColaboracionModel, colaboracion_id)
        if not model:
            return None

        campania_model = self.session.get(CampaniaModel, model.campania_id)
        influencer_model = self.session.get(InfluencerModel, model.influencer_id)
        contrato_model = self.session.get(ContratoModel, model.contrato_id)

        publicaciones = []
        if model.publicaciones:
            publicaciones = [
                Publicacion(
                    url=p["url"],
                    red=p["red"],
                    fecha=p["fecha"],  # conviértelo a date si lo quieres estricto
                )
                for p in model.publicaciones
            ]

        return Colaboracion(
            id=Identificador(model.id),
            campania=Campania(
                id=Identificador(campania_model.id),
                nombre=campania_model.nombre,
                marca=campania_model.marca,
                periodo=Periodo(
                    inicio=campania_model.fecha_inicio, fin=campania_model.fecha_fin
                ),
                estado=EstadoCampania(campania_model.estado),
            ),
            influencer=Influencer(
                id=Identificador(influencer_model.id),
                nombre=influencer_model.nombre,
                email=Email(influencer_model.email),
            ),
            contrato=Contrato(
                id=Identificador(contrato_model.id),
                periodo=Periodo(
                    inicio=contrato_model.fecha_inicio, fin=contrato_model.fecha_fin
                ),
                estado=EstadoContrato(contrato_model.estado),
            ),
            estado=EstadoColaboracion(model.estado),
            publicaciones=publicaciones or [],  # nunca None
        )