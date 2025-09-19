# colaboraciones/src/config/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de conexión
TESTING = os.getenv("TESTING", "false").lower() == "true"

if TESTING:
    DATABASE_URL = "sqlite:///./colaboraciones_test.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DB_USERNAME = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "adminadmin")
    DB_HOSTNAME = os.getenv("DB_HOSTNAME", "localhost")
    DB_NAME = os.getenv("DB_NAME", "colaboraciones")
    DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}/{DB_NAME}"
    engine = create_engine(DATABASE_URL)

# Session / Base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
