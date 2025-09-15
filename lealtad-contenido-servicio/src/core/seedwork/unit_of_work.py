from __future__ import annotations
from contextlib import AbstractContextManager
from typing import Protocol

class UnitOfWork(AbstractContextManager):
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory
        self.session = None

    def __enter__(self):
        self.session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
