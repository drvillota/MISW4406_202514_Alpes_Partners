# Schemas simplificados para PoC
from pulsar.schema import Record, String, Integer, Float

class BaseEventSchema(Record):
    """Schema base para eventos de Pulsar"""
    user_id = String()
    session_id = String()
    timestamp = Integer()  # Unix timestamp

class ConversionEventSchema(BaseEventSchema):
    """Schema simple para conversiones"""
    amount = Float()

class ClickEventSchema(BaseEventSchema):
    """Schema simple para clicks"""
    url = String()

class SaleEventSchema(BaseEventSchema):
    """Schema simple para ventas"""
    order_id = String()
    amount = Float()

class PublicacionRegistradaSchema(BaseEventSchema):
    """Schema para eventos de publicaciones registradas"""
    colaboracion_id = String()
    campania_id = String()
    influencer_id = String()
    url = String()
    red = String()
    fecha = String()  # ISO format date