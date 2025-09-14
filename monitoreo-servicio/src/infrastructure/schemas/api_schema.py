from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class EventType(str, Enum):
    CONVERSION = "conversion"
    CLICK = "click"
    SALE = "sale"

class Period(str, Enum):
    HOUR = "1h"
    DAY = "24h" 
    WEEK = "7d"

# Responses simples
class HealthResponse(BaseModel):
    status: str
    service: str

class EventResponse(BaseModel):
    id: str
    type: EventType
    user_id: str
    timestamp: datetime

class MetricsResponse(BaseModel):
    total_clicks: int
    total_conversions: int
    total_sales: int
    conversion_rate: float