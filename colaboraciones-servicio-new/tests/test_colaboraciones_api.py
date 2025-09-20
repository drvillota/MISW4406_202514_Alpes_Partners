# tests/test_colaboraciones_api.py
import pytest
from fastapi.testclient import TestClient

# importa el router FastAPI
from api.v1.router import router as colaboraciones_router

# importa los módulos correctos (seedwork)
import seedwork.aplicacion.comandos as comandos_seedwork
import seedwork.aplicacion.queries as queries_seedwork

# y importa el módulo del router para parchar referencias locales también
import api.v1.router as api_mod

from modulos.aplicacion.dto import ColaboracionDTO


@pytest.fixture
def app(monkeypatch):
    from fastapi import FastAPI

    app = FastAPI()
    # monta el router tal como en tu main
    app.include_router(colaboraciones_router)
    
    # ---- mock ejecutar_comando (para que NO llame a los handlers reales) ----
    def fake_ejecutar_comando(cmd):
        print(f"[MOCK ejecutar_comando] {cmd}")
        return True

    # aplicar mock tanto al seedwork como al módulo router (donde fue importado)
    monkeypatch.setattr(comandos_seedwork, "ejecutar_commando", fake_ejecutar_comando)
    monkeypatch.setattr(api_mod, "ejecutar_commando", fake_ejecutar_comando)

    # ---- mock ejecutar_query ----
    class DummyResultado:
        def __init__(self, data):
            self.resultado = data

    def fake_ejecutar_query(q):
        # comprobar el tipo de query por nombre de clase (igual que en el test antiguo)
        if q.__class__.__name__ == "ObtenerColaboracion":
            return DummyResultado(
                CollaboracionDTO if False else ColaboracionDTO(  # for linters; actual usage below
                    id="col-123",
                    id_campania="camp-123",
                    id_influencer="inf-001",
                    estado="pendiente",
                    contrato_url="http://contratos.com/abc.pdf",
                    fecha_creacion="2024-01-01T00:00:00Z"
                )
            )
        else:
            return DummyResultado([
                ColaboracionDTO(
                    id="col-1", id_campania="camp-001", id_influencer="inf-111",
                    estado="validado", contrato_url="http://contratos.com/docX.pdf",
                    fecha_creacion="2024-01-01T00:00:00Z"
                ),
                ColaboracionDTO(
                    id="col-2", id_campania="camp-001", id_influencer="inf-222",
                    estado="pendiente", contrato_url="http://contratos.com/docY.pdf",
                    fecha_creacion="2024-01-01T00:00:00Z"
                )
            ])

    monkeypatch.setattr(queries_seedwork, "ejecutar_query", fake_ejecutar_query)
    monkeypatch.setattr(api_mod, "ejecutar_query", fake_ejecutar_query)

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_crear_colaboracion(client):
    payload = {
        "id_campania": "camp-001",
        "id_influencer": "inf-001",
        "contrato_url": "http://contratos.com/doc1.pdf"
    }
    resp = client.post("/colaboraciones", json=payload)
    assert resp.status_code == 202


def test_obtener_colaboracion(client):
    resp = client.get("/colaboraciones/col-123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "col-123"
    assert data["estado"] == "pendiente"


def test_listar_colaboraciones(client):
    resp = client.get("/colaboraciones?id_campania=camp-001")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert data[0]["estado"] in ["validado", "pendiente"]
