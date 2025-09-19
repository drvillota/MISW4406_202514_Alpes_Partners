from dataclasses import dataclass
import uuid

from seedwork.aplicacion.queries import Query, QueryHandler, QueryResultado
from seedwork.aplicacion.queries import ejecutar_query as query


# ---------- Definiciones de Queries ----------

@dataclass
class ObtenerColaboracion(Query):
    id: uuid.UUID


@dataclass
class ListarColaboracionesPorCampania(Query):
    id_campania: uuid.UUID


# ---------- Handlers ----------

class ObtenerColaboracionHandler(QueryHandler):
    def handle(self, query: ObtenerColaboracion) -> QueryResultado:
        # Simulación sin DB
        colaboracion_mock = {
            "id": str(query.id),
            "id_campania": "camp-123",
            "id_influencer": "inf-456",
            "estado": "pendiente",
            "contrato_url": "http://contratos.com/abc.pdf"
        }
        return QueryResultado(resultado=colaboracion_mock)


class ListarColaboracionesPorCampaniaHandler(QueryHandler):
    def handle(self, query: ListarColaboracionesPorCampania) -> QueryResultado:
        # Simulación sin DB
        colaboraciones_mock = [
            {"id": "col-1", "id_campania": str(query.id_campania), "id_influencer": "inf-111", "estado": "validado"},
            {"id": "col-2", "id_campania": str(query.id_campania), "id_influencer": "inf-222", "estado": "pendiente"},
        ]
        return QueryResultado(resultado=colaboraciones_mock)


# ---------- Registro de queries ----------

@query.register(ObtenerColaboracion)
def ejecutar_query_obtener_colaboracion(query: ObtenerColaboracion):
    handler = ObtenerColaboracionHandler()
    return handler.handle(query)


@query.register(ListarColaboracionesPorCampania)
def ejecutar_query_listar_colaboraciones(query: ListarColaboracionesPorCampania):
    handler = ListarColaboracionesPorCampaniaHandler()
    return handler.handle(query)
