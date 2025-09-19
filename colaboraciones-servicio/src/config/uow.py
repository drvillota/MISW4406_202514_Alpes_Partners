# colaboraciones/src/config/uow.py
from colaboraciones.src.modulos.infraestructura.uow import UnidadTrabajo, Batch
from sqlalchemy.orm import Session

class UnidadTrabajoSQLAlchemy(UnidadTrabajo):
    def __init__(self, session: Session):
        self.session = session
        self._batches = []

    def __enter__(self):
        # opcional: abrir savepoint/contexto
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            try:
                self.commit()
            except:
                self.rollback()
                raise

    def _limpiar_batches(self):
        self._batches = []

    @property
    def batches(self):
        return self._batches

    def registrar_batch(self, operacion, *args, lock=None, **kwargs):
        batch = Batch(operacion, lock, *args, **kwargs)
        self._batches.append(batch)
        # publicar eventos de dominio si corresponde (como antes)
        self._publicar_eventos_dominio(batch, kwargs.get("repositorio_eventos_func"))

    def commit(self):
        # ejecutar operaciones registradas (ej: repo.agregar)
        for batch in list(self._batches):
            batch.operacion(*batch.args, **batch.kwargs)

        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self._limpiar_batches()
            # publicar eventos post commit si tu UoW lo hace
            self._publicar_eventos_post_commit()

    def rollback(self, savepoint=None):
        # si savepoint: retornar a savepoint; si no, rollback whole tx
        self.session.rollback()
        self._limpiar_batches()

    def savepoint(self):
        # opcional: return self.session.begin_nested()
        return self.session.begin_nested()
