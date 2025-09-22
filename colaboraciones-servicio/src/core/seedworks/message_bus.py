from __future__ import annotations
from typing import Callable, Dict, Type, Any
import logging
from .comandos import Comando
from .eventos import EventoDominio, event_bus

logger = logging.getLogger(__name__)


class MessageBus:
    def __init__(self):
        self._command_handlers: Dict[Type[Comando], Callable[[Comando], Any]] = {}
        self._event_handlers: Dict[Type[EventoDominio], list[Callable[[EventoDominio], Any]]] = {}

    # ==========================
    # Comandos
    # ==========================
    def register_command(self, command_type: Type[Comando], handler: Callable[[Comando], Any]) -> None:
        logger.info(f"MessageBus: Registrando handler de comando para {command_type}")
        self._command_handlers[command_type] = handler
        logger.info(f"MessageBus: Total handlers de comandos: {len(self._command_handlers)}")

    def handle_command(self, command: Comando) -> Any:
        command_type = type(command)
        logger.info(f"MessageBus: Buscando handler de comando para {command_type}")
        logger.info(f"MessageBus: Handlers de comandos disponibles: {list(self._command_handlers.keys())}")

        if command_type not in self._command_handlers:
            logger.error(f"MessageBus: No handler de comando encontrado para {command_type}")
            raise KeyError(f"No handler registered for {command_type}")

        handler = self._command_handlers[command_type]
        logger.info(f"MessageBus: Ejecutando handler de comando {handler}")
        return handler(command)

    # ==========================
    # Eventos
    # ==========================
    def register_event(self, event_type: Type[EventoDominio], handler: Callable[[EventoDominio], Any]) -> None:
        logger.info(f"MessageBus: Registrando handler de evento para {event_type}")
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.info(f"MessageBus: Total handlers de eventos para {event_type}: {len(self._event_handlers[event_type])}")

    def handle_event(self, event: EventoDominio) -> None:
        event_type = type(event)
        logger.info(f"MessageBus: Buscando handlers de evento para {event_type}")
        handlers = self._event_handlers.get(event_type, [])

        if not handlers:
            logger.warning(f"MessageBus: No hay handlers registrados para evento {event_type}")
            return

        for handler in handlers:
            try:
                logger.info(f"MessageBus: Ejecutando handler de evento {handler}")
                handler(event)
            except Exception as e:
                logger.error(f"Error en handler {handler} para evento {event_type}: {e}")

    # ==========================
    # Publicación a event_bus
    # ==========================
    def publicar_evento(self, evento: Any) -> None:
        """Publicar evento hacia el bus de integración (ej. Pulsar)"""
        try:
            event_type = type(evento).__name__
            payload = evento.__dict__ if hasattr(evento, "__dict__") else dict(evento)

            logger.info(f"MessageBus: Publicando evento {event_type}")
            logger.debug(f"MessageBus: Payload -> {payload}")

            event_bus.publicar(payload)

        except Exception as e:
            logger.error(f"Error publicando evento {type(evento).__name__}: {e}")


# Instancia global
bus = MessageBus()
