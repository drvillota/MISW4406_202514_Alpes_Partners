from __future__ import annotations
from datetime import datetime
from uuid import UUID
from ..core.seedwork.message_bus import bus
from ..core.seedwork.events import event_bus
from ..domains.commissions.events import ConversionRegistrada
from ..domains.commissions.entities import nueva_conversion
from ..domains.affiliates.repository import AfiliadoRepository
from ..domains.commissions.repository import ConversionRepository, ComisionRepository
from ..infrastructure.messaging.publisher import IntegracionPublisher
from ..domains.commissions.policies import crear_politica_comisiones
from .commands import RegistrarConversionCommand
from .queries import ConsultarComisionesPorAfiliadoQuery

# Los repos son inyectados por bootstrap (ver app.main)

def register_handlers(repo_afiliados: AfiliadoRepository, repo_conversions: ConversionRepository, repo_comisiones: ComisionRepository, publisher: IntegracionPublisher):
    # comando
    def handle_registrar_conversion(cmd: RegistrarConversionCommand):
        # crear entidad dominio y persistir
        conv = nueva_conversion(cmd.affiliate_id, cmd.event_type, cmd.monto, cmd.moneda, cmd.occurred_at)
        repo_conversions.add(conv)
        # emitir evento de dominio que conecta módulos (tracking -> comisiones)
        event_bus.publish(ConversionRegistrada(affiliate_id=cmd.affiliate_id, event_type=cmd.event_type, monto=cmd.monto, moneda=cmd.moneda, occurred_at=cmd.occurred_at))
        return {"conversion_id": str(conv.id)}

    bus.register_command(RegistrarConversionCommand, handle_registrar_conversion)

    # consulta
    def handle_consultar(q: ConsultarComisionesPorAfiliadoQuery):
        items = repo_comisiones.list_by_affiliate(q.affiliate_id, q.desde.isoformat() if q.desde else None, q.hasta.isoformat() if q.hasta else None)
        return [{
            "commission_id": str(i.id),
            "affiliate_id": str(i.affiliate_id),
            "valor": i.valor,
            "moneda": i.moneda,
            "estado": i.estado,
            "created_at": i.created_at.isoformat()
        } for i in items]

    # política de comisiones (evento de dominio -> cálculo y persistencia + evento de integración)
    handler_politica = crear_politica_comisiones(repo_afiliados=repo_afiliados, repo_comisiones=repo_comisiones, publisher_integracion=publisher.publicar_comision_creada)
    from ..domains.commissions.events import ConversionRegistrada as _CR
    event_bus.subscribe(_CR, handler_politica)

    # devolver manejadores para usarlos directamente si se requiere
    return handle_registrar_conversion, handle_consultar
