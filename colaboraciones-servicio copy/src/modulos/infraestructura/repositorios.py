# colaboraciones/src/modulos/infraestructura/repositorios.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

import json
from pulsar.schema import JsonSchema

from modulos.dominio.repositorios import (
    RepositorioColaboraciones,
    RepositorioEventosColaboraciones,
)
from modulos.dominio.entidades import Colaboracion
from modulos.dominio.fabricas import FabricaColaboraciones
from .dto import Colaboracion as ColaboracionDTO, EventoColaboracion as EventoColaboracionDTO
from .mapeadores import MapeadorColaboracionInfra, MapeadorEventoColaboracionInfra


class RepositorioColaboracionesSQLAlchemy(RepositorioColaboraciones):
    def __init__(self, session: Optional[Session] = None):
        """
        Repositorio que usa SQLAlchemy Session inyectada.
        Si no se proporciona `session`, se usa SessionLocal() de config.db como fallback.
        (Recomendado: inyectar siempre la session desde la UoW o Depends(get_db) en FastAPI.)
        """
        if session is None:
            # fallback para compatibilidad: crear una sesión si no se inyectó
            try:
                from config.db import SessionLocal  # import local para evitar ciclos
                self.session = SessionLocal()
            except Exception:
                raise RuntimeError(
                    "No se inyectó una Session y no se pudo obtener SessionLocal desde config.db"
                )
        else:
            self.session = session

        self._fabrica: FabricaColaboraciones = FabricaColaboraciones()

    @property
    def fabrica(self) -> FabricaColaboraciones:
        return self._fabrica

    def _to_str_id(self, id: UUID | str) -> str:
        return str(id)

    def obtener_por_id(self, id: UUID | str) -> Optional[Colaboracion]:
        """
        Devuelve la entidad de dominio o None si no existe.
        Acepta id como UUID o str.
        """
        try:
            dto = self.session.query(ColaboracionDTO).filter_by(id=self._to_str_id(id)).one()
        except NoResultFound:
            return None
        return self.fabrica.crear_objeto(dto, MapeadorColaboracionInfra())

    def obtener_todos(self) -> List[Colaboracion]:
        dtos = self.session.query(ColaboracionDTO).all()
        return [self.fabrica.crear_objeto(dto, MapeadorColaboracionInfra()) for dto in dtos]

    def agregar(self, colaboracion: Colaboracion):
        """
        Crea el DTO a partir de la entidad y lo añade a la sesión.
        No hace commit: la UoW es la responsable del commit.
        """
        dto: ColaboracionDTO = self.fabrica.crear_objeto(colaboracion, MapeadorColaboracionInfra())
        # Asegurar que el DTO tiene el id como string (por si la fábrica no lo puso)
        if getattr(dto, "id", None) is None:
            dto.id = self._to_str_id(colaboracion.id)
        self.session.add(dto)
        # no commit aquí (lo hace la UoW)

    def actualizar(self, colaboracion: Colaboracion):
        dto: ColaboracionDTO = self.fabrica.crear_objeto(colaboracion, MapeadorColaboracionInfra())
        if getattr(dto, "id", None) is None:
            dto.id = self._to_str_id(colaboracion.id)
        self.session.merge(dto)

    def eliminar(self, colaboracion_id: UUID | str):
        self.session.query(ColaboracionDTO).filter_by(id=self._to_str_id(colaboracion_id)).delete()


class RepositorioEventosColaboracionesSQLAlchemy(RepositorioEventosColaboraciones):
    def __init__(self, session: Optional[Session] = None):
        """
        Repositorio de eventos infra (persistencia de eventos).
        Recibe sesión en el constructor. Usa fallback a SessionLocal() si no se inyecta.
        """
        if session is None:
            try:
                from config.db import SessionLocal
                self.session = SessionLocal()
            except Exception:
                raise RuntimeError(
                    "No se inyectó una Session y no se pudo obtener SessionLocal desde config.db"
                )
        else:
            self.session = session

        self._fabrica: FabricaColaboraciones = FabricaColaboraciones()

    @property
    def fabrica(self) -> FabricaColaboraciones:
        return self._fabrica

    def _to_str_id(self, id: UUID | str) -> str:
        return str(id)

    def obtener_por_id(self, id: UUID | str):
        try:
            dto = self.session.query(EventoColaboracionDTO).filter_by(id=self._to_str_id(id)).one()
        except NoResultFound:
            return None
        return self.fabrica.crear_objeto(dto, MapeadorEventoColaboracionInfra())

    def obtener_todos(self) -> list:
        dtos = self.session.query(EventoColaboracionDTO).all()
        return [self.fabrica.crear_objeto(dto, MapeadorEventoColaboracionInfra()) for dto in dtos]

    def agregar(self, evento):
        """
        Convierte el evento a DTO infra y lo persiste.
        Se asume que `evento` tiene propiedades: id, id_colaboracion, fecha_creacion, etc.
        """
        evento_dto = self.fabrica.crear_objeto(evento, MapeadorEventoColaboracionInfra())

        # Serializar payload (se asume que evento_dto.data es el objeto a serializar)
        parser_payload = JsonSchema(evento_dto.data.__class__)
        json_bytes = parser_payload.encode(evento_dto.data)
        # JsonSchema.encode devuelve bytes; si necesitas string:
        try:
            json_str = json_bytes.decode("utf-8")
        except Exception:
            # fallback si ya es string
            json_str = str(json_bytes)

        evento_db = EventoColaboracionDTO()
        evento_db.id = str(getattr(evento, "id", evento_db.id))
        # id_entidad guarda la referencia a la entidad (colaboración)
        evento_db.id_entidad = str(getattr(evento, "id_colaboracion", getattr(evento, "id_entidad", None)))
        evento_db.fecha_evento = getattr(evento, "fecha_creacion", None)
        evento_db.version = str(getattr(evento_dto, "specversion", ""))
        evento_db.tipo_evento = evento.__class__.__name__
        evento_db.formato_contenido = "JSON"
        evento_db.nombre_servicio = str(getattr(evento_dto, "service_name", ""))
        evento_db.contenido = json_str

        self.session.add(evento_db)

    def actualizar(self, evento):
        raise NotImplementedError

    def eliminar(self, evento_id: UUID | str):
        self.session.query(EventoColaboracionDTO).filter_by(id=self._to_str_id(evento_id)).delete()
