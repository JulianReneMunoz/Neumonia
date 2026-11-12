# Settings

> God node · 21 connections · `src/neumonia/config.py`

**Community:** [Community 17](Community_17.md)

## Connections by Relation

### contains
- config.py `EXTRACTED`

### imports
- app.py `EXTRACTED`
- gateways.py `EXTRACTED`
- server.py `EXTRACTED`
- factory.py `EXTRACTED`

### method
- .from_env() `EXTRACTED`
- .__post_init__() `EXTRACTED`

### rationale_for
- Parámetros de ejecución. Inmutable para que nadie la modifique en caliente. `EXTRACTED`

### references
- get_settings() `EXTRACTED`
- Resultados (12/11/2026) `INFERRED`
- .__init__() `EXTRACTED`

### uses
- [create_app()](create_app.md) `INFERRED`
- build_service() `INFERRED`
- build_gateway() `INFERRED`
- create_server() `INFERRED`
- PneumoniaDetectorServicer `INFERRED`
- settings() `INFERRED`
- test_settings_validation() `INFERRED`
- real_service() `INFERRED`
- test_build_gateway_uses_http_when_api_url_set() `INFERRED`
- test_settings_from_env() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*