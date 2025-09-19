from pulsar.schema import *
from dataclasses import dataclass, field
from seedwork.infraestructura.schema.v1.comandos import ComandoIntegracion
from seedwork.infraestructura.utils import time_millis
import uuid


class CrearColaboracionPayload(Record):
    id_campania = String()
    id_influencer = String()
    contrato_url = String()
    fecha_creacion = Long()


class ValidarContratoPayload(Record):
    id_colaboracion = String()
    fecha_validacion = Long()


class RechazarContratoPayload(Record):
    id_colaboracion = String()
    motivo = String()
    fecha_rechazo = Long()


class ComandoCrearColaboracion(ComandoIntegracion):
    id = String(default=str(uuid.uuid4()))
    time = Long()
    ingestion = Long(default=time_millis())
    specversion = String(default="v1")
    type = String(default="CrearColaboracion")
    datacontenttype = String(default="JSON")
    service_name = String(default="marketing")
    data = CrearColaboracionPayload

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ComandoValidarContrato(ComandoIntegracion):
    id = String(default=str(uuid.uuid4()))
    time = Long()
    ingestion = Long(default=time_millis())
    specversion = String(default="v1")
    type = String(default="ValidarContrato")
    datacontenttype = String(default="JSON")
    service_name = String(default="marketing")
    data = ValidarContratoPayload

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ComandoRechazarContrato(ComandoIntegracion):
    id = String(default=str(uuid.uuid4()))
    time = Long()
    ingestion = Long(default=time_millis())
    specversion = String(default="v1")
    type = String(default="RechazarContrato")
    datacontenttype = String(default="JSON")
    service_name = String(default="marketing")
    data = RechazarContratoPayload

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
