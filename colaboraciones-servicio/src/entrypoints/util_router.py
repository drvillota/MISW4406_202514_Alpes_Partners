# src/entrypoints/util_routes.py
from __future__ import annotations
import logging
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone, date
from sqlalchemy.orm import Session

from core.seedworks.message_bus import bus
from application.comandos import IniciarColaboracionComando, RegistrarPublicacionComando
from application.queries import ListarColaboracionesQuery
from infrastructure.database.connection import SessionLocal
from infrastructure.database.dto import ColaboracionModel, ContratoModel, CampaniaModel, InfluencerModel
from infrastructure.messaging.despachadores import ColaboracionPublisher

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Dependencia DB ---
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Modelos de entrada ---
class ColaboracionIn(BaseModel):
    campania_id: UUID
    influencer_id: UUID
    contrato_id: UUID
    estado: str = "VIGENTE"

class PublicacionIn(BaseModel):
    colaboracion_id: UUID
    url: str
    red: str
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CampaniaIn(BaseModel):
    nombre: str
    marca: str
    fecha_inicio: date
    fecha_fin: date
    estado: str = "NUEVA"

class InfluencerIn(BaseModel):
    nombre: str
    email: str

class ContratoIn(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    estado: str = "PENDIENTE"

# --- Endpoints de comandos ---
@router.post("/dev/colaboraciones")
def iniciar_colaboracion(payload: ColaboracionIn, session: Session = Depends(get_session)):
    cmd = IniciarColaboracionComando(
        id=uuid4(),
        campania_id=payload.campania_id,
        influencer_id=payload.influencer_id,
        contrato_id=payload.contrato_id,
        estado=payload.estado,
    )
    try:
        result = bus.handle_command(cmd)
        return {"status": "ok", "colaboracion_id": str(cmd.id), "result": result}
    except Exception as e:
        logger.error(f"Error procesando comando: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error procesando comando: {e}")

@router.post("/dev/publicaciones")
def registrar_publicacion(payload: PublicacionIn, session: Session = Depends(get_session)):
    cmd = RegistrarPublicacionComando(
        colaboracion_id=payload.colaboracion_id,
        url=payload.url,
        red=payload.red,
        fecha=payload.fecha,
    )
    try:
        result = bus.handle_command(cmd)

        colab = session.query(ColaboracionModel).filter_by(id=payload.colaboracion_id).first()
        if not colab:
            raise HTTPException(status_code=404, detail="Colaboración no encontrada")

        nueva_pub = {
            "id": str(uuid4()),
            "url": payload.url,
            "red": payload.red,
            "fecha": payload.fecha.isoformat(),
        }
        publicaciones = colab.publicaciones or []
        publicaciones.append(nueva_pub)
        colab.publicaciones = publicaciones
        session.commit()

        return {"status": "ok", "result": result, "publicacion": nueva_pub}
    except Exception as e:
        logger.error(f"Error procesando comando: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error procesando comando: {e}")

# --- Endpoints de consultas ---
@router.get("/dev/colaboraciones")
def listar_colaboraciones(session: Session = Depends(get_session)):
    try:
        colabs = session.query(ColaboracionModel).all()
        return [
            {
                "id": str(c.id),
                "campania_id": str(c.campania_id),
                "influencer_id": str(c.influencer_id),
                "contrato_id": str(c.contrato_id),
                "estado": c.estado,
                "created_at": c.created_at.isoformat(),
                "publicaciones": c.publicaciones,
            }
            for c in colabs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando query: {e}")

# --- Seeders individuales ---
@router.post("/dev/seed_campania")
def seed_campania(payload: CampaniaIn, session: Session = Depends(get_session)):
    m = CampaniaModel(
        id=uuid4(),
        nombre=payload.nombre,
        marca=payload.marca,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
        estado=payload.estado,
    )
    session.add(m)
    session.commit()
    return {"campania_id": str(m.id)}

@router.post("/dev/seed_influencer")
def seed_influencer(payload: InfluencerIn, session: Session = Depends(get_session)):
    m = InfluencerModel(
        id=uuid4(),
        nombre=payload.nombre,
        email=payload.email,
    )
    session.add(m)
    session.commit()
    return {"influencer_id": str(m.id)}

@router.post("/dev/seed_contrato")
def seed_contrato(payload: ContratoIn, session: Session = Depends(get_session)):
    m = ContratoModel(
        id=uuid4(),
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
        estado=payload.estado,
    )
    session.add(m)
    session.commit()
    return {"contrato_id": str(m.id)}

# --- Seeder de colaboracion ---
@router.post("/dev/seed_colaboracion")
def seed_colaboracion(payload: ColaboracionIn, session: Session = Depends(get_session)):
    m = ColaboracionModel(
        id=uuid4(),
        campania_id=payload.campania_id,
        influencer_id=payload.influencer_id,
        contrato_id=payload.contrato_id,
        estado=payload.estado,
        publicaciones=[],
    )
    session.add(m)
    session.commit()
    return {"colaboracion_id": str(m.id)}

# --- Endpoints de diagnóstico Pulsar ---
PULSAR_ADMIN = "http://broker:8080/admin/v2" 

@router.get("/utils/dev/pulsar/topics")
def listar_topics():
    try:
        r = requests.get(f"{PULSAR_ADMIN}/persistent/public/default")
        r.raise_for_status()
        return {"status": "ok", "topics": r.json()}
    except Exception as e:
        logger.error(f"Error listando tópicos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listando tópicos: {e}")

@router.get("/utils/dev/pulsar/subscriptions/{topic}")
def listar_subs(topic: str):
    try:
        pulsar_topic = f"persistent://public/default/{topic}"
        r = requests.get(f"{PULSAR_ADMIN}/persistent/public/default/{topic}/subscriptions")
        r.raise_for_status()
        return {"status": "ok", "topic": pulsar_topic, "subscriptions": r.json()}
    except Exception as e:
        logger.error(f"Error listando subs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listando subs: {e}")

@router.get("/utils/dev/pulsar/stats/{topic}")
def stats_topic(topic: str):
    try:
        pulsar_topic = f"persistent://public/default/{topic}"
        r = requests.get(f"{PULSAR_ADMIN}/persistent/public/default/{topic}/stats")
        r.raise_for_status()
        return {"status": "ok", "topic": pulsar_topic, "stats": r.json()}
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error obteniendo stats: {e}")

@router.get("/dev/pulsar/health")
def pulsar_health():
    """Consulta el estado de salud del broker Pulsar"""
    broker_admin = "http://broker:8080/admin/v2/brokers/health"
    try:
        resp = requests.get(broker_admin, timeout=5)
        if resp.status_code == 200:
            try:
                return {"status": "ok", "detail": resp.json()}
            except Exception:
                return {"status": "ok", "detail": resp.text or "Broker healthy"}
        else:
            return {"status": "error", "detail": f"Unexpected status {resp.status_code}"}
    except Exception as e:
        logger.error(f"Error consultando health de Pulsar: {e}")
        raise HTTPException(status_code=500, detail=str(e))