from dataclasses import dataclass, field
from .reglas import IdEntidadEsInmutable
from .excepciones import IdDebeSerInmutableExcepcion
from datetime import datetime
from typing import List, Type, Callable, DefaultDict
from collections import defaultdict
import uuid

@dataclass
class EventoDominio():
    id: uuid.UUID = field(hash=True)
    _id: uuid.UUID = field(init=False, repr=False, hash=True)
    fecha_evento: datetime =  field(default=datetime.now())


    @classmethod
    def siguiente_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id: uuid.UUID) -> None:
        if not IdEntidadEsInmutable(self).es_valido():
            raise IdDebeSerInmutableExcepcion()
        self._id = self.siguiente_id()

class HasDomainEvents:
    def __init__(self) -> None:
        self._domain_events: List[EventoDominio] = []

    def record_event(self, event: EventoDominio) -> None:
        self._domain_events.append(event)

    def pull_events(self) -> List[EventoDominio]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

class EventBus:
    def __init__(self) -> None:
        self._handlers: DefaultDict[Type[EventoDominio], List[Callable[[EventoDominio], None]]] = defaultdict(list)

    def subscribe(self, event_type: Type[EventoDominio], handler: Callable[[EventoDominio], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: EventoDominio) -> None:
        for etype, handlers in self._handlers.items():
            if isinstance(event, etype):
                for h in handlers:
                    h(event)

event_bus = EventBus()
