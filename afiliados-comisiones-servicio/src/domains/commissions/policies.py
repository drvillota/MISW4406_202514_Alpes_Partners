from __future__ import annotations
from typing import Callable
from uuid import uuid4
from .events import ConversionRegistrada, ComisionCreada
from .entities import nueva_comision
from ..affiliates.repository import AfiliadoRepository
from ...core.seedwork.events import event_bus

# Politica: dado ConversionRegistrada, calcular y persistir Comision, luego emitir ComisionCreada
def crear_politica_comisiones(repo_afiliados: AfiliadoRepository, repo_comisiones, publisher_integracion: Callable[[ComisionCreada], None]):
    def _handler(event: ConversionRegistrada):
        afiliado = repo_afiliados.get(event.affiliate_id)
        if not afiliado:
            # no se puede calcular comisión si no existe el afiliado
            return
        # regla simple de porcentaje sobre el monto
        valor = round(event.monto * (afiliado.tasa_comision / 100.0), 2)
        comision = nueva_comision(affiliate_id=event.affiliate_id, conversion_id=None, valor=valor, moneda=event.moneda)
        # persistir
        repo_comisiones.add(comision)
        # emitir evento de dominio y de integración
        ev = ComisionCreada(commission_id=comision.id, affiliate_id=comision.affiliate_id, valor=comision.valor, moneda=comision.moneda)
        event_bus.publish(ev)
        publisher_integracion(ev)
    return _handler
