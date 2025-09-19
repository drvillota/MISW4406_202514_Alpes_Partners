# src/modulos/aplicacion/comandos/comandos.py
from dataclasses import dataclass
import uuid
from datetime import datetime
from typing import Optional

from modulos.aplicacion.dto import ColaboracionDTO
from seedwork.aplicacion.comandos import Comando, ComandoHandler
from seedwork.aplicacion.comandos import ejecutar_commando as comando

from modulos.dominio.entidades import Colaboracion
from modulos.dominio.objetos_valor import EstadoColaboracion
from modulos.aplicacion.mapeadores import MapeadorColaboracion

# Repositorios infra que ahora aceptan opcionalmente una Session en el constructor
from modulos.infraestructura.repositorios import (
    RepositorioColaboracionesSQLAlchemy,
    RepositorioEventosColaboracionesSQLAlchemy,
)

# Puerto / helpers de UoW (unidad_de_trabajo() está en el mismo módulo — lo usamos para obtener la instancia)
from seedwork.infraestructura.uow import UnidadTrabajoPuerto, unidad_de_trabajo


# ---------- Comandos ----------
@dataclass
class ComandoCrearColaboracion(Comando):
    id_campania: str
    id_influencer: str
    contrato_url: str


@dataclass
class ComandoValidarContrato(Comando):
    id_colaboracion: str


@dataclass
class ComandoRechazarContrato(Comando):
    id_colaboracion: str
    motivo: str


# ---------- Handlers ----------
class CrearColaboracionHandler(ComandoHandler):
    def handle(self, comando: ComandoCrearColaboracion):
        # Creamos el DTO tal como antes
        dto = ColaboracionDTO(
            id=str(uuid.uuid4()),
            id_campania=comando.id_campania,
            id_influencer=comando.id_influencer,
            contrato_url=comando.contrato_url,
            estado=EstadoColaboracion.PENDIENTE.value,
            fecha_creacion=datetime.utcnow().isoformat(),
        )

        # Mapear DTO → Entidad de dominio
        colaboracion: Colaboracion = MapeadorColaboracion().dto_a_entidad(dto)

        # Obtener la UoW activa (si existe) para tomar su session
        uow = unidad_de_trabajo()  # devuelve la instancia actual (FastAPI/ContextVar o Flask)
        # intentamos extraer session si la UoW la expone (UnidadTrabajoSQLAlchemy debería exponerla)
        session = getattr(uow, "session", None)

        # Construir repositorios pasando la session (si es None, el repo puede usar su fallback)
        repositorio = RepositorioColaboracionesSQLAlchemy(session=session)
        repositorio_eventos = RepositorioEventosColaboracionesSQLAlchemy(session=session)

        # Registrar operación en la UoW (la UoW real se encargará de ejecutar el batch en commit)
        UnidadTrabajoPuerto.registrar_batch(
            repositorio.agregar,
            colaboracion,
            repositorio_eventos_func=repositorio_eventos.agregar,
        )
        UnidadTrabajoPuerto.commit()


class ValidarContratoHandler(ComandoHandler):
    def handle(self, comando: ComandoValidarContrato):
        uow = unidad_de_trabajo()
        session = getattr(uow, "session", None)

        repositorio = RepositorioColaboracionesSQLAlchemy(session=session)
        colaboracion = repositorio.obtener_por_id(comando.id_colaboracion)

        if colaboracion is None:
            raise ValueError(f"Colaboracion {comando.id_colaboracion} no encontrada")

        colaboracion.validar_contrato()

        UnidadTrabajoPuerto.registrar_batch(repositorio.actualizar, colaboracion)
        UnidadTrabajoPuerto.commit()


class RechazarContratoHandler(ComandoHandler):
    def handle(self, comando: ComandoRechazarContrato):
        uow = unidad_de_trabajo()
        session = getattr(uow, "session", None)

        repositorio = RepositorioColaboracionesSQLAlchemy(session=session)
        colaboracion = repositorio.obtener_por_id(comando.id_colaboracion)

        if colaboracion is None:
            raise ValueError(f"Colaboracion {comando.id_colaboracion} no encontrada")

        colaboracion.rechazar_contrato(comando.motivo)

        UnidadTrabajoPuerto.registrar_batch(repositorio.actualizar, colaboracion)
        UnidadTrabajoPuerto.commit()


# ---------- Registro de comandos ----------
@comando.register(ComandoCrearColaboracion)
def ejecutar_comando_crear_colaboracion(comando: ComandoCrearColaboracion):
    handler = CrearColaboracionHandler()
    handler.handle(comando)


@comando.register(ComandoValidarContrato)
def ejecutar_comando_validar_contrato(comando: ComandoValidarContrato):
    handler = ValidarContratoHandler()
    handler.handle(comando)


@comando.register(ComandoRechazarContrato)
def ejecutar_comando_rechazar_contrato(comando: ComandoRechazarContrato):
    handler = RechazarContratoHandler()
    handler.handle(comando)
