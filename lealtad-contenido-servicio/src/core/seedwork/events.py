from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Type, Callable, Dict, Any, DefaultDict
from collections import defaultdict
import uuid

class DomainEvent:
    name: str
    occurred_on: datetime
    def __init__(self, name: str):
        self.name = name
        self.occurred_on = datetime.utcnow()

class HasDomainEvents:
    def __init__(self) -> None:
        self._domain_events: List[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pull_events(self) -> List[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

class EventBus:
    def __init__(self) -> None:
        self._handlers: DefaultDict[Type[DomainEvent], List[Callable[[DomainEvent], None]]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for etype, handlers in self._handlers.items():
            if isinstance(event, etype):
                for h in handlers:
                    h(event)

event_bus = EventBus()
