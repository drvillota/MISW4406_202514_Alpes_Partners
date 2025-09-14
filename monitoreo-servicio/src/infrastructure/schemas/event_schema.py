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