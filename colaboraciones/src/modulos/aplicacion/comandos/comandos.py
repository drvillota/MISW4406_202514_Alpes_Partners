from dataclasses import dataclass
import uuid

from modulos.aplicacion.dto import ColaboracionDTO
from seedwork.aplicacion.comandos import Comando, ComandoHandler
from seedwork.aplicacion.comandos import ejecutar_commando as comando

from modulos.dominio.entidades import Colaboracion
from modulos.dominio.objetos_valor import CampaniaId, InfluencerId, Contrato, EstadoColaboracion
from modulos.aplicacion.mapeadores import MapeadorColaboracion
from modulos.infraestructura.repositorios import RepositorioColaboracionesSQLAlchemy, RepositorioEventosColaboracionesSQLAlchemy
from seedwork.infraestructura.uow import UnidadTrabajoPuerto
from datetime import datetime


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
        dto = ColaboracionDTO(
            id=str(uuid.uuid4()),
            id_campania=comando.id_campania,
            id_influencer=comando.id_influencer,
            contrato_url=comando.contrato_url,
            estado=EstadoColaboracion.PENDIENTE.value,
            fecha_creacion=datetime.utcnow().isoformat()
        )

        # Mapear DTO → Entidad de dominio
        colaboracion: Colaboracion = MapeadorColaboracion().dto_a_entidad(dto)

        repositorio = RepositorioColaboracionesSQLAlchemy()
        repositorio_eventos = RepositorioEventosColaboracionesSQLAlchemy()

        UnidadTrabajoPuerto.registrar_batch(
            repositorio.agregar,
            colaboracion,
            repositorio_eventos_func=repositorio_eventos.agregar
        )
        UnidadTrabajoPuerto.commit()


class ValidarContratoHandler(ComandoHandler):
    def handle(self, comando: ComandoValidarContrato):
        repositorio = RepositorioColaboracionesSQLAlchemy()
        colaboracion = repositorio.obtener_por_id(comando.id_colaboracion)

        colaboracion.validar_contrato()

        UnidadTrabajoPuerto.registrar_batch(repositorio.actualizar, colaboracion)
        UnidadTrabajoPuerto.commit()


class RechazarContratoHandler(ComandoHandler):
    def handle(self, comando: ComandoRechazarContrato):
        repositorio = RepositorioColaboracionesSQLAlchemy()
        colaboracion = repositorio.obtener_por_id(comando.id_colaboracion)

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
