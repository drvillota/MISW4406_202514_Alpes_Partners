from __future__ import annotations
from typing import Callable, Dict, Type, Any
import logging
from .comandos import Comando
from .eventos import DomainEvent, event_bus

logger = logging.getLogger(__name__)

class MessageBus:
    def __init__(self):
        self._command_handlers: Dict[Type[Comando], Callable[[Comando], Any]] = {}

    def register_command(self, command_type: Type[Comando], handler: Callable[[Comando], Any]) -> None:
        logger.info(f"MessageBus: Registrando handler para {command_type}")
        self._command_handlers[command_type] = handler
        logger.info(f"MessageBus: Total handlers: {len(self._command_handlers)}")

    def handle_command(self, command: Comando) -> Any:
        command_type = type(command)
        logger.info(f"MessageBus: Buscando handler para {command_type}")
        logger.info(f"MessageBus: Handlers disponibles: {list(self._command_handlers.keys())}")
        
        if command_type not in self._command_handlers:
            logger.error(f"MessageBus: No handler encontrado para {command_type}")
            raise KeyError(f"No handler registered for {command_type}")
            
        handler = self._command_handlers[command_type]
        logger.info(f"MessageBus: Ejecutando handler {handler}")
        return handler(command)
bus = MessageBus()
