# src/colaboraciones/modulos/aplicacion/mapeadores.py

from datetime import datetime
from dataclasses import is_dataclass, asdict
from typing import Any

from seedwork.aplicacion.dto import Mapeador as AppMap
from seedwork.dominio.repositorios import Mapeador as RepMap
from modulos.aplicacion.dto import ColaboracionDTO
from modulos.dominio.entidades import Colaboracion
from modulos.dominio.objetos_valor import (
    CampaniaId,
    InfluencerId,
    Contrato,
    EstadoColaboracion,
    Fecha,
)


# ---------- helpers ----------
def _safe_iso_to_datetime(s: str) -> datetime:
    """
    Convierte un ISO string (con o sin Z/offset) a datetime.
    Si falla, retorna datetime.utcnow().
    """
    if not s:
        return datetime.utcnow()
    try:
        # fromisoformat no acepta 'Z' -> reemplazamos por +00:00
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        # fallback: intentar parseo sin timezone
        try:
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return datetime.utcnow()


# ---------- JSON <-> DTO ----------

class MapeadorColaboracionDTOJson(AppMap):
    def externo_a_dto(self, externo: dict) -> ColaboracionDTO:
        return ColaboracionDTO(
            id=externo.get("id", ""),
            id_campania=externo.get("id_campania", ""),
            id_influencer=externo.get("id_influencer", ""),
            contrato_url=externo.get("contrato_url", ""),
            # Normalizamos a minúsculas en la representación externa (tal como usan los tests).
            estado=externo.get("estado", "PENDIENTE"),
            fecha_creacion=externo.get("fecha_creacion", datetime.utcnow().isoformat()),
        )

    def dto_a_externo(self, dto: ColaboracionDTO) -> dict:
        # Manejar DTO que sea dict, dataclass u objeto con __dict__
        if isinstance(dto, dict):
            return dto
        if is_dataclass(dto):
            return asdict(dto)
        try:
            return dto.__dict__
        except Exception:
            # fallback
            return dict(dto)


# ---------- DTO <-> Entidad ----------

class MapeadorColaboracion(RepMap):
    _FORMATO_FECHA = "%Y-%m-%dT%H:%M:%SZ"

    def obtener_tipo(self) -> type:
        # Devuelve la clase de entidad que maneja el mapeador
        return Colaboracion

    def entidad_a_dto(self, entidad: Colaboracion) -> ColaboracionDTO:
        # soporte id o id_cliente
        id_val = getattr(entidad, "id", None) or getattr(entidad, "id_cliente", None) or getattr(entidad, "id_colaboracion", None)
        id_str = str(id_val) if id_val is not None else ""

        # seguridad sobre campos opcionales
        id_campania = getattr(entidad.id_campania, "id", "") if getattr(entidad, "id_campania", None) else ""
        id_influencer = getattr(entidad.id_influencer, "id", "") if getattr(entidad, "id_influencer", None) else ""
        contrato_url = entidad.contrato.url if getattr(entidad, "contrato", None) else ""

        # estado a minúsculas (representación externa)
        if hasattr(entidad, "estado") and getattr(entidad.estado, "value", None) is not None:
            estado_str = entidad.estado.value.lower()
        else:
            estado_str = str(getattr(entidad, "estado", "")).lower()

        # fecha_creacion (si tu entidad usa Fecha.valor o un datetime)
        fecha_creacion_val = ""
        fc = getattr(entidad, "fecha_creacion", None)
        if fc is not None:
            if hasattr(fc, "valor"):
                try:
                    fecha_creacion_val = fc.valor.isoformat()
                except Exception:
                    fecha_creacion_val = str(fc.valor)
            elif isinstance(fc, datetime):
                fecha_creacion_val = fc.isoformat()
            else:
                fecha_creacion_val = str(fc)

        return ColaboracionDTO(
            id=id_str,
            id_campania=id_campania,
            id_influencer=id_influencer,
            contrato_url=contrato_url,
            estado=estado_str,
            fecha_creacion=fecha_creacion_val,
        )

    def dto_a_entidad(self, dto: ColaboracionDTO) -> Colaboracion:
        # dto.estado puede venir 'pendiente' o 'PENDIENTE'
        estado_raw = getattr(dto, "estado", None) or ""
        estado_str = estado_raw.upper() if isinstance(estado_raw, str) else str(estado_raw)

        # valores raw del DTO
        id_val = getattr(dto, "id", None) or None
        camp_raw = getattr(dto, "id_campania", None)
        inf_raw = getattr(dto, "id_influencer", None)
        contrato_url = getattr(dto, "contrato_url", "") or ""
        fecha_iso = getattr(dto, "fecha_creacion", "") or ""

        # detectamos qué campos declara realmente la dataclass Colaboracion
        dataclass_fields = getattr(Colaboracion, "__dataclass_fields__", {}) or {}

        kwargs: dict[str, Any] = {}

        # id: puede ser 'id' o 'id_cliente' según tu entidad
        if "id" in dataclass_fields:
            kwargs["id"] = id_val
        elif "id_cliente" in dataclass_fields:
            kwargs["id_cliente"] = id_val
        elif "id_colaboracion" in dataclass_fields:
            kwargs["id_colaboracion"] = id_val

        # id_campania / id_influencer si existen
        if "id_campania" in dataclass_fields:
            kwargs["id_campania"] = CampaniaId(camp_raw) if camp_raw else None
        if "id_influencer" in dataclass_fields:
            kwargs["id_influencer"] = InfluencerId(inf_raw) if inf_raw else None

        # contrato
        if "contrato" in dataclass_fields:
            kwargs["contrato"] = (
                Contrato(
                    url=contrato_url,
                    fecha_creacion=_safe_iso_to_datetime(fecha_iso),
                    fecha_validacion=None,
                    fecha_finalizacion=None,
                    fecha_rechazo=None,
                )
                if contrato_url
                else None
            )

        # estado
        if "estado" in dataclass_fields:
            kwargs["estado"] = EstadoColaboracion(estado_str) if estado_str else EstadoColaboracion.PENDIENTE

        # fecha_creacion
        if "fecha_creacion" in dataclass_fields:
            kwargs["fecha_creacion"] = Fecha(_safe_iso_to_datetime(fecha_iso)) if fecha_iso else Fecha(datetime.utcnow())

        # construir la entidad sólo con los campos detectados
        return Colaboracion(**kwargs)
