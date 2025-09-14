from __future__ import annotations
import os
from functools import lru_cache
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Configuración centralizada del servicio de monitoreo"""
    
    # Aplicación
    APP_NAME: str = "monitoreo-servicio"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="dev", env="APP_ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Base de datos
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://monitoreo:monitoreo@localhost:5433/monitoreo",
        env="DATABASE_URL"
    )
    
    # Pulsar/Messaging
    PULSAR_HOST: str = Field(default="localhost", env="PULSAR_HOST")
    BROKER_HOST: str = Field(default="localhost", env="BROKER_HOST")  # Alias para PULSAR_HOST
    PULSAR_PORT: int = Field(default=6650, env="PULSAR_PORT")
    
    # API Server
    UVICORN_HOST: str = Field(default="0.0.0.0", env="UVICORN_HOST")
    UVICORN_PORT: int = Field(default=8080, env="UVICORN_PORT")  # Corregido para coincidir con Docker
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Métricas y limpieza
    METRICS_RETENTION_DAYS: int = Field(default=90, env="METRICS_RETENTION_DAYS")
    CLEANUP_INTERVAL_HOURS: int = Field(default=24, env="CLEANUP_INTERVAL_HOURS")
    
    # Paginación
    DEFAULT_PAGE_SIZE: int = Field(default=100, env="DEFAULT_PAGE_SIZE")
    MAX_PAGE_SIZE: int = Field(default=1000, env="MAX_PAGE_SIZE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def pulsar_url(self) -> str:
        """URL completa de Pulsar"""
        # Usar BROKER_HOST si está definido, sino PULSAR_HOST
        host = os.getenv("BROKER_HOST", self.PULSAR_HOST)
        return f"pulsar://{host}:{self.PULSAR_PORT}"
    
    @property
    def effective_pulsar_host(self) -> str:
        """Host efectivo de Pulsar (BROKER_HOST tiene precedencia)"""
        return os.getenv("BROKER_HOST", self.PULSAR_HOST)
    
    @property
    def is_development(self) -> bool:
        """Si estamos en entorno de desarrollo"""
        return self.APP_ENV.lower() in ["dev", "development"]
    
    @property 
    def is_production(self) -> bool:
        """Si estamos en entorno de producción"""
        return self.APP_ENV.lower() in ["prod", "production"]


@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la configuración singleton.
    Usa cache para evitar recargar en cada llamada.
    """
    return Settings()