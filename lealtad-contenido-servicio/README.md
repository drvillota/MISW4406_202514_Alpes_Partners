# Afiliados — Comisiones por Evento (DDD + EDA + Hexagonal)

Servicio base en **Python** con **arquitectura hexagonal**, **DDD**, **eventos de dominio** y **CQS**.
Implementa el dominio de afiliados y contenidos con persistencia real en **Postgres**
y publicación de eventos de integración vía **Pulsar**.

> **Módulos internos (bounded modules) y comunicación por eventos de dominio**
>
> - **Tracking** (contenido): emite `ContenidoRegistrado` (evento de dominio).
> - **Publicar**: escucha `ContenidoRegistrado`, define si publica y persiste estado `Contenido`, y emite `ContenidoPublicado`.
>

---

## Arquitectura

- **Hexagonal (Ports & Adapters)**: capas `domain` / `application` / `infrastructure` + `entrypoints` (FastAPI).
- **DDD**: 
  - Agregados (Afiliado, Contenido)
  - Entidades
  - Repositorios (puertos)
  - Implementaciones (adaptadores).
- **CQS**:
  - **Comando**: `RegistrarContenidoCommand`
  - **Consulta**: `ConsultarContenidoPublicadoQuery`
  - **Eventos**: `ContenidoRegistrado`, `ContenidoPublicado`
- **Persistencia real**: **Postgres** con SQLAlchemy 
- **Event-driven**: Publicación de eventos de **integración** en Pulsar (`contenido.publicado`) y
  **eventos de dominio** in-process entre módulos.
- **Configuración**: `.env` + variables de entorno.
- **Docker Compose**: Postgres, Pulsar y servicio.

## Correr con Docker

### Iniciar el Servicio

```bash
# Navegar al directorio del proyecto
cd MISW4406_202514_Alpes_Partners

# Iniciar solo el servicio de lealtad-contenido con sus dependencias
docker compose --profile lealtad-contenido up -d --build

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
docker compose logs lealtad-contenido

# Verificar que la API responde
curl http://localhost:8081/docs

# Verificar que Pulsar está funcionando
curl http://localhost:8080/admin/v2/clusters
```

---

## Prueba de Concepto - Publicación de contenido auténtico

Esta sección demuestra el **flujo completo** del servicio de contenido, desde la creación de afiliados hasta publicación de contenido auténtico.

### Paso 1: Crear un Afiliado

**Endpoint**: `POST /dev/seed_affiliate`

```bash
curl -X POST "http://localhost:8081/dev/seed_affiliate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pepito Pérez",
    "email": "pepito.perez@empresa.com",
    "commission_rate": 15.0,
    "leal": "Si"
  }'
```

**Respuesta esperada**:
```json
{
  "affiliate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

> **Guarda el `affiliate_id`** devuelto para los siguientes pasos.

### Paso 2: Registrar un contenido

**Endpoint**: `POST /contents`

```bash
# Reemplaza <AFFILIATE_ID> con el ID obtenido en el paso anterior
curl -X POST "http://localhost:8081/contents" \
  -H "Content-Type: application/json" \
  -d '{
    "affiliate_id": "<AFFILIATE_ID>",
    "titulo":"Titulo test 1",
    "contenido":"Contenido test 1",
    "tipo":"Testimonio"
  }'
```

**Respuesta esperada**:
```json
{
  "message": "Content registered successfully",
  "content_id": "b2c3d4e5-f6g7-8901-bcde-f23456789012"
}
```

**Lo que sucede internamente**:
1. Se registra el evento de contenido en la base de datos
2. Se emite un evento de dominio `ContenidoRegistrado`
3. El módulo de contenidos escucha el evento
4. Se define si se publica el contenido basado en la lealtad del afiliado
5. Se persiste el estado de la publicación del contenido en la base de datos
6. Se emite un evento `ContenidoPublicado` para integración

### Paso 3: Consultar contenido auténtico publicado por afiliado

**Endpoint**: `GET /affiliates/{affiliate_id}/commissions`

```bash
# Reemplaza <AFFILIATE_ID> con el ID del afiliado
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>/contents"
```

**Respuesta esperada**:
```json
{
  "affiliate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "titulo":"Titulo test 1",
  "contenido":"Contenido test 1",
  "tipo":"Testimonio",
  "publicar": "Si",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Paso 4: Registrar Múltiples Contenidos (Prueba de Volumen)

```bash
# Contenido de registro (evento diferente)
curl -X POST "http://localhost:8081/contents" \
  -H "Content-Type: application/json" \
  -d '{
    "affiliate_id": "<AFFILIATE_ID>",
    "titulo":"Titulo test 2",
    "contenido":"Contenido test 2",
    "tipo":"Reseña"
  }'

# Otro registro
curl -X POST "http://localhost:8081/contents" \
  -H "Content-Type: application/json" \
  -d '{
    "affiliate_id": "<AFFILIATE_ID>",
    "titulo":"Titulo test 3",
    "contenido":"Contenido test 3",
    "tipo":"Testimonio"
  }'
```

### Paso 5: Consultar Contenidos Filtrados por Fecha

```bash
# Consultar contenidos publicados desde una fecha específica
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>/contents?desde=2024-01-01T00:00:00Z"

# Consultar contenidos publicados en un rango de fechas
curl "http://localhost:8081/affiliates/<AFFILIATE_ID>/contents?desde=2024-01-01T00:00:00Z&hasta=2024-01-31T23:59:59Z"
```

### Paso 6: Crear Múltiples Afiliados para Pruebas Avanzadas

```bash
# Afiliado leal
curl -X POST "http://localhost:8081/dev/seed_affiliate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tatiana Sánchez",
    "email": "tatiana.sanchez@premium.com",
    "commission_rate": 25.0,
    "leal": "Si"
  }'

# Afiliado no leal
curl -X POST "http://localhost:8081/dev/seed_affiliate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Martha Díaz",
    "email": "martha.diaz@startup.com",
    "commission_rate": 8.5,
    "leal": "No"
  }'
```

---

## Resultados Esperados

Después de ejecutar todas las pruebas, deberías ver:

### En la Base de Datos

**Tabla `affiliates`**: Afiliados creados con diferentes tasas de comisión
**Tabla `content_events`**: Eventos de contenido registrados

### En los Logs del Servicio

```bash
docker compose logs lealtad-contenido | grep -E "(Processing content|Command created|Event published)"
```

Deberías ver logs similares a:
```
lealtad-contenido | INFO:     Processing content for affiliate: a1b2c3d4-e5f6-7890...
lealtad-contenido | INFO:     Command created: RegistrarContentCommand
lealtad-contenido | INFO:     Event published: ContentRegistrado
lealtad-contenido | INFO:     Publicated content: Si
lealtad-contenido | INFO:     Event published: ContentPublicado
```

### En Apache Pulsar (Eventos de Integración)

1. Accede a `http://localhost:8080/admin/v2/persistent` (Pulsar Admin API)
2. Verifica los topics creados:
   ```bash
   curl http://localhost:8080/admin/v2/persistent/public/default
   ```
3. Deberías ver topics relacionados con `afiliados.conversiones` y `contenidos.creados`
4. Para ver mensajes en un topic específico:
   ```bash
   curl http://localhost:8080/admin/v2/persistent/public/default/contenidos.creados/stats
   ```

---

## 🛠 Script de Prueba Automatizado

Para facilitar las pruebas, aquí tienes un script completo:

```bash
#!/bin/bash

echo "Iniciando prueba de concepto - Comisiones por Evento"

# Verificar conexión a Pulsar
echo "🔍 Paso 0: Verificando conexión a Pulsar..."
PULSAR_HEALTH=$(curl -s "http://localhost:8081/dev/pulsar/health")
PULSAR_STATUS=$(echo $PULSAR_HEALTH | jq -r '.status')

if [ "$PULSAR_STATUS" != "connected" ]; then
    echo "Pulsar no conectado. Intentando crear topics..."
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
    "commission_rate": 12.5,
    "leal": "Si"
  }')

AFFILIATE_ID=$(echo $AFFILIATE_RESPONSE | jq -r '.affiliate_id')
echo "Afiliado creado: $AFFILIATE_ID"

# Probar publicación de eventos
echo "📡 Paso 1.5: Probando publicación de eventos..."
TEST_PUBLISH=$(curl -s -X POST "http://localhost:8081/dev/pulsar/test-publish")
TEST_STATUS=$(echo $TEST_PUBLISH | jq -r '.status')
echo "Estado de publicación: $TEST_STATUS"

# Registrar contenido
echo "Paso 2: Registrando contenido..."
CONVERSION_RESPONSE=$(curl -s -X POST "http://localhost:8081/contents" \
  -H "Content-Type: application/json" \
  -d "{
    \"affiliate_id\": \"$AFFILIATE_ID\",
    \"titulo\": \"Titulo test 4\",
    \"contenido\": \"Contenido test 4\",
    \"tipo\": \"Reseña\"
  }")

echo "Contenido registrado"
echo "📄 Respuesta: $CONTENT_RESPONSE"

# Esperar procesamiento
echo "Esperando procesamiento de eventos..."
sleep 3

# Verificar topics creados
echo "Verificando topics de Pulsar..."
TOPICS_RESPONSE=$(curl -s "http://localhost:8081/dev/pulsar/topics")
echo $TOPICS_RESPONSE | jq '.count, .topics[]' 2>/dev/null || echo "Topics: $TOPICS_RESPONSE"

# Consultar contenidos
echo "Paso 3: Consultando contenidos generados..."
CONTENTS=$(curl -s "http://localhost:8081/affiliates/$AFFILIATE_ID/contents")
echo $CONTENTS | jq '.' 2>/dev/null || echo "Contenidos: $CONTENTS"

echo "🎉 Prueba completada exitosamente!"
echo "Resumen:"
echo "   - Pulsar: $PULSAR_STATUS"
echo "   - Publicación: $TEST_STATUS"  
echo "   - Afiliado: $AFFILIATE_ID"
```

**Ejecutar el script**:
```bash
chmod +x test-commissions.sh
./test-contents.sh
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
    "persistent://public/default/contenidos.creados",
    "persistent://public/default/affiliate-events",
    "persistent://public/default/content-events"
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

## Troubleshooting y Diagnóstico

### Verificar Estado de los Servicios

```bash
# Estado general de todos los contenedores
docker compose ps

# Logs específicos del servicio de contenidos
docker compose logs -f lealtad-contenido

# Logs de la base de datos
docker compose logs -f db-lealtad-contenido

# Logs de Apache Pulsar
docker compose logs -f broker

# Verificar conectividad de red
docker compose exec lealtad-contenido ping db-lealtad-contenido
docker compose exec lealtad-contenido ping broker
```

### Problemas Comunes y Soluciones

#### 1. Error de Conexión a Base de Datos
```bash
# Verificar que PostgreSQL esté corriendo
docker compose exec db-lealtad-contenido pg_isready -U afiliados

# Reiniciar solo la base de datos
docker compose restart db-lealtad-contenido

# Verificar variables de entorno
docker compose exec lealtad-contenido env | grep DATABASE
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
docker compose exec db-lealtad-contenido psql -U afiliados -d afiliados -c "\dt"

# Forzar recreación de tablas (cuidado: borra datos existentes)
docker compose down
docker compose up -d --build
```

#### 4. Eventos no Publicados
```bash
# Verificar logs de eventos
docker compose logs lealtad-contenido | grep -i event

# Verificar handlers registrados
docker compose logs lealtad-contenido | grep -i handler

# Verificar conexión a Pulsar
curl http://localhost:8080/admin/v2/brokers/cluster-a

# Ver topics existentes
curl http://localhost:8080/admin/v2/persistent/public/default

# Verificar estadísticas de un topic específico
curl http://localhost:8080/admin/v2/persistent/public/default/contenidos.creados/stats
```

#### 5. Problemas con Apache Pulsar

**Error común**: `Topic persistent://public/default/contenidos.creados not found`

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
curl -X DELETE http://localhost:8080/admin/v2/persistent/public/default/contenidos.creados

# Crear topic manualmente si es necesario
curl -X PUT http://localhost:8080/admin/v2/persistent/public/default/contenidos.creados

# Ver mensajes en un topic (requiere consumer)
docker compose exec broker bin/pulsar-client consume persistent://public/default/contenidos.creados -s "test-subscription" -n 10
```

### Validación de Datos

#### Consultar Directamente la Base de Datos

```bash
# Conectar a PostgreSQL
docker compose exec db-lealtad-contenido psql -U afiliados -d afiliados

# Consultas útiles:
SELECT * FROM affiliates;
SELECT * FROM contents;

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

### Logs Estructurados

```bash
# Filtrar logs por nivel
docker compose logs lealtad-contenido | grep ERROR
docker compose logs lealtad-contenido | grep WARNING
docker compose logs lealtad-contenido | grep INFO

# Seguimiento de comandos CQS
docker compose logs lealtad-contenido | grep -E "(Command|Query|Event)"

# Métricas de performance
docker compose logs lealtad-contenido | grep -E "(processed|handled|calculated)"

# Logs específicos de Pulsar
docker compose logs broker | grep -E "(producer|consumer|topic)"

# Verificar conexiones a Pulsar
docker compose logs lealtad-contenido | grep -i pulsar
```

### Métricas de Apache Pulsar

```bash
# Estadísticas generales del broker
curl http://localhost:8080/admin/v2/broker-stats/metrics

# Estadísticas de un topic específico
curl http://localhost:8080/admin/v2/persistent/public/default/contenidos.creados/stats

# Ver productores activos en un topic
curl http://localhost:8080/admin/v2/persistent/public/default/contenidos.creados/producers

# Ver consumidores activos
curl http://localhost:8080/admin/v2/persistent/public/default/contenidos.creados/consumers

# Throughput de mensajes
curl http://localhost:8080/admin/v2/persistent/public/default/contenidos.creados/stats | jq '.msgRateIn, .msgRateOut'
```

---

## Reset y Limpieza

### Limpiar Datos de Prueba

```bash
# Conectar a la base de datos y limpiar tablas
docker compose exec db-lealtad-contenido psql -U afiliados -d afiliados -c "
DELETE FROM contents;
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
docker compose restart lealtad-contenido

# Ver logs en tiempo real tras reinicio
docker compose logs -f lealtad-contenido
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
│   └── contents/               # Dominio de contenidos (agregado + eventos + políticas + repos)
├── application/                # Commands/Queries + handlers
├── infrastructure/
│   ├── db/                     # SQLAlchemy + modelos + repos
│   ├── messaging/              # Publicación a Apache Pulsar (eventos de integración)
│   └── config.py               # Carga de configuración
└── entrypoints/
  └── fastapi/                # Rutas / DTOs
```
