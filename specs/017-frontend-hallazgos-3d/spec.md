# SPEC-017 · Informe detallado y vista 3D en el frontend desacoplado

**Historia**: Como usuario clínico, quiero ver en el frontend el informe de hallazgos y la vista 3D de la
atención del modelo, para tener la misma información que ofrecía la app interna sin depender de Streamlit.

## Problema
La API ya devuelve `findings` (atención por zona, lateralidad, extensión, atención fuera del pulmón, alerta
de atajo, resumen y la rejilla Grad-CAM 31×31), pero el frontend desacoplado (SPEC-012) solo muestra el
resultado. El informe y la vista 3D existen únicamente en la app Streamlit, que no se usa en la demo del M3.

## Requisitos
- RF1. Pestañas «Resultado», «Informe detallado» y «Vista 3D» en el estado *success*.
- RF2. Informe: resumen, alerta de atajo, tabla de zonas con la dominante marcada, lateralidad, extensión,
  atención fuera del pulmón (con razón) y fuente de la segmentación.
- RF3. Vista 3D: superficie de la rejilla de atención, rotable con el ratón, sin librerías externas.
- RF4. Sin `findings`, ambas pestañas muestran un aviso y no fallan.
- RNF. Sin cambios en la API ni en el contrato; textos con `textContent`; aclaración de que la vista 3D no
  reconstruye el pulmón.

## Criterios de aceptación (Given-When-Then)
| # | Criterio | Prueba |
|---|---|---|
| 1 | Dado el cliente, entonces declara las tres pestañas y la vista 3D usa canvas sin dependencias externas | `tests/test_frontend_desacoplado.py::test_frontend_has_report_and_3d_tabs` |
| 2 | Dada una respuesta con `findings`, cuando se abre «Informe detallado», entonces aparecen zonas, lateralidad y alerta | E2E (plan.md) |
| 3 | Dada una respuesta con `findings`, cuando se abre «Vista 3D», entonces se dibuja la superficie y rota al arrastrar | E2E (plan.md) |
| 4 | Dada una respuesta sin `findings`, entonces las pestañas muestran un aviso | E2E (plan.md) |

## Fuera de alcance
Tomografía 3D en el frontend (requiere un endpoint nuevo para las mallas del caso).
