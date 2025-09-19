# tests/test_crear_colaboracion_handler.py
import pytest

from modulos.aplicacion.comandos.comandos import (
    ComandoCrearColaboracion,
    CrearColaboracionHandler,
)
from modulos.dominio.entidades import Colaboracion


def test_handler_crear_colaboracion(monkeypatch):
    # --- Fake repositorio (no DB) ---
    class FakeRepositorio:
        def __init__(self):
            self.entidad = None

        def agregar(self, entidad):
            # el handler registra repo.agregar en la UoW; aquí simulamos que se ejecuta
            self.entidad = entidad

        def actualizar(self, entidad): ...
        def eliminar(self, id): ...
        def obtener_por_id(self, id): return None
        def obtener_todos(self): return []

    fake_repo = FakeRepositorio()

    # --- Fake Unidad de Trabajo que SIMULA comportamiento real (ejecuta el batch) ---
    class FakeUOW:
        @staticmethod
        def registrar_batch(func, *args, **kwargs):
            """
            El handler en tu código hace:
              UnidadTrabajoPuerto.registrar_batch(repo.agregar, colaboracion, repositorio_eventos_func=...)
            Simulamos ejecutar inmediatamente la función para que fake_repo.entidad quede poblada.
            Aceptamos *args/**kwargs para ser compatibles con distintos usos.
            """
            # normalmente el primer arg será la entidad
            entidad = args[0] if args else kwargs.get("entidad")
            func(entidad)
            FakeUOW._last = {"func": func, "args": args, "kwargs": kwargs}

        @staticmethod
        def commit():
            FakeUOW._committed = True
            return True

    # --- Parcheos EN EL MÓDULO DEL HANDLER (crucial) ---
    # parchear las clases/objetos que el handler crea/usa dentro de SU MÓDULO
    module_path = "modulos.aplicacion.comandos.comandos"
    monkeypatch.setattr(f"{module_path}.RepositorioColaboracionesSQLAlchemy", lambda: fake_repo)
    monkeypatch.setattr(f"{module_path}.RepositorioEventosColaboracionesSQLAlchemy", lambda: fake_repo)
    monkeypatch.setattr(f"{module_path}.UnidadTrabajoPuerto", FakeUOW)

    # parchear UnidadTrabajoPuerto (el handler usa UnidadTrabajoPuerto.registrar_batch/commit)
    monkeypatch.setattr(f"{module_path}.UnidadTrabajoPuerto", FakeUOW)

    # --- Ejecutar comando/handler ---
    comando = ComandoCrearColaboracion(
        id_campania="camp-001",
        id_influencer="inf-001",
        contrato_url="http://contratos.com/abc.pdf"
    )

    handler = CrearColaboracionHandler()
    handler.handle(comando)

    # --- Aserciones ---
    assert isinstance(fake_repo.entidad, Colaboracion)

    camp_id = fake_repo.entidad.id_campania
    inf_id = fake_repo.entidad.id_influencer

    # comprobaciones flexibles para distintos diseños de VO (id/valor/value/str)
    if hasattr(camp_id, "id"):
        assert camp_id.id == "camp-001"
    else:
        assert str(camp_id) == "camp-001"

    if hasattr(inf_id, "id"):
        assert inf_id.id == "inf-001"
    else:
        assert str(inf_id) == "inf-001"

    assert getattr(FakeUOW, "_committed", False) is True
