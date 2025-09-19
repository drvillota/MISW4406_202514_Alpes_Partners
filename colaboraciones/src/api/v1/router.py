# colaboraciones/src/api/v1/router.py
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from contextvars import ContextVar
from datetime import datetime

from modulos.aplicacion.dto import ColaboracionDTO
from modulos.aplicacion.mapeadores import MapeadorColaboracionDTOJson
from modulos.aplicacion.comandos.comandos import (
    ComandoCrearColaboracion,
    ComandoValidarContrato,
    ComandoRechazarContrato,
)
from modulos.aplicacion.queries.queries import (
    ObtenerColaboracion,
    ListarColaboracionesPorCampania,
)
from seedwork.aplicacion.comandos import ejecutar_commando
from seedwork.aplicacion.queries import ejecutar_query
from seedwork.dominio.excepciones import ExcepcionDominio

router = APIRouter(prefix="/colaboraciones", tags=["colaboraciones"])

# ------------------------------------------------------------------
# ContextVar para seleccionar método de Unidad de Trabajo (reemplaza flask.session['uow_metodo'])
# ------------------------------------------------------------------
_uow_metodo: ContextVar[Optional[str]] = ContextVar("_uow_metodo", default=None)

def set_uow_pulsar() -> None:
    """
    Dependencia rápida que marca el método de UoW como 'pulsar'.
    NO usamos un generator (yield) para evitar problemas de ContextVar/token
    al mezclar ejecución en hilos (tests / starlette).
    - Úsala con Depends(set_uow_pulsar).
    Nota: el valor se guarda en el ContextVar para la petición/ contexto actual.
    """
    _uow_metodo.set("pulsar")

def get_current_uow_metodo() -> Optional[str]:
    """Si necesitas leer el valor en otro lugar (ej: UnidadTrabajoPuerto)"""
    return _uow_metodo.get()


# ---------- POST: Crear colaboración ----------
@router.post("", status_code=202)
def crear_colaboracion(body: dict = Body(...), _uow=Depends(set_uow_pulsar)):
    try:
        data = body
        map_colab = MapeadorColaboracionDTOJson()
        dto: ColaboracionDTO = map_colab.externo_a_dto(data)

        comando = ComandoCrearColaboracion(
            id_campania=dto.id_campania,
            id_influencer=dto.id_influencer,
            contrato_url=dto.contrato_url,
        )
        ejecutar_commando(comando)

        return {} 

    except ExcepcionDominio as e:
        # devolver 400 con mensaje de error
        raise HTTPException(status_code=400, detail=str(e))


# ---------- PUT: Validar contrato ----------
@router.put("/{id}/validar", status_code=202)
def validar_contrato(id: str, _uow=Depends(set_uow_pulsar)):
    try:
        comando = ComandoValidarContrato(id_colaboracion=id)
        ejecutar_commando(comando)
        return {}
    except ExcepcionDominio as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- PUT: Rechazar contrato ----------
@router.put("/{id}/rechazar", status_code=202)
def rechazar_contrato(id: str, body: Optional[dict] = Body(None), _uow=Depends(set_uow_pulsar)):
    try:
        data = body or {}
        motivo = data.get("motivo", "Sin motivo especificado")

        comando = ComandoRechazarContrato(id_colaboracion=id, motivo=motivo)
        ejecutar_commando(comando)

        return {}
    except ExcepcionDominio as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- GET: Obtener colaboración ----------
@router.get("/{id}")
def obtener_colaboracion(id: str):
    query_resultado = ejecutar_query(ObtenerColaboracion(id=id))
    map_colab = MapeadorColaboracionDTOJson()
    # dto_a_externo devuelve dict
    return map_colab.dto_a_externo(query_resultado.resultado)


# ---------- GET: Listar colaboraciones por campaña ----------
@router.get("")
def listar_colaboraciones(id_campania: Optional[str] = None):
    if not id_campania:
        raise HTTPException(status_code=400, detail="Debe especificar un id_campania")

    query_resultado = ejecutar_query(ListarColaboracionesPorCampania(id_campania=id_campania))
    return [dto.__dict__ for dto in query_resultado.resultado]
