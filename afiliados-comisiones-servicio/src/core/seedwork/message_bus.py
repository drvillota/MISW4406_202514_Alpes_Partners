from __future__ import annotations
from typing import Callable, Dict, Type, Any
from .commands import Command
from .events import DomainEvent, event_bus

class MessageBus:
    def __init__(self):
        self._command_handlers: Dict[Type[Command], Callable[[Command], Any]] = {}

    def register_command(self, command_type: Type[Command], handler: Callable[[Command], Any]) -> None:
        self._command_handlers[command_type] = handler

    def handle_command(self, command: Command) -> Any:
        handler = self._command_handlers[type(command)]
        return handler(command)

bus = MessageBus()
