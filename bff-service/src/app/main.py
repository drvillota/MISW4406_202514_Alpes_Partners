import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from infrastructure.config import settings
from infrastructure.saga_log import SagaLogRepository
from entrypoints.routes import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("Iniciando BFF Service...")
    
    try:
        # Inicializar repositorio de saga log
        saga_repo = SagaLogRepository()
        await saga_repo.init_database()
        app.state.saga_repo = saga_repo
        logger.info("Saga Log repository inicializado")
        
        logger.info("BFF Service iniciado correctamente")
        yield
        
    except Exception as e:
        logger.error(f"Error iniciando BFF Service: {e}")
        raise
    finally:
        logger.info("Cerrando BFF Service...")


# Crear aplicación FastAPI
app = FastAPI(
    title="BFF CSaaS API",
    description="Backend for Frontend - Content as a Service Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bff-csaas"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)