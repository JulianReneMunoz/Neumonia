# Declaración de uso de IA

El proyecto se desarrolló con **asistencia de agentes de código en consola** (Claude Code), siguiendo el flujo
*especificación → prueba → código → compuerta → revisión humana* descrito en `docs/metodologias.md` §23.

## Qué hizo el agente
- Propuso la estructura MVC, el código de `src/neumonia/`, las pruebas, los scripts, Docker y CI/CD.
- Buscó y comparó datasets y la fuente pública del modelo (`docs/dataset.md`).
- Redactó borradores de la documentación (metodologías, M2, Model Card, ADR).

## Qué verificó el equipo (humanos)
- [ ] Ejecutó `make check` y `make smoke` en su máquina (Windows, `C:\Neumonia`).
- [ ] Revisó línea a línea `model/preprocessing.py`, `model/gradcam.py` y `controller/decision.py`.
- [ ] Validó las cifras de la Model Card contra MLflow (`run_id`: __________).
- [ ] Revisó licencias del modelo y del dataset.
- [ ] Ajustó la propuesta M2 (equipo, roles, BMC) a su contexto real.
- [ ] Aprobó cada PR (el agente no hace *merge*).

## Controles que limitan al agente
`.claude/settings.json` (permisos), `.claude/hooks/guard_bash.py` (bloquea `pip`, pesos, secretos y *push*
forzado), `tests/test_architecture.py` (reglas MVC) y las compuertas de CI.

## Responsabilidad
Los integrantes son autores y responsables del contenido entregado. Toda afirmación sobre desempeño del
modelo proviene de ejecuciones reproducibles registradas en MLflow.

| Integrante | Firma / fecha |
|---|---|
| | |
