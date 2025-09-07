# Afiliados — Comisiones por Evento (DDD + EDA + Hexagonal)

Servicio base en **Python** con **arquitectura hexagonal**, **DDD**, **eventos de dominio** y **CQS**.
Implementa el dominio de _afiliados_ y _comisiones por evento_ con persistencia real en **PostgreSQL**
y publicación de eventos de integración vía **RabbitMQ**.

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
- **Event-driven**: Publicación de eventos de **integración** en RabbitMQ (`comisiones.creadas`) y
  **eventos de dominio** in-process entre módulos.
- **Configuración**: `.env` + variables de entorno.
- **Docker Compose**: Postgres, RabbitMQ y servicio.

## Correr con Docker

```bash
docker compose up -d --build
```

- API: `http://localhost:8080/docs`
- RabbitMQ Console: `http://localhost:15672` (guest/guest)
- Postgres: `localhost:5432`

> Al iniciar el servicio se **auto-crean** las tablas si no existen.

### Probar rápidamente

**Crear un afiliado de ejemplo** (endpoint utilitario):

```bash
curl -X POST http://localhost:8080/dev/seed_affiliate   -H "Content-Type: application/json"   -d '{"id":"4c131185-068f-4387-9220-6dd9a2fe95cd","nombre":"Alice","tasa_comision":12.5}'
```

**Registrar una conversión (Comando CQS):**

```bash
curl -X POST http://localhost:8080/conversions   -H "Content-Type: application/json"   -d '{"affiliate_id":"<UUID_DEL_AFILIADO>","event_type":"COMPRA","monto":199.99,"moneda":"USD"}'
```

**Consultar comisiones por afiliado (Consulta CQS):**

```bash
curl "http://localhost:8080/affiliates/<UUID_DEL_AFILIADO>/commissions?desde=&hasta="
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
│   ├── messaging/              # Publicación a RabbitMQ (eventos de integración)
│   └── config.py               # Carga de configuración
└── entrypoints/
  └── fastapi/                # Rutas / DTOs
```


