# src/colaboraciones/modulos/infraestructura/mapeadores.py
from modulos.dominio.entidades import Colaboracion
from modulos.dominio.objetos_valor import (
    CampaniaId, InfluencerId, Contrato, EstadoColaboracion, Fecha
)
from .dto import Colaboracion as ColaboracionDTO
from datetime import datetime
from dataclasses import is_dataclass


class MapeadorColaboracionInfra:
    """Convierte entre DTO de infraestructura (SQLAlchemy) y entidad de dominio"""

    def obtener_tipo(self) -> type:
        # La fábrica usa esto para decidir qué fábrica usar
        return Colaboracion

    def entidad_a_dto(self, entidad: Colaboracion) -> ColaboracionDTO:
        dto = ColaboracionDTO()

        # id: soporte para entidad.id o entidad.id_cliente (historic)
        entidad_id = getattr(entidad, "id", None) or getattr(entidad, "id_cliente", None)
        dto.id = str(entidad_id) if entidad_id is not None else ""

        # ids internos: soporte .id (nuevo) o .valor (antiguo)
        id_camp = getattr(entidad, "id_campania", None)
        dto.id_campania = getattr(id_camp, "id", None) or getattr(id_camp, "valor", "") if id_camp else ""

        id_inf = getattr(entidad, "id_influencer", None)
        dto.id_influencer = getattr(id_inf, "id", None) or getattr(id_inf, "valor", "") if id_inf else ""

        dto.contrato_url = entidad.contrato.url if getattr(entidad, "contrato", None) else ""
        # estado: si es Enum (tiene .value) usamos eso, si no str()
        estado = getattr(entidad, "estado", None)
        dto.estado = estado.value if hasattr(estado, "value") else (str(estado) if estado is not None else "")

        # fecha_creacion: normalmente Fecha.valor (datetime) o directamente datetime
        fecha_obj = getattr(entidad, "fecha_creacion", None)
        if fecha_obj is None:
            dto.fecha_creacion = datetime.utcnow()
        else:
            # si es objeto Fecha con atributo 'valor'
            dto.fecha_creacion = getattr(fecha_obj, "valor", fecha_obj)

        return dto

    def dto_a_entidad(self, dto: ColaboracionDTO) -> Colaboracion:
        # dto.fecha_creacion puede ser datetime o string iso; normalizamos a datetime
        fcre = getattr(dto, "fecha_creacion", None)
        if isinstance(fcre, str):
            try:
                fcre_dt = datetime.fromisoformat(fcre)
            except Exception:
                # fallback
                fcre_dt = datetime.utcnow()
        elif isinstance(fcre, datetime):
            fcre_dt = fcre
        else:
            fcre_dt = datetime.utcnow()

        return Colaboracion(
            id=getattr(dto, "id", None) or None,
            id_campania=CampaniaId(getattr(dto, "id_campania", "")) if getattr(dto, "id_campania", "") else None,
            id_influencer=InfluencerId(getattr(dto, "id_influencer", "")) if getattr(dto, "id_influencer", "") else None,
            contrato=Contrato(
                url=getattr(dto, "contrato_url", ""),
                fecha_creacion=fcre_dt,
                fecha_validacion=None,
                fecha_finalizacion=None,
                fecha_rechazo=None
            ) if getattr(dto, "contrato_url", "") else None,
            estado=EstadoColaboracion(getattr(dto, "estado", "PENDIENTE").upper()),
            fecha_creacion=Fecha(fcre_dt)
        )


class MapeadorEventoColaboracionInfra:
    """Convierte eventos de dominio a DTOs persistentes"""

    def obtener_tipo(self) -> type:
        # si tu fábrica necesita distinguir eventos, aquí puedes devolver el tipo de evento;
        # como simplificación devolvemos dict (no usado por fábrica principal)
        return dict

    def entidad_a_dto(self, evento) -> dict:
        # Devuelve un dict con los campos que tu DTO ORM espera.
        return {
            "id": str(getattr(evento, "id", "")),
            "id_entidad": str(getattr(evento, "id_colaboracion", "")),
            "fecha_evento": getattr(evento, "fecha_creacion", datetime.utcnow()),
            "version": getattr(evento, "version", "1.0"),
            "tipo_evento": evento.__class__.__name__,
            "formato_contenido": "JSON",
            "nombre_servicio": getattr(evento, "service_name", "colaboraciones"),
            # Si el evento tiene payload como dataclass o dict, normalizamos
            "contenido": (evento.__dict__ if hasattr(evento, "__dict__") else dict(evento))
        }

    def dto_a_entidad(self, dto):
        raise NotImplementedError
