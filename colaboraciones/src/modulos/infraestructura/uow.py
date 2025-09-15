# src/colaboraciones/modulos/infraestructura/uow.py
from abc import ABC, abstractmethod
from enum import Enum
from contextvars import ContextVar
from typing import Optional, List

from seedwork.dominio.entidades import AgregacionRaiz
from pydispatch import dispatcher

import pickle
import logging
import traceback


# ContextVar para entornos async/non-flask (FastAPI)
_CTX_UOW: ContextVar[Optional[object]] = ContextVar("_CTX_UOW", default=None)


class Lock(Enum):
    OPTIMISTA = 1
    PESIMISTA = 2


class Batch:
    def __init__(self, operacion, lock: Lock, *args, **kwargs):
        self.operacion = operacion
        self.args = args
        self.lock = lock
        self.kwargs = kwargs


class UnidadTrabajo(ABC):

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    def _obtener_eventos_rollback(self, batches=None):
        batches = self.batches if batches is None else batches
        eventos = list()
        for batch in batches:
            for arg in batch.args:
                if isinstance(arg, AgregacionRaiz):
                    eventos += arg.eventos_compensacion
                    break
        return eventos

    def _obtener_eventos(self, batches=None):
        batches = self.batches if batches is None else batches
        eventos = list()
        for batch in batches:
            for arg in batch.args:
                if isinstance(arg, AgregacionRaiz):
                    eventos += arg.eventos
                    break
        return eventos

    @abstractmethod
    def _limpiar_batches(self):
        raise NotImplementedError

    @abstractmethod
    def batches(self) -> List[Batch]:
        raise NotImplementedError

    @abstractmethod
    def savepoints(self) -> list:
        raise NotImplementedError

    def commit(self):
        # publicamos eventos post-commit y limpiamos
        self._publicar_eventos_post_commit()
        self._limpiar_batches()

    @abstractmethod
    def rollback(self, savepoint=None):
        self._limpiar_batches()

    @abstractmethod
    def savepoint(self):
        raise NotImplementedError

    def registrar_batch(self, operacion, *args, lock=Lock.PESIMISTA, repositorio_eventos_func=None, **kwargs):
        batch = Batch(operacion, lock, *args, **kwargs)
        self.batches.append(batch)
        self._publicar_eventos_dominio(batch, repositorio_eventos_func)

    def _publicar_eventos_dominio(self, batch, repositorio_eventos_func):
        for evento in self._obtener_eventos(batches=[batch]):
            if repositorio_eventos_func:
                try:
                    repositorio_eventos_func(evento)
                except Exception:
                    logging.exception("Error guardando evento en repo eventos")
            dispatcher.send(signal=f'{type(evento).__name__}Dominio', evento=evento)

    def _publicar_eventos_post_commit(self):
        try:
            for evento in self._obtener_eventos():
                dispatcher.send(signal=f'{type(evento).__name__}Integracion', evento=evento)
        except:
            logging.error('ERROR: enviando eventos post-commit!')
            traceback.print_exc()


# -------------------------
# Helpers para multi-framework
# -------------------------
def is_flask():
    try:
        # detecta flask import disponible en runtime
        from flask import session  # type: ignore
        return True
    except Exception:
        return False


def registrar_unidad_de_trabajo(serialized_obj_or_instance):
    """
    Guarda la UoW en el store correspondiente:
     - si estamos en Flask -> guarda el objeto serializado (pickle) en session['uow']
     - si no -> guarda la instancia en ContextVar
    `serialized_obj_or_instance` puede ser bytes (pickle) o la instancia ya creada.
    """
    if is_flask():
        from flask import session  # type: ignore
        # si llega instancia, la serializamos para mantener compatibilidad histórica
        if not isinstance(serialized_obj_or_instance, (bytes, bytearray)):
            serialized = pickle.dumps(serialized_obj_or_instance)
        else:
            serialized = serialized_obj_or_instance
        session['uow'] = serialized
    else:
        # si llega pickled bytes -> deserializar; si es instancia -> set
        if isinstance(serialized_obj_or_instance, (bytes, bytearray)):
            try:
                inst = pickle.loads(serialized_obj_or_instance)
                _CTX_UOW.set(inst)
            except Exception:
                # si falla deserializar, no hacemos nada
                logging.exception("No se pudo desempaquetar UoW en registrar_unidad_de_trabajo")
        else:
            _CTX_UOW.set(serialized_obj_or_instance)


def flask_uow():
    """Mantener compatibilidad hacia atrás: devuelve pickled uow bytes si se usa Flask session."""
    from flask import session  # type: ignore
    if session.get('uow'):
        return session['uow']

    # serializar una UoW por defecto (SQLAlchemy) y guardar en session
    from config.uow import UnidadTrabajoSQLAlchemy, UnidadTrabajoPulsar  # import local para evitar ciclos
    uow_inst = UnidadTrabajoSQLAlchemy()
    serialized = pickle.dumps(uow_inst)
    if session.get('uow_metodo') == 'pulsar':
        serialized = pickle.dumps(UnidadTrabajoPulsar())
    registrar_unidad_de_trabajo(serialized)
    return serialized


def unidad_de_trabajo() -> UnidadTrabajo:
    """
    Retorna la UoW activa:
     - si estamos en Flask: deserializa y devuelve la instancia desde session
     - si no: usa ContextVar y crea la instancia (SQLAlchemy o Pulsar) basada en
       get_current_uow_metodo() si existe en tu router (opcional)
    """
    if is_flask():
        # compatibilidad existing
        return pickle.loads(flask_uow())

    # non-flask / async context: obtener UoW del ContextVar
    uow = _CTX_UOW.get()
    if uow is None:
        # intentar decidir tipo consultando al router (si existe)
        metodo = None
        try:
            from api.v1.router import get_current_uow_metodo  # may not exist
            metodo = get_current_uow_metodo()
        except Exception:
            metodo = None

        # instanciar la clase apropiada (importar aquí para evitar ciclos)
        from config.uow import UnidadTrabajoSQLAlchemy, UnidadTrabajoPulsar
        if metodo == 'pulsar':
            uow = UnidadTrabajoPulsar()
        else:
            uow = UnidadTrabajoSQLAlchemy()

        _CTX_UOW.set(uow)
    return uow


def guardar_unidad_trabajo(uow: UnidadTrabajo):
    """
    Guarda la instancia en el lugar adecuado (session o ContextVar).
    Usa esto después de modificar o commitear la UoW para persistir estado.
    """
    if is_flask():
        registrar_unidad_de_trabajo(pickle.dumps(uow))
    else:
        _CTX_UOW.set(uow)


# -------------------------
# Puerto para la aplicación
# -------------------------
class UnidadTrabajoPuerto:

    @staticmethod
    def commit():
        uow = unidad_de_trabajo()
        uow.commit()
        guardar_unidad_trabajo(uow)

    @staticmethod
    def rollback(savepoint=None):
        uow = unidad_de_trabajo()
        uow.rollback(savepoint=savepoint)
        guardar_unidad_trabajo(uow)

    @staticmethod
    def savepoint():
        uow = unidad_de_trabajo()
        uow.savepoint()
        guardar_unidad_trabajo(uow)

    @staticmethod
    def dar_savepoints():
        uow = unidad_de_trabajo()
        return uow.savepoints()

    @staticmethod
    def registrar_batch(operacion, *args, lock=Lock.PESIMISTA, **kwargs):
        uow = unidad_de_trabajo()
        uow.registrar_batch(operacion, *args, lock=lock, **kwargs)
        guardar_unidad_trabajo(uow)
