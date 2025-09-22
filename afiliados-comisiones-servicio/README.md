# Afiliados — Comisiones por Evento (DDD + EDA + Hexagonal)

Servicio base en **Python** con **arquitectura hexagonal**, **DDD**, **eventos de dominio** y **CQS**.
Implementa el dominio de _afiliados_ y _comisiones por evento_ con persistencia real en **PostgreSQL**
y publicación de eventos de integración vía **Apache Pulsar**.

> **Módulos internos (bounded modules) y comunicación por eventos de dominio**
>
> - **Tracking** (conversión): emite `ConversionRegistrada` (evento de dominio).
> - **Comisiones**: escucha `ConversionRegistrada`, calcula y persiste una `Comision`, y emite `ComisionCreada`.
>

---

## Arquitectura

- **Hexagonal (Ports & Adapters)**: capas `domain` / `application` / `infrastructure` + `entrypoints` (FastAPI).
- **DDD**: 
  - Agregados (Afiliado, Conversion, Comision)
  - Objetos de Valor (`Dinero`, `TasaComision`)
  - Entidades
  - Repositorios (puertos)
  - Implementaciones (adaptadores).
- **CQS**:
  - **Comando**: `RegistrarConversionCommand`
  - **Consulta**: `ConsultarComisionesPorAfiliadoQuery`
  - **Eventos**: `ConversionRegistrada`, `ComisionCreada`
- **Persistencia real**: **PostgreSQL** con SQLAlchemy 
- **Event-driven**: Publicación de eventos de **integración** en Apache Pulsar (`comisiones.creadas`) y
  **eventos de dominio** in-process entre módulos.
- **Configuración**: `.env` + variables de entorno.
- **Docker Compose**: Postgres, Apache Pulsar y servicio.

## Correr con Docker

### Iniciar el Servicio

```bash
# Navegar al directorio del proyecto
cd MISW4406_202514_Alpes_Partners

# Iniciar solo el servicio de afiliados-comisiones con sus dependencias
docker compose --profile afiliados-comisiones up -d --build

# O iniciar todos los servicios
docker compose up -d --build
```

**Servicios disponibles:**
- **API REST**: `http://localhost:8081/docs` (Swagger UI)
- **Base de datos**: PostgreSQL en `localhost:5432`
- **Apache Pulsar**: Broker en `pulsar://broker:6650`
- **Pulsar Admin**: `http://localhost:8080` (Admin API)

> **Nota**: El servicio se ejecuta en el puerto **8081** (no 8080), según la configuración del docker-compose.yml

### Verificar que el Servicio Está Funcionando

```bash
# Verificar el estado de los contenedores
docker compose ps

# Ver logs del servicio
docker compose logs afiliados-comisiones

# Verificar que la API responde
curl http://localhost:8081/docs

# Verificar que Pulsar está funcionando
curl http://localhost:8080/admin/v2/clusters
```

---

## 🧪 Prueba de Concepto - Comisiones por Evento

Esta sección demuestra el **flujo completo** del servicio de comisiones por evento basado en **arquitectura de eventos**. Los endpoints publican eventos en Apache Pulsar y los consumidores ejecutan los comandos correspondientes de forma asíncrona.

### Paso 1: Crear un Afiliado

**Endpoint**: `POST /dev/seed_affiliate`

```bash
curl -X POST "http://localhost:8081/dev/seed_affiliate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Juan Pérez",
    "email": "juan@example.com",
    "commission_rate": 0.05
  }'
```

**Respuesta esperada**:
```json
{
  "status": "requested",
  "message": "Affiliate registration published to event stream",
  "affiliate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

> **Guarda el `affiliate_id`** devuelto para los siguientes pasos. Este endpoint publica un evento `AffiliateRegistered` que será procesado por los consumidores.

### Paso 2: Registrar una Conversión (Evento de Compra)

**Endpoint**: `POST /dev/conversions`

```bash
# Reemplaza <AFFILIATE_ID> con el ID obtenido en el paso anterior
curl -X POST "http://localhost:8081/dev/conversions" \
  -H "Content-Type: application/json" \
  -d '{
    "affiliate_id": "<AFFILIATE_ID>",
    "event_type": "COMPRA",
    "monto": 100.0,
    "moneda": "USD"
  }'
```

**Respuesta esperada**:
```json
{
  "status": "requested",
  "message": "Conversion request published to event stream",
  "affiliate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event_type": "COMPRA",
  "timestamp": "2025-09-21T10:30:00Z"
}
```

**Lo que sucede internamente**:
1. Se publica un evento `ConversionRequested` en Apache Pulsar
2. Los consumidores de eventos detectan el evento
3. Se ejecuta automáticamente `RegistrarConversionCommand` 
4. Se calcula la comisión (100.0 × 5% = 5.00 USD)
5. Se persiste la conversión y comisión en la base de datos
6. Se emite un evento `ComisionCreada` para integración

### Paso 3: Consultar Afiliado Creado

**Endpoint**: `GET /affiliates/{affiliate_id}`

```bash
# Reemplaza <AFFILIATE_ID> con el ID del afiliado
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>"
```

**Respuesta esperada**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "commission_rate": 0.05,
  "created_at": "2025-09-21T10:25:00Z",
  "status": "active",
  "timestamp": "2025-09-21T10:30:00Z"
}
```

### Paso 4: Consultar Comisiones Generadas

**Endpoint**: `GET /affiliates/{affiliate_id}/commissions`

```bash
# Reemplaza <AFFILIATE_ID> con el ID del afiliado
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>/commissions"
```

**Respuesta esperada**:
```json
{
  "affiliate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total_commissions": 1,
  "commissions": [
    {
      "id": "c3d4e5f6-g7h8-9012-cdef-345678901234",
      "affiliate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "amount": 5.0,
      "currency": "USD",
      "conversion_id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
      "created_at": "2025-09-21T10:30:00Z",
      "status": "active"
    }
  ],
  "query_period": {
    "desde": null,
    "hasta": null
  },
  "timestamp": "2025-09-21T10:35:00Z"
}
```

### Paso 5: Consultar Comisiones Filtradas por Fecha

```bash
# Consultar comisiones desde una fecha específica
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>/commissions?desde=2025-01-01"

# Consultar comisiones en un rango de fechas
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>/commissions?desde=2025-01-01&hasta=2025-12-31"
```

### Paso 6: Diagnosticar Apache Pulsar

**Verificar Estado de Conexión**:
```bash
# Verificar si el servicio puede conectarse a Pulsar
curl "http://localhost:8081/dev/pulsar/health"
```

**Crear Topics Necesarios**:
```bash
# Crear todos los topics necesarios
curl -X POST "http://localhost:8081/dev/pulsar/create-topics"
```

**Listar Topics Existentes**:
```bash
# Ver todos los topics disponibles
curl "http://localhost:8081/dev/pulsar/topics"
```

### Paso 7: Registrar Múltiples Conversiones (Prueba de Volumen)

```bash
# Conversión de registro (evento diferente)
curl -X POST "http://localhost:8081/dev/conversions" \
  -H "Content-Type: application/json" \
  -d '{
    "affiliate_id": "<AFFILIATE_ID>",
    "event_type": "REGISTRO",
    "monto": 50.00,
    "moneda": "USD"
  }'

# Otra compra con mayor monto
curl -X POST "http://localhost:8081/dev/conversions" \
  -H "Content-Type: application/json" \
  -d '{
    "affiliate_id": "<AFFILIATE_ID>",
    "event_type": "COMPRA",
    "monto": 1200.00,
    "moneda": "USD"
  }'
```

### Paso 8: Crear Múltiples Afiliados para Pruebas Avanzadas

```bash
# Afiliado con comisión alta
curl -X POST "http://localhost:8081/dev/seed_affiliate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Carlos Rodríguez",
    "email": "carlos.rodriguez@premium.com",
    "commission_rate": 0.25
  }'

# Afiliado con comisión baja
curl -X POST "http://localhost:8081/dev/seed_affiliate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ana López",
    "email": "ana.lopez@startup.com",
    "commission_rate": 0.085
  }'
```

---

## 📊 Resultados Esperados

Después de ejecutar todas las pruebas, deberías ver:

### En la Base de Datos

**Tabla `affiliates`**: Afiliados creados con diferentes tasas de comisión
**Tabla `conversion_events`**: Eventos de conversión registrados
**Tabla `commissions`**: Comisiones calculadas automáticamente

### En los Logs del Servicio

```bash
docker compose logs afiliados-comisiones | grep -E "(Processing conversion|Command created|Event published)"
```

Deberías ver logs similares a:
```
afiliados-comisiones | INFO:     Processing conversion for affiliate: a1b2c3d4-e5f6-7890...
afiliados-comisiones | INFO:     Command created: RegistrarConversionCommand
afiliados-comisiones | INFO:     Event published: ConversionRegistrada
afiliados-comisiones | INFO:     Commission calculated: 75.00 USD
afiliados-comisiones | INFO:     Event published: ComisionCreada
```

### En Apache Pulsar (Eventos de Integración)

1. Accede a `http://localhost:8080/admin/v2/persistent` (Pulsar Admin API)
2. Verifica los topics creados:
   ```bash
   curl http://localhost:8080/admin/v2/persistent/public/default
   ```
3. Deberías ver topics relacionados con `afiliados.conversiones` y `comisiones.creadas`
4. Para ver mensajes en un topic específico:
   ```bash
   curl http://localhost:8080/admin/v2/persistent/public/default/comisiones.creadas/stats
   ```

---

## 🛠 Script de Prueba Automatizado

Para facilitar las pruebas, aquí tienes un script completo:

```bash
#!/bin/bash

echo "🚀 Iniciando prueba de concepto - Comisiones por Evento"

# Verificar conexión a Pulsar
echo "🔍 Paso 0: Verificando conexión a Pulsar..."
PULSAR_HEALTH=$(curl -s "http://localhost:8081/dev/pulsar/health")
PULSAR_STATUS=$(echo $PULSAR_HEALTH | jq -r '.status')

if [ "$PULSAR_STATUS" != "connected" ]; then
    echo "❌ Pulsar no conectado. Intentando crear topics..."
    curl -s -X POST "http://localhost:8081/dev/pulsar/create-topics" > /dev/null
    sleep 2
fi

# Crear afiliado
echo "📝 Paso 1: Creando afiliado..."
AFFILIATE_RESPONSE=$(curl -s -X POST "http://localhost:8081/dev/seed_affiliate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prueba Afiliado",
    "email": "prueba@test.com",
    "commission_rate": 12.5
  }')

AFFILIATE_ID=$(echo $AFFILIATE_RESPONSE | jq -r '.affiliate_id')
echo "✅ Afiliado creado: $AFFILIATE_ID"

# Probar publicación de eventos
echo "📡 Paso 1.5: Probando publicación de eventos..."
TEST_PUBLISH=$(curl -s -X POST "http://localhost:8081/dev/pulsar/test-publish")
TEST_STATUS=$(echo $TEST_PUBLISH | jq -r '.status')
echo "📊 Estado de publicación: $TEST_STATUS"

# Registrar conversión
echo "💰 Paso 2: Registrando conversión..."
CONVERSION_RESPONSE=$(curl -s -X POST "http://localhost:8081/dev/conversions" \
  -H "Content-Type: application/json" \
  -d "{
    \"affiliate_id\": \"$AFFILIATE_ID\",
    \"event_type\": \"COMPRA\",
    \"monto\": 800.00,
    \"moneda\": \"USD\"
  }")

echo "✅ Conversión registrada"
echo "📄 Respuesta: $CONVERSION_RESPONSE"

# Esperar procesamiento
echo "⏳ Esperando procesamiento de eventos..."
sleep 3

# Verificar topics creados
echo "📋 Verificando topics de Pulsar..."
TOPICS_RESPONSE=$(curl -s "http://localhost:8081/dev/pulsar/topics")
echo $TOPICS_RESPONSE | jq '.count, .topics[]' 2>/dev/null || echo "Topics: $TOPICS_RESPONSE"

# Consultar comisiones
echo "📊 Paso 3: Consultando comisiones generadas..."
COMMISSIONS=$(curl -s "http://localhost:8081/affiliates/$AFFILIATE_ID/commissions")
echo $COMMISSIONS | jq '.' 2>/dev/null || echo "Comisiones: $COMMISSIONS"

echo "🎉 Prueba completada exitosamente!"
echo "📈 Resumen:"
echo "   - Pulsar: $PULSAR_STATUS"
echo "   - Publicación: $TEST_STATUS"  
echo "   - Afiliado: $AFFILIATE_ID"
```

**Ejecutar el script**:
```bash
chmod +x test-commissions.sh
./test-commissions.sh
```

---

## 🔍 Diagnóstico de Apache Pulsar

Para verificar que Pulsar está funcionando correctamente, el servicio incluye endpoints especiales de diagnóstico:

### Verificar Estado de Conexión

```bash
# Verificar si el servicio puede conectarse a Pulsar
curl "http://localhost:8081/dev/pulsar/health"
```

**Respuesta esperada**:
```json
{
  "status": "connected",
  "broker_url": "pulsar://broker:6650",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Crear Topics Necesarios

Si tienes el error "Topic not found", ejecuta:

```bash
# Crear todos los topics necesarios
curl -X POST "http://localhost:8081/dev/pulsar/create-topics"
```

**Respuesta esperada**:
```json
{
  "status": "completed",
  "created_topics": [
    "persistent://public/default/comisiones.creadas",
    "persistent://public/default/affiliate-events",
    "persistent://public/default/conversion-events",
    "persistent://public/default/commission-events"
  ],
  "errors": [],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Listar Topics Existentes

```bash
# Ver todos los topics disponibles
curl "http://localhost:8081/dev/pulsar/topics"
```

### Probar Publicación de Eventos

```bash
# Enviar un evento de prueba
curl -X POST "http://localhost:8081/dev/pulsar/test-publish"
```

### Flujo de Diagnóstico Completo

**Si tienes problemas con Pulsar, ejecuta estos comandos en orden:**

```bash
# 1. Verificar que Pulsar está corriendo
docker compose logs broker | tail -20

# 2. Verificar conectividad desde el servicio
curl "http://localhost:8081/dev/pulsar/health"

# 3. Crear topics si no existen
curl -X POST "http://localhost:8081/dev/pulsar/create-topics"

# 4. Verificar que los topics se crearon
curl "http://localhost:8081/dev/pulsar/topics"

# 5. Probar publicación de eventos
curl -X POST "http://localhost:8081/dev/pulsar/test-publish"

# 6. Ahora ejecutar el flujo normal de conversiones
```

---

## 🔧 Troubleshooting y Diagnóstico

### Verificar Estado de los Servicios

```bash
# Estado general de todos los contenedores
docker compose ps

# Logs específicos del servicio de comisiones
docker compose logs -f afiliados-comisiones

# Logs de la base de datos
docker compose logs -f db-afiliados-comisiones

# Logs de Apache Pulsar
docker compose logs -f broker

# Verificar conectividad de red
docker compose exec afiliados-comisiones ping db-afiliados-comisiones
docker compose exec afiliados-comisiones ping broker
```

### Problemas Comunes y Soluciones

#### 1. Error de Conexión a Base de Datos
```bash
# Verificar que PostgreSQL esté corriendo
docker compose exec db-afiliados-comisiones pg_isready -U afiliados

# Reiniciar solo la base de datos
docker compose restart db-afiliados-comisiones

# Verificar variables de entorno
docker compose exec afiliados-comisiones env | grep DATABASE
```

#### 2. Puerto ya en Uso
Si el puerto 8081 está ocupado, puedes cambiarlo en el `docker-compose.yml`:
```yaml
ports:
  - "8082:8080"  # Cambiar 8081 por otro puerto disponible
```

#### 3. Tablas no Creadas
```bash
# Verificar que las tablas existen
docker compose exec db-afiliados-comisiones psql -U afiliados -d afiliados -c "\dt"

# Forzar recreación de tablas (cuidado: borra datos existentes)
docker compose down
docker compose up -d --build
```

#### 4. Eventos no Publicados
```bash
# Verificar logs de eventos
docker compose logs afiliados-comisiones | grep -i event

# Verificar handlers registrados
docker compose logs afiliados-comisiones | grep -i handler

# Verificar conexión a Pulsar
curl http://localhost:8080/admin/v2/brokers/cluster-a

# Ver topics existentes
curl http://localhost:8080/admin/v2/persistent/public/default

# Verificar estadísticas de un topic específico
curl http://localhost:8080/admin/v2/persistent/public/default/comisiones.creadas/stats
```

#### 5. Problemas con Apache Pulsar

**Error común**: `Topic persistent://public/default/comisiones.creadas not found`

**Solución paso a paso**:

```bash
# 1. Verificar que Pulsar está corriendo
curl http://localhost:8080/admin/v2/clusters

# 2. Verificar conectividad desde el servicio
curl "http://localhost:8081/dev/pulsar/health"

# 3. Si la conexión falla, reiniciar Pulsar
docker compose restart broker

# 4. Crear topics necesarios
curl -X POST "http://localhost:8081/dev/pulsar/create-topics"

# 5. Verificar que los topics se crearon
curl "http://localhost:8081/dev/pulsar/topics"
```

**Comandos adicionales de Pulsar**:
```bash
# Verificar que Pulsar está funcionando
curl http://localhost:8080/admin/v2/clusters

# Reiniciar Pulsar si es necesario
docker compose restart broker

# Verificar el cluster de Pulsar
curl http://localhost:8080/admin/v2/brokers/cluster-a

# Limpiar topics (solo para development)
curl -X DELETE http://localhost:8080/admin/v2/persistent/public/default/comisiones.creadas

# Crear topic manualmente si es necesario
curl -X PUT http://localhost:8080/admin/v2/persistent/public/default/comisiones.creadas

# Ver mensajes en un topic (requiere consumer)
docker compose exec broker bin/pulsar-client consume persistent://public/default/comisiones.creadas -s "test-subscription" -n 10
```

### Validación de Datos

#### Consultar Directamente la Base de Datos

```bash
# Conectar a PostgreSQL
docker compose exec db-afiliados-comisiones psql -U afiliados -d afiliados

# Consultas útiles:
SELECT * FROM affiliates;
SELECT * FROM conversion_events;
SELECT * FROM commissions;

# Verificar relaciones
SELECT 
    a.name as affiliate_name,
    ce.event_type,
    ce.amount as conversion_amount,
    c.amount as commission_amount
FROM affiliates a
LEFT JOIN conversion_events ce ON a.id = ce.affiliate_id
LEFT JOIN commissions c ON ce.id = c.conversion_id
ORDER BY ce.occurred_at DESC;
```

#### Endpoints de Salud y Diagnóstico

```bash
# Verificar que la API responde
curl -I http://localhost:8081/docs

# Obtener información de la aplicación (si está implementado)
curl http://localhost:8081/health

# Verificar estructura de la API
curl http://localhost:8081/openapi.json | jq '.paths'

# Verificar estado de Apache Pulsar
curl http://localhost:8080/admin/v2/brokers/health

# Ver configuración del broker
curl http://localhost:8080/admin/v2/brokers/configuration/runtime

# Listar todos los topics
curl http://localhost:8080/admin/v2/persistent/public/default
```

---

## 🎯 Métricas y Monitoreo

### Métricas de Negocio

```bash
# Total de conversiones por afiliado
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>/commissions" | jq '.total_commissions'

# Volumen de comisiones
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>/commissions" | jq '.total_amount'

# Verificar diferentes tipos de eventos
docker compose exec db-afiliados-comisiones psql -U afiliados -d afiliados -c "
SELECT event_type, COUNT(*), SUM(amount) 
FROM conversion_events 
GROUP BY event_type;
"
```

### Logs Estructurados

```bash
# Filtrar logs por nivel
docker compose logs afiliados-comisiones | grep ERROR
docker compose logs afiliados-comisiones | grep WARNING
docker compose logs afiliados-comisiones | grep INFO

# Seguimiento de comandos CQS
docker compose logs afiliados-comisiones | grep -E "(Command|Query|Event)"

# Métricas de performance
docker compose logs afiliados-comisiones | grep -E "(processed|handled|calculated)"

# Logs específicos de Pulsar
docker compose logs broker | grep -E "(producer|consumer|topic)"

# Verificar conexiones a Pulsar
docker compose logs afiliados-comisiones | grep -i pulsar
```

### Métricas de Apache Pulsar

```bash
# Estadísticas generales del broker
curl http://localhost:8080/admin/v2/broker-stats/metrics

# Estadísticas de un topic específico
curl http://localhost:8080/admin/v2/persistent/public/default/comisiones.creadas/stats

# Ver productores activos en un topic
curl http://localhost:8080/admin/v2/persistent/public/default/comisiones.creadas/producers

# Ver consumidores activos
curl http://localhost:8080/admin/v2/persistent/public/default/comisiones.creadas/consumers

# Throughput de mensajes
curl http://localhost:8080/admin/v2/persistent/public/default/comisiones.creadas/stats | jq '.msgRateIn, .msgRateOut'
```

---

## 🔄 Reset y Limpieza

### Limpiar Datos de Prueba

```bash
# Conectar a la base de datos y limpiar tablas
docker compose exec db-afiliados-comisiones psql -U afiliados -d afiliados -c "
DELETE FROM commissions;
DELETE FROM conversion_events;
DELETE FROM affiliates;
"
```

### Reinicio Completo

```bash
# Parar y eliminar contenedores
docker compose down

# Eliminar volúmenes (CUIDADO: elimina todos los datos)
docker compose down -v

# Reconstruir desde cero
docker compose up -d --build
```

### Solo Reiniciar el Servicio

```bash
# Reiniciar solo el servicio de comisiones
docker compose restart afiliados-comisiones

# Ver logs en tiempo real tras reinicio
docker compose logs -f afiliados-comisiones
```

---

## Estructura

```
src/
├── app/
│   └── main.py                 # FastAPI + bootstrap
├── core/
│   └── seedwork/               # Eventos, comandos, bus, UoW, repos (puertos)
├── domains/
│   ├── affiliates/             # Dominio de afiliados (entidad + repo)
│   └── commissions/            # Dominio de comisiones (agregado + eventos + políticas + repos)
├── application/                # Commands/Queries + handlers
├── infrastructure/
│   ├── db/                     # SQLAlchemy + modelos + repos
│   ├── messaging/              # Publicación a Apache Pulsar (eventos de integración)
│   └── config.py               # Carga de configuración
└── entrypoints/
  └── fastapi/                # Rutas / DTOs
```


