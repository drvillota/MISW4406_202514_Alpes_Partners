# src/colaboraciones/config/uow.py
from config.db import db
from seedwork.dominio.entidades import AgregacionRaiz
from seedwork.infraestructura.uow import UnidadTrabajo, Batch
from pydispatch import dispatcher

import logging
import traceback
from datetime import datetime

class ExcepcionUoW(Exception):
    ...


class UnidadTrabajoSQLAlchemy(UnidadTrabajo):

    def __init__(self):
        self._batches: list[Batch] = list()

    def __enter__(self) -> UnidadTrabajo:
        return super().__enter__()

    def __exit__(self, *args):
        # al salir, revertir si necesario
        self.rollback()

    def _limpiar_batches(self):
        self._batches = list()

    @property
    def savepoints(self) -> list:
        # Implementación básica: no hay savepoints administrados actualmente
        return []

    @property
    def batches(self) -> list[Batch]:
        return self._batches

    def commit(self):
        # ejecutar operaciones registradas (ej: repositorio.agregar)
        for batch in list(self.batches):
            try:
                batch.operacion(*batch.args, **batch.kwargs)
            except Exception:
                logging.exception("Error ejecutando operación de batch en commit")
                # si falla ejecutar op -> hacer rollback
                self.rollback()
                raise

        # confirmar transacción DB
        try:
            db.session.commit()
        except Exception:
            logging.exception("Error en db.session.commit()")
            db.session.rollback()
            raise

        # publicar eventos post-commit (UnidadTrabajo.commit() en la superclase lo hace)
        super().commit()

    def rollback(self, savepoint=None):
        # si tenemos savepoint -> revertir, sino rollback de sesión
        if savepoint:
            try:
                savepoint.rollback()
            except Exception:
                logging.exception("Error al rollbackear savepoint")
        else:
            try:
                db.session.rollback()
            except Exception:
                logging.exception("Error en db.session.rollback()")

        super().rollback()

    def savepoint(self):
        # TODO: implementar si necesitas savepoints (Postgres/MySQL)
        raise NotImplementedError


class UnidadTrabajoPulsar(UnidadTrabajo):

    def __init__(self):
        self._batches: list[Batch] = list()

    def __enter__(self) -> UnidadTrabajo:
        return super().__enter__()

    def __exit__(self, *args):
        self.rollback()

    def _limpiar_batches(self):
        self._batches = list()

    @property
    def savepoints(self) -> list:
        return []

    @property
    def batches(self) -> list[Batch]:
        return self._batches

    def commit(self):
        """
        Para la UoW tipo 'pulsar' enviamos los eventos de integración.
        Si hay error al enviar (a la mitad), enviamos eventos de compensación
        de los que ya fueron publicados.
        """
        published = 0
        try:
            for evento in self._obtener_eventos():
                dispatcher.send(signal=f'{type(evento).__name__}Integracion', evento=evento)
                published += 1
        except Exception:
            logging.error('ERROR: enviando eventos integracion (Pulsar UoW)!')
            traceback.print_exc()
            # hacemos rollback de compensaciones para lo publicado
            self.rollback(index=published)
            raise

        # si todo ok, limpiar batches
        self._limpiar_batches()
        # No llamamos a super().commit() porque en la UoW Pulsar ya enviamos integracion.
        # Pero llamamos a _publicar_eventos_post_commit si queremos señal adicional:
        # super().commit()  # <-- opcional si quieres que se envíe otra señal
        # en este diseño _publicar_eventos_post_commit ya fue ejecutado al llamar super().commit()

    def rollback(self, index: int = None, savepoint=None):
        """
        En rollback para Pulsar enviamos eventos de compensación (si existen)
        Sólo consideramos los eventos que fueron publicados (index) si se provee.
        """
        try:
            if index is None:
                eventos_comp = self._obtener_eventos_rollback()
            else:
                # publicar compensaciones sólo para los primeros `index` eventos
                # recolectamos los eventos y tomamos los primeros `index`
                todos = self._obtener_eventos()
                publicados = todos[:index]
                # construir una lista de batches que contienen esos eventos publicados
                # (aproximación simple: buscar batches que contengan agregación con esos eventos)
                batches_publicados = []
                for batch in self.batches:
                    for arg in batch.args:
                        if isinstance(arg, AgregacionRaiz):
                            # si alguno de los eventos publicados pertenece a esta agregación
                            if any(e in arg.eventos for e in publicados):
                                batches_publicados.append(batch)
                                break
                eventos_comp = self._obtener_eventos_rollback(batches=batches_publicados)

            for ev in eventos_comp:
                try:
                    dispatcher.send(signal=f'{type(ev).__name__}Compensacion', evento=ev)
                except Exception:
                    logging.exception("Error enviando evento de compensación")

        except Exception:
            logging.exception("Error creando/ejecutando rollback Pulsar")

        # limpiar batches y terminar
        self._limpiar_batches()
        super().rollback()

    def savepoint(self):
        # NOTE: No se implementa para Event-driven UoW
        raise NotImplementedError
