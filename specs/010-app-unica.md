# Spec 010 · Aplicación única (radiografía + tomografía en el mismo puerto)

Historia **HU-13**: *Como médico quiero abrir una sola aplicación y pasar de la radiografía a la tomografía
desde el menú lateral.* Decisión: [ADR-0012](../docs/adr/0012-app-unica-multipagina.md). Estado: hecho (nivel 1).

| # | Criterio de aceptación | Prueba (`tests/test_app_unica.py`) |
|---|---|---|
| 1 | Las páginas apuntan a las vistas existentes (`streamlit_app.py`, `ct_app.py`) | `test_pages_point_to_the_existing_views` |
| 2 | Radiografía es la página por defecto; las URL son únicas; la tomografía se rotula como prototipo | `test_radiography_is_the_only_default_page_and_urls_are_unique` |
| 3 | La app abre en radiografía y cambia a tomografía sin errores, incluso sin modelo ni casos | `test_unified_app_runs_both_pages` |
| 4 | La entrada no importa modelo ni controlador (MVC) | `test_architecture.py` |

**Nivel 2 (pendiente)**: paciente compartido entre páginas e informe PDF único.
