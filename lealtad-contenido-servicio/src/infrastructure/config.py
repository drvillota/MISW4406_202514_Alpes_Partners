from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "dev")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://afiliados:afiliados@localhost:5432/afiliados")
UVICORN_PORT = int(os.getenv("UVICORN_PORT", "8080"))
