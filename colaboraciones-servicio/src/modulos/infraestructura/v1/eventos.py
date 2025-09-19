from pulsar.schema import *
from seedwork.infraestructura.schema.v1.eventos import EventoIntegracion
from seedwork.infraestructura.utils import time_millis
import uuid


class ColaboracionCreadaPayload(Record):
    id_colaboracion = String()
    id_campania = String()
    id_influencer = String()
    contrato_url = String()
    fecha_creacion = Long()


class ContratoValidadoPayload(Record):
    id_colaboracion = String()
    fecha_validacion = Long()


class ContratoRechazadoPayload(Record):
    id_colaboracion = String()
    motivo = String()
    fecha_rechazo = Long()


class EventoColaboracion(EventoIntegracion):
    id = String(default=str(uuid.uuid4()))
    time = Long()
    ingestion = Long(default=time_millis())
    specversion = String(default="v1")
    type = String(default="EventoColaboracion")
    datacontenttype = String(default="JSON")
    service_name = String(default="marketing")

    colaboracion_creada = ColaboracionCreadaPayload
    contrato_validado = ContratoValidadoPayload
    contrato_rechazado = ContratoRechazadoPayload

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
