# tests/test_repositorio_colaboraciones.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from importlib import import_module

# usar rutas con src (tu proyecto usa ese namespace)
from config.db import Base, db
from modulos.dominio.entidades import Colaboracion
from modulos.infraestructura.repositorios import RepositorioColaboracionesSQLAlchemy
from modulos.dominio.objetos_valor import EstadoColaboracion


@pytest.fixture(scope="module")
def session():
    engine = create_engine("sqlite:///:memory:")

    # abrir conexión única que usaremos para todo el módulo (IMPORTANTE para SQLite in-memory)
    connection = engine.connect()

    # --- IMPORTAR MÓDULOS DE INFRA antes de create_all para registrar los modelos en Base.metadata
    # Esto asegura que las clases con __tablename__ se hayan definido y registrado en la misma MetaData.
    try:
        infra_dto = import_module("modulos.infraestructura.dto")
    except Exception:
        # si falla la importación deja que create_all falle después: lanzará error explicativo
        infra_dto = None

    # opcional: importar mapeadores/repositorios para registrar cualquier side-effect necesario
    try:
        import_module("modulos.infraestructura.mapeadores")
    except Exception:
        pass
    try:
        import_module("modulos.infraestructura.repositorios")
    except Exception:
        pass

    # --- comenzar la transacción ANTES de create_all (asegura que la sesión y las tablas
    # se creen sobre la misma conexión / transacción)
    transaction = connection.begin()

    # crear tablas sobre la MISMA conexión — así CREATE TABLE usa el mismo connection.
    Base.metadata.create_all(bind=connection)

    # vincular la sesión al mismo connection (no al engine)
    db.session = scoped_session(sessionmaker(bind=connection))

    try:
        yield db.session
    finally:
        # rollback y limpieza
        try:
            transaction.rollback()
        except Exception:
            pass
        connection.close()
        db.session.remove()


def test_repositorio_agregar_y_obtener(session):
    repo = RepositorioColaboracionesSQLAlchemy()

    colab = Colaboracion.crear(
        id_campania="camp-001",
        id_influencer="inf-001",
        contrato_url="http://contratos.com/abc.pdf"
    )
    colab.estado = EstadoColaboracion.PENDIENTE

    repo.agregar(colab)
    session.commit()

    recuperada = repo.obtener_por_id(colab.id)
    assert recuperada.id_campania.id == "camp-001"
    assert recuperada.estado.name == "PENDIENTE"
