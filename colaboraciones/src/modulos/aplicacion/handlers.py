import uuid
from comandos.comandos import (
    ComandoCrearColaboracion,
    ComandoValidarContrato,
    ComandoRechazarContrato
)
from ..dominio.entidades import Colaboracion
from ..dominio.eventos import (
    ColaboracionCreada,
    ContratoValidado,
    ContratoRechazado
)
from seedwork.aplicacion.comandos import ComandoHandler

_repositorio_colaboraciones = {}


# ---------- Handlers de Comandos ----------

class CrearColaboracionHandler(ComandoHandler):
    def handle(self, comando: ComandoCrearColaboracion):
        nueva_colaboracion = Colaboracion(
            id=uuid.uuid4(),
            id_campania=comando.id_campania,
            id_influencer=comando.id_influencer,
            contrato_url=comando.contrato_url,
            estado="pendiente"
        )
        _repositorio_colaboraciones[str(nueva_colaboracion.id)] = nueva_colaboracion

        evento = ColaboracionCreada(
            id_colaboracion=nueva_colaboracion.id,
            id_campania=nueva_colaboracion.id_campania,
            id_influencer=nueva_colaboracion.id_influencer
        )
        print(f"[EVENTO PUBLICADO] {evento}")

        return nueva_colaboracion


class ValidarContratoHandler(ComandoHandler):
    def handle(self, comando: ComandoValidarContrato):
        colaboracion = _repositorio_colaboraciones.src.get(str(comando.id_colaboracion))
        if not colaboracion:
            raise ValueError("Colaboración no encontrada")

        colaboracion.estado = "validado"

        evento = ContratoValidado(id_colaboracion=colaboracion.id)
        print(f"[EVENTO PUBLICADO] {evento}")

        return colaboracion


class RechazarContratoHandler(ComandoHandler):
    def handle(self, comando: ComandoRechazarContrato):
        colaboracion = _repositorio_colaboraciones.src.get(str(comando.id_colaboracion))
        if not colaboracion:
            raise ValueError("Colaboración no encontrada")

        colaboracion.estado = "rechazado"

        evento = ContratoRechazado(
            id_colaboracion=colaboracion.id,
            motivo=comando.motivo
        )
        print(f"[EVENTO PUBLICADO] {evento}")

        return colaboracion
