# SPEC-019 · Tablero Kanban en GitHub Projects

## Contexto
El M2 propone gestionar el trabajo con Kanban. Hasta ahora el flujo se veía solo en issues y PR sueltos;
no existía un tablero ni una copia versionada que el curso pudiera revisar sin acceso a GitHub.

## Requisitos
1. Tablero **«Neumonía · Kanban»** (GitHub Projects #5 del usuario `JulianReneMunoz`), público y vinculado
   al repositorio `JulianReneMunoz/Neumonia`.
2. Todos los issues y PR del repositorio (abiertos y cerrados) están en el tablero.
3. El campo *Status* tiene, en este orden: **Backlog · Todo · In Progress · En revisión · Done**.
4. Asignación inicial: issues cerrados y PR fusionados o cerrados → Done; PR abiertos → En revisión;
   issues abiertos → Todo.
5. Política Kanban: definición de cada columna, límite WIP de **3** en *In Progress* y criterio de Done =
   PR fusionado con CI en verde.
6. Copia versionada en `docs/kanban.md`: enlace al tablero, política, conteo por columna, fecha de corte y
   una tabla por columna con número, título, tipo (issue o PR), etiquetas y enlace.
7. `scripts/kanban_snapshot.py` regenera `docs/kanban.md` llamando a `gh` mediante `subprocess`, sin
   dependencias nuevas; objetivo `make kanban`.

## Fuera de alcance
La vista *Board*, el límite WIP visual y los workflows automáticos del tablero: `gh` no los configura y se
activan en la interfaz web (ver `plan.md`).

## Criterios de aceptación
- `tests/test_kanban_snapshot.py`: normalización de ítems, conteo en el orden del tablero (incluidas
  columnas vacías), contenido del documento (enlace, política, tablas, total, fecha) y aviso de WIP excedido.
- `make kanban` produce `docs/kanban.md` con los datos reales del tablero.
- El README enlaza `docs/kanban.md` y el tablero desde la sección de entregables.
