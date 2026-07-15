# Observability Stack (OpenTelemetry + Prometheus + Grafana + Jaeger)

Start stack:

```bash
cd /app/observability
docker compose -f docker-compose.observability.yml up -d
```

UIs:

- Jaeger: `http://localhost:16686`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3005` (admin/admin)

Backend env for OTLP exporter:

- `OTEL_ENABLED=true`
- `OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317`
- `OBSERVABILITY_SERVICE_NAME=realaicoach-backend`

Frontend OTLP HTTP exporter (optional):

- `REACT_APP_OTEL_EXPORTER_OTLP_HTTP=http://localhost:4318/v1/traces`
