# ADR-0006 · MLflow con backend SQLite

- **Estado**: aceptado · **Fecha**: 2026-11-12

## Contexto
MLflow 3 dejó el *file store* (`./mlruns`) en modo mantenimiento y lanza una excepción salvo con
`MLFLOW_ALLOW_FILE_STORE=true`.

## Decisión
`MLFLOW_TRACKING_URI=sqlite:///mlflow.db` por defecto en local y servidor MLflow con SQLite + volumen en Docker
Compose (perfil `mlops`). `MlflowTracker` detrás del protocolo `Tracker` (DIP); `NullTracker` si MLflow no está.

## Consecuencias
- (+) Compatible con versiones actuales de MLflow; un solo archivo fácil de respaldar.
- (−) SQLite no es para concurrencia alta; en un equipo grande se migraría a PostgreSQL sin cambiar el código.
