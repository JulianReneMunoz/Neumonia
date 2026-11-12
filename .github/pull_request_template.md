## Qué cambia
<!-- Una o dos frases. Enlace a la historia de usuario: HU-0X (docs/M2_propuesta.md) -->

## Por qué

## Cómo se probó
- [ ] `make check` pasa en local (ruff + formato + pytest con cobertura ≥ 80 %)
- [ ] Pruebas nuevas siguen el patrón AAA
- [ ] `make smoke` pasa con el modelo real

## Checklist de arquitectura (Definition of Done)
- [ ] Respeta MVC: la vista no importa `neumonia.model` (lo verifica `tests/test_architecture.py`)
- [ ] Contrato estable: `label`, `probability`, `gradcam_url` intactos (si cambia, actualizar `api/openapi.yaml`)
- [ ] Sin pesos, datos ni secretos en el diff (`*.h5`, `.env`, `kaggle.json`)
- [ ] Documentación actualizada (README / ADR si es una decisión de arquitectura)
- [ ] Declaración de uso de IA: ¿se usó un agente? ¿qué revisó el humano? (`docs/declaracion_uso_ia.md`)

## Revisión (la completa el revisor)
- [ ] Leí el código, no solo el diff de pruebas
- [ ] Probé la funcionalidad en local
