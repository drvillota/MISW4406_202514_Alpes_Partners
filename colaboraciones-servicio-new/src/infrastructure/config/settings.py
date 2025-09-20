import os
from functools import lru_cache

class Settings:
    """Configuración simplificada del servicio de monitoreo"""
    
    def __init__(self):
        # Base de datos - usar variable de entorno o default para desarrollo local
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql+psycopg2://monitoreo:monitoreo@localhost:5432/monitoreo"
        )
        
        # Pulsar - usar BROKER_HOST si existe (para Docker), sino PULSAR_HOST
        pulsar_host = os.getenv("BROKER_HOST") or os.getenv("PULSAR_HOST", "localhost")
        self.PULSAR_HOST = pulsar_host
        self.PULSAR_PORT = int(os.getenv("PULSAR_PORT", "6650"))
        
        # API Server
        self.UVICORN_HOST = os.getenv("UVICORN_HOST", "0.0.0.0")
        self.UVICORN_PORT = int(os.getenv("UVICORN_PORT", "8080"))
        
        # Debug
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    @property
    def pulsar_url(self) -> str:
        """URL completa de Pulsar"""
        return f"pulsar://{self.PULSAR_HOST}:{self.PULSAR_PORT}"


@lru_cache()
def get_settings() -> Settings:
    """Configuración singleton simplificada"""
    return Settings()