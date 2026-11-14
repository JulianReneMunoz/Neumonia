# Plan · SPEC-015

## Diseño
- Un paso `run` en el job `docker` de `.github/workflows/ci.yml`, justo después del checkout y antes de
  «Build imagen CPU»: `df -h /`, `sudo rm -rf` de las 4 rutas, `docker system prune -af`, `df -h /`.
- `tests/test_ci_workflow.py`: lee el YAML como texto (sin dependencias nuevas) y verifica el orden de los
  pasos y los comandos (AC1).

## Decisiones
| Decisión | Por qué | Alternativa descartada |
|---|---|---|
| Borrar herramientas preinstaladas que no se usan | Libera decenas de GB en segundos sin tocar la imagen | Reducir la imagen (más trabajo, otro alcance) |
| Comandos propios en vez de una acción de terceros | Sin dependencias nuevas en la cadena de suministro del CI | `jlumbroso/free-disk-space` |
| Prueba sobre el texto del YAML | No agrega PyYAML; basta con el orden de los pasos | Parsear el YAML |

## Riesgos
Si GitHub cambia las rutas preinstaladas, `rm -rf` no falla (rutas inexistentes) pero libera menos espacio:
el `df -h /` del log lo deja ver.

## Pruebas
pytest para AC1; el CI de la propia PR para AC2; la PR #9 reabierta para AC3.
