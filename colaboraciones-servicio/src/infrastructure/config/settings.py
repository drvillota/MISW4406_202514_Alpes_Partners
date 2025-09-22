import os
from functools import lru_cache

class Settings:
    """Configuración simplificada del servicio de colaboraciones"""
    
    def __init__(self):
        # Base de datos
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql+psycopg2://colaboraciones:colaboraciones@localhost:5432/colaboraciones"
        )
        
        # Pulsar
        pulsar_host = os.getenv("BROKER_HOST") or os.getenv("PULSAR_HOST", "localhost")
        self.PULSAR_HOST = pulsar_host
        self.PULSAR_PORT = int(os.getenv("PULSAR_PORT", "6650"))
        self.PULSAR_ADMIN_PORT = int(os.getenv("PULSAR_ADMIN_PORT", "8080"))  # 👈 nuevo
        
        # API Server
        self.UVICORN_HOST = os.getenv("UVICORN_HOST", "0.0.0.0")
        self.UVICORN_PORT = int(os.getenv("UVICORN_PORT", "8080"))
        
        # Debug
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    @property
    def pulsar_url(self) -> str:
        """URL completa de Pulsar (binaria para producer/consumer)"""
        return f"pulsar://{self.PULSAR_HOST}:{self.PULSAR_PORT}"

    @property
    def pulsar_admin_url(self) -> str:
        """URL completa de la API REST de Pulsar"""
        return f"http://{self.PULSAR_HOST}:{self.PULSAR_ADMIN_PORT}"


@lru_cache()
def get_settings() -> Settings:
    """Configuración singleton simplificada"""
    return Settings()
