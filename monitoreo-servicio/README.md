# Monitoreo Servicio - Analytics & Event Monitoring (DDD + Hexagonal + CQRS)

Servicio de monitoreo y análisis en **Python** con **arquitectura hexagonal**, **DDD** y **CQRS**.
Implementa el tracking y análisis de eventos de comportamiento de usuarios (clicks, conversiones, ventas) 
con persistencia en **PostgreSQL** y consumo de eventos desde **Apache Pulsar**.

> **Eventos monitoreados:**
>
> - **Clicks**: Eventos de interacción del usuario con elementos de la interfaz
> - **Conversiones**: Eventos de conversión (registro, suscripción, etc.)
> - **Ventas**: Eventos de compra/transacción completada
>
> **Métricas calculadas:**
>
> - Conteos totales por tipo de evento
> - Tasa de conversión (conversiones/clicks)
> - Análisis por períodos de tiempo (1h, 24h, 7d)

---

## 🏗️ Arquitectura

### **Arquitectura Hexagonal (Ports & Adapters)**
- **Core**: Lógica de negocio y entities
- **Application**: Commands, Queries y Handlers (CQRS)
- **Infrastructure**: Adaptadores para Pulsar, PostgreSQL, configuración
- **Entrypoints**: API REST con FastAPI

### **Domain-Driven Design (DDD)**
- **Bounded Context**: Monitoreo y análisis de eventos
- **Aggregates**: Event (unificado para todos los tipos)
- **Value Objects**: EventType, Period, MetricValue
- **Repositories**: EventRepository (puerto), EventRepositorySQL (adaptador)

### **CQRS (Command Query Responsibility Segregation)**
- **Commands**: 
  - `RecordEventCommand`: Registra un nuevo evento
- **Queries**: 
  - `GetMetricsQuery`: Obtiene métricas agregadas
  - `GetEventsQuery`: Lista eventos con filtros
- **Handlers**: `EventHandler` procesa commands y queries

### **Event-Driven Architecture**
- **Consumo**: Eventos desde Apache Pulsar (3 topics: conversions, clicks, sales)
- **Procesamiento**: Asíncrono con `aiopulsar` y `asyncio`
- **Persistencia**: PostgreSQL para análisis histórico

---

## Flujo de Datos

```
[Pulsar Topics]
  ├── conversions    ┐
  ├── clicks         ├─→ [EventConsumerService] 
  └── sales          ┘         ↓
                        [PulsarEventMapper]
                               ↓  
                        [handle_event()]
                               ↓
                     [RecordEventCommand]
                               ↓
                        [EventHandler]
                               ↓
                      [Stored Events] ←─┐
                            ↓          │
                  [GET /metrics] ──────┘
                       ↓
                [MetricsResponse]
```

### **Detalle del Flujo:**

1. **Eventos llegan a Pulsar** desde sistemas externos
2. **EventConsumerService** consume de 3 topics concurrentemente
3. **PulsarEventMapper** convierte eventos Pulsar → SimpleEvent  
4. **handle_event()** transforma SimpleEvent → RecordEventCommand
5. **EventHandler** procesa comando y persiste evento
6. **API REST** consulta eventos via queries para generar métricas

---

## Quick Start con Docker

### **Levantar todo el stack:**
```bash
# Levantar Pulsar + PostgreSQL + Servicio
docker compose up -d --build

# Ver logs del servicio
docker compose logs -f monitoreo
```

### **URLs importantes:**
- **API Docs**: http://localhost:8082/docs
- **Health Check**: http://localhost:8082/health  
- **Métricas**: http://localhost:8082/metrics
- **Eventos**: http://localhost:8082/events

### **Pulsar Admin** (si necesitas debuggear):
- **Admin UI**: http://localhost:8080/admin/v2/

### **PostgreSQL**:
- **Host**: localhost:5433
- **Database**: monitoreo / monitoreo / monitoreo

---

## API Endpoints

### **Health Check**
```bash
curl http://localhost:8082/health
```
```json
{
  "status": "healthy",
  "service": "monitoreo-servicio"
}
```

### **Métricas Agregadas**
```bash
# Métricas últimas 24h (por defecto)
curl http://localhost:8082/metrics

# Métricas última hora  
curl "http://localhost:8082/metrics?period=1h"

# Métricas última semana
curl "http://localhost:8082/metrics?period=7d"
```

**Respuesta:**
```json
{
  "total_clicks": 150,
  "total_conversions": 15, 
  "total_sales": 10,
  "conversion_rate": 10.0
}
```

### **Lista de Eventos**
```bash
# Últimos 10 eventos
curl http://localhost:8082/events

# Filtrar por tipo
curl "http://localhost:8082/events?event_type=conversion&limit=5"
```

---

## Testing Manual con Pulsar

### **Simular eventos** (necesitarás cliente Pulsar):

```python
import pulsar
import json
from datetime import datetime

client = pulsar.Client('pulsar://localhost:6650')
producer = client.create_producer('clicks')

# Simular click
click_event = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000", 
    "session_id": "sess_abc123",
    "url": "https://product.com/item/123",
    "timestamp": int(datetime.now().timestamp() * 1000)
}

producer.send(json.dumps(click_event).encode('utf-8'))
```

### **Verificar que se procesó:**
```bash
# Ver métricas actualizadas
curl http://localhost:8082/metrics

# Ver evento en la lista
curl http://localhost:8082/events
```

---

## 📁 Estructura del Proyecto

```
monitoreo-servicio/
├── src/
│   ├── app/
│   │   └── main.py                 # FastAPI + lifecycle + consumers bootstrap
│   ├── core/
│   │   └── seedwork/               # Base classes (Repository, Command, etc)
│   ├── domains/
│   │   └── events/                 # Event entities + repository interfaces
│   ├── application/
│   │   ├── commands.py             # RecordEventCommand
│   │   ├── queries.py              # GetMetricsQuery, GetEventsQuery  
│   │   └── handlers.py             # EventHandler (commands + queries)
│   ├── infrastructure/
│   │   ├── database/               # SQLAlchemy models + repositories
│   │   ├── messaging/              # Pulsar consumers + event mapper
│   │   ├── schemas/                # Pydantic schemas (API + Pulsar)
│   │   └── config/                 # Settings centralizadas
│   └── entrypoints/
│       └── fastapi/                # REST API routes
├── docker-compose.yml              # Pulsar + PostgreSQL + Servicio
├── monitoreo.Dockerfile            # Container del servicio
├── monitoreo-requirements.txt      # Dependencias Python
└── .env                           # Variables de entorno
```

---

## ⚙️ Configuración

### **Variables de entorno** (`.env`):
```bash
# Aplicación
APP_ENV=dev
DEBUG=true

# Base de datos  
DATABASE_URL=postgresql+psycopg2://monitoreo:monitoreo@localhost:5433/monitoreo

# Pulsar
BROKER_HOST=broker  # En Docker
PULSAR_HOST=localhost  # Local

# API
UVICORN_PORT=8080
UVICORN_HOST=0.0.0.0
```

### **Docker Compose** maneja:
- **Pulsar cluster** (zookeeper + broker + bookie)
- **PostgreSQL** (puerto 5433 externo)
- **Servicio monitoreo** (puerto 8082 externo)

---

## 🔧 Desarrollo Local

### **Sin Docker:**
```bash
# Instalar dependencias
pip install -r monitoreo-requirements.txt

# Variables de entorno para local
export DATABASE_URL="postgresql+psycopg2://monitoreo:monitoreo@localhost:5433/monitoreo"  
export BROKER_HOST="localhost"

# Correr servicio
python -m src.app.main
```

### **Con Docker (solo servicios externos):**
```bash
# Solo Pulsar + PostgreSQL
docker compose up -d db-monitoreo broker

# Servicio en local
python -m src.app.main
```

---

## 🎯 Casos de Uso

### **1. Dashboard de Métricas en Tiempo Real**
- Consultar `/metrics?period=1h` cada minuto
- Mostrar gráficos de evolución temporal
- Alertas cuando conversion_rate < umbral

### **2. Análisis de User Journey** 
- Consultar `/events?user_id=XXX` para ver secuencia de eventos
- Identificar patrones de comportamiento
- Optimizar funnel de conversión

### **3. Reporting Ejecutivo**
- `/metrics?period=7d` para reportes semanales  
- Comparar períodos para identificar tendencias
- KPIs para toma de decisiones

---

## 🏷️ Tecnologías

- **Python 3.11** + **FastAPI** + **Uvicorn**
- **Apache Pulsar** para mensajería asíncrona
- **PostgreSQL** + **SQLAlchemy** para persistencia
- **Pydantic** para validación y schemas
- **Docker** + **Docker Compose** para deployment
- **Asyncio** + **aiopulsar** para concurrencia

---

## Roadmap / TODOs

### **Para Producción:**
- [ ] Implementar persistencia real (DB) en lugar de memoria
- [ ] Agregar autenticación y autorización
- [ ] Métricas más sofisticadas (percentiles, histogramas)
- [ ] Caching con Redis para queries frecuentes
- [ ] Monitoring con Prometheus + Grafana
- [ ] Testing automatizado (unit + integration)
- [ ] CI/CD pipeline

### **Mejoras de Arquitectura:**
- [ ] Event Sourcing para audit trail completo
- [ ] CQRS con read models separados
- [ ] Circuit breaker para Pulsar connections
- [ ] Retry policies con backoff exponencial
- [ ] Dead letter queues para eventos fallidos

---

**¡El servicio está listo para procesar eventos y generar insights de negocio!** 🎉


