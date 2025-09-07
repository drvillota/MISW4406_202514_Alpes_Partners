from __future__ import annotations
import asyncio
from fastapi import FastAPI
from ..infrastructure.config import UVICORN_PORT
from ..infrastructure.db.sqlalchemy import Base, engine, SessionLocal
from ..infrastructure.db.repositories import AfiliadoRepoSQL, ConversionRepoSQL, ComisionRepoSQL
from ..infrastructure.messaging.publisher import IntegracionPublisher
from ..application.handlers import register_handlers
from ..entrypoints.fastapi.routes import router
import uvicorn

app = FastAPI(title="Afiliados — Comisiones por Evento (DDD/EDA/Hex)")
app.include_router(router)

# Exponer handler de consulta para rutas (ver ruta GET)
query_handler = None

@app.on_event("startup")
async def on_startup():
    # Crear tablas (demo)
    Base.metadata.create_all(bind=engine)

    # Instancias repos
    session = SessionLocal()
    repo_afiliados = AfiliadoRepoSQL(session)
    repo_conversions = ConversionRepoSQL(session)
    repo_comisiones = ComisionRepoSQL(session)

    # Publisher de integración
    publisher = IntegracionPublisher()

    # Registrar CQS + políticas (suscripción a eventos de dominio)
    global query_handler
    _, query_handler = register_handlers(
        repo_afiliados=repo_afiliados,
        repo_conversions=repo_conversions,
        repo_comisiones=repo_comisiones,
        publisher=publisher
    )

if __name__ == "__main__":
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=UVICORN_PORT, reload=False)
