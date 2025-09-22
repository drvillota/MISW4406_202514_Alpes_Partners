# colaboraciones/tests/test_crear_colaboracion_handler_integration.py
import pytest
from importlib import import_module
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# NOTA: no importes aún repositorios/handlers que usen db/session; lo haremos después
# importamos Base desde tu módulo de configuración
import config.db as config_db
from config.db import Base

@pytest.fixture(scope="module")
def db_session():
    """
    Fixture que prepara una DB sqlite:///:memory: y asegura que todos los módulos
    usen la sesión/connection creadas aquí.
    """

    # 1) crear engine/connection/transaction únicos para todo el módulo
    engine = create_engine("sqlite:///:memory:", future=True)
    connection = engine.connect()
    transaction = connection.begin()  # mantiene todo en una sola transacción

    # 2) configurar SessionLocal y db.session EN config_db antes de importar modelos/repos
    #    de esta forma los módulos que hacen `from config.db import SessionLocal`
    #    o `from config.db import db` usarán esta sesión.
    session_factory = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    # Si tu config_db exporta SessionLocal como un sessionmaker, reemplázalo:
    config_db.SessionLocal = session_factory
    # Algunas partes del proyecto pueden esperar `config_db.db.session` (Flask-SQLAlchemy style).
    # Creamos un objeto mínimo `db` con .session apuntando al scoped_session sobre la misma connection.
    config_db.db = SimpleNamespace(session=scoped_session(session_factory))

    # 3) ahora importar los módulos que registran modelos en Base.metadata
    #    (asegúrate que en esos módulos hagan `from config.db import Base`).
    import_module("modulos.infraestructura.dto")
    # opcional: importar repositorios/mapeadores si registran cosas en el import time
    try:
        import_module("modulos.infraestructura.repositorios")
    except Exception:
        # puede fallar si repositorios hacen cosas con recursos externos; ignoramos aquí
        pass

    # 4) crear tablas usando la misma conexión
    Base.metadata.create_all(bind=connection)

    # 5) entregar la sesión (scoped_session) para uso en pruebas si se requiere
    try:
        yield config_db.db.session
    finally:
        # teardown: rollback + cerrar conexión
        try:
            transaction.rollback()
        except Exception:
            pass
        connection.close()
        # si usamos scoped_session, remover
        try:
            config_db.db.session.remove()
        except Exception:
            pass


def test_handler_crear_colaboracion_integration(monkeypatch, db_session):
    """
    Test de integración que:
      - usa Repositorio real (SQLAlchemy) sobre sqlite in-memory,
      - usa UnidadTrabajoSQLAlchemy real (commits sobre db.session configurada arriba),
      - ejecuta el handler real (sin mocks de repositorio).
    """

    # Importar las clases AHORA (después del setup del fixture).
    from config.uow import UnidadTrabajoSQLAlchemy
    from modulos.aplicacion.comandos.comandos import (
        ComandoCrearColaboracion,
        CrearColaboracionHandler,
    )
    from modulos.infraestructura.repositorios import RepositorioColaboracionesSQLAlchemy

    # Crear la UoW real (usa config_db.db.session internamente si tu UoW está implementada así)
    real_uow = UnidadTrabajoSQLAlchemy()

    # Adapter mínimo para exponer la interfaz que el handler espera (UnidadTrabajoPuerto)
    class UOWAdapter:
        @staticmethod
        def registrar_batch(func, *args, **kwargs):
            return real_uow.registrar_batch(func, *args, **kwargs)

        @staticmethod
        def commit():
            return real_uow.commit()

        @staticmethod
        def rollback(savepoint=None):
            return real_uow.rollback(savepoint=savepoint)

        @staticmethod
        def savepoint():
            return real_uow.savepoint()

    # Parchear UnidadTrabajoPuerto en el módulo donde el handler lo usa.
    module_path = "modulos.aplicacion.comandos.comandos"
    monkeypatch.setattr(f"{module_path}.UnidadTrabajoPuerto", UOWAdapter)

    # Ejecutar handler real
    comando = ComandoCrearColaboracion(
        id_campania="camp-INT-001",
        id_influencer="inf-INT-001",
        contrato_url="http://contratos.local/abc.pdf"
    )
    handler = CrearColaboracionHandler()
    handler.handle(comando)

    # Confirmar que la entidad quedó persistida usando el repo real
    repo = RepositorioColaboracionesSQLAlchemy()
    todas = repo.obtener_todos()

    assert any(
        getattr(c.id_influencer, "id", str(c.id_influencer)) in ("inf-INT-001",)
        for c in todas
    )
