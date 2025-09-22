import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # BFF Service settings
    app_name: str = "BFF CSaaS"
    debug: bool = True
    
    # Database for Saga Log
    database_url: str = os.getenv("SAGA_DATABASE_URL", "postgresql+psycopg2://saga:saga@db-saga:5432/saga")
    
    # Microservices URLs
    lealtad_contenido_url: str = os.getenv("LEALTAD_CONTENIDO_URL", "http://lealtad-contenido:8080")
    afiliados_comisiones_url: str = os.getenv("AFILIADOS_COMISIONES_URL", "http://afiliados-comisiones:8081")
    colaboraciones_url: str = os.getenv("COLABORACIONES_URL", "http://colaboraciones-servicio:8083")
    monitoreo_url: str = os.getenv("MONITOREO_URL", "http://monitoreo:8082")
    
    # Pulsar settings
    pulsar_url: str = os.getenv("PULSAR_URL", "pulsar://broker:6650")
    broker_host: str = os.getenv("BROKER_HOST", "broker")


settings = Settings()