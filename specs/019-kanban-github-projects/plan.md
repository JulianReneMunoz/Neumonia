# Plan · SPEC-019

- **Tablero (`gh`)**: `gh project link 5` vincula el repositorio; `gh project item-add` agrega cada issue y
  PR que aún no está; las opciones de *Status* se reemplazan en orden con la mutación GraphQL
  `updateProjectV2Field` (antes de asignar estados, porque la mutación recrea las opciones);
  `gh project item-edit` asigna la columna; `gh project edit --visibility PUBLIC` lo publica.
- **Copia versionada** (`scripts/kanban_snapshot.py`): `fetch_items` (único punto que llama a `gh`),
  `normalize`, `count_by_column` y `render` son funciones puras y se prueban con dobles en memoria.
- **Makefile**: objetivo `kanban` → `uv run python scripts/kanban_snapshot.py`.
- **Pendiente en la web** (no configurable con `gh`):
  1. Crear la vista *Board* agrupada por *Status*.
  2. Fijar el límite de 3 en la columna *In Progress*.
  3. Activar los workflows «Item closed → Done» y «Pull request merged → Done».
- **Riesgos**: sin el scope `project`, `gh` falla → `gh auth refresh -s project`. La copia es una foto a la
  fecha de corte; se regenera con `make kanban` antes de cada entrega.
