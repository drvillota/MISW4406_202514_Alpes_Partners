# colaboraciones\src\main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import List

from config.api import app_configs
from api.v1.router import router as v1

# consumidores / eventos / comandos / despachador según tu estructura
from modulos.infraestructura.consumidores import suscribirse_a_topico
from modulos.infraestructura.v1.eventos import (
    ColaboracionCreadaPayload,
    ContratoValidadoPayload,
    ContratoRechazadoPayload,
    EventoColaboracion,
)
from modulos.infraestructura.v1.comandos import (
    ComandoCrearColaboracion,
    ComandoValidarContrato,
    ComandoRechazarContrato,
)
from modulos.infraestructura.despachadores import Despachador
from seedwork.infraestructura import utils
from fastapi import Request
from config.uow import UnidadTrabajoSQLAlchemy
from modulos.infraestructura.uow import set_current_uow, clear_current_uow

import asyncio

# -------------------------------------------------------
# Lifespan: arrancar consumidores en background (startup)
# y cancelarlos en shutdown
# -------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks: List[asyncio.Task] = []

    # Evitar arrancar consumidores durante tests: usa app_configs.env == "test"
    if getattr(app_configs, "env", "").lower() != "test":
        try:
            # Suscribirse a tópicos relevantes para colaboraciones
            # Ajusta los nombres de tópico/subscriber si usas otros
            tasks.append(asyncio.create_task(
                suscribirse_a_topico("evento-colaboraciones", "sub-colaboraciones-eventos", EventoColaboracion)
            ))
            tasks.append(asyncio.create_task(
                suscribirse_a_topico("comando-crear-colaboracion", "sub-com-crear-colab", ComandoCrearColaboracion)
            ))
            tasks.append(asyncio.create_task(
                suscribirse_a_topico("comando-validar-contrato", "sub-com-validar-contrato", ComandoValidarContrato)
            ))
            tasks.append(asyncio.create_task(
                suscribirse_a_topico("comando-rechazar-contrato", "sub-com-rechazar-contrato", ComandoRechazarContrato)
            ))
        except Exception as exc:
            # opcional: loggear aquí, no interrumpir startup por fallo en una suscripción
            # import logging; logging.exception("Error arrancando consumidores: %s", exc)
            pass

    # startup completed
    yield

    # shutdown: cancelar y esperar tareas (evita warnings y fugas)
    if tasks:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


# -------------------------------------------------------
# App FastAPI (una sola vez, con lifespan)
# -------------------------------------------------------
app = FastAPI(lifespan=lifespan, **app_configs)

@app.middleware("http")
async def uow_middleware(request: Request, call_next):
    # crear UoW nueva por request
    uow = UnidadTrabajoSQLAlchemy()
    set_current_uow(uow)

    try:
        response = await call_next(request)
        # commit si todo salió bien
        uow.commit()
        return response
    except Exception:
        # rollback si hubo error
        uow.rollback()
        raise
    finally:
        # limpiar ContextVar para no “ensuciar” requests posteriores
        clear_current_uow()
        
# Health simple
@app.get("/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}

# Opcional: endpoints de prueba para publicar eventos/comandos (útiles en desarrollo)
@app.get("/prueba-colaboracion-creada", include_in_schema=False)
async def prueba_colaboracion_creada() -> dict:
    # Construye un payload mínimo; adapta los atributos a los dataclasses que uses.
    payload = ColaboracionCreadaPayload(
        id="camp-xxx-inf-yyy",  # ajusta campos reales
        id_campania="camp-001",
        id_influencer="inf-001",
        contrato_url="http://contratos/doc.pdf",
        fecha_creacion=utils.time_millis(),
    )
    evento = EventoColaboracion(
        time=utils.time_millis(),
        ingestion=utils.time_millis(),
        datacontenttype=ColaboracionCreadaPayload.__name__,
        data=payload
    )
    desp = Despachador()
    desp.publicar_mensaje(evento, "evento-colaboraciones")
    return {"status": "ok"}

# incluir tu router (APIRouter) con las rutas ya convertidas a FastAPI
app.include_router(v1, prefix="/v1", tags=["Version 1"])
