# SPEC-018 · Tomografía 3D en el frontend desacoplado

## Contexto
La pestaña «Vista 3D» del frontend HTML/JS (SPEC-017) solo mostraba la superficie de atención
Grad-CAM de la radiografía. La reconstrucción 3D de pulmones y lesión existía únicamente en la
página Streamlit de tomografía, que no puede usarse en la demo M3 (Anuncio 007).

## Requisitos
1. La API expone, en solo lectura, los casos de tomografía ya procesados con MEDPSeg (caché `.npz`):
   - `GET /ct/cases` → lista de casos disponibles.
   - `GET /ct/cases/{case_id}` → mallas (vértices y caras, mm, RAS+) e informe volumétrico por lóbulo;
     404 si el caso no está en la caché (no se aceptan rutas arbitrarias).
   - `GET /vendor/plotly.min.js` → Plotly.js del paquete instalado, para funcionar sin internet.
2. La pestaña «Vista 3D» abre por defecto «Tomografía 3D: pulmones y lesión»: pulmones, vía aérea,
   arterias pulmonares, vidrio esmerilado y consolidación, con los mismos colores, cámara anterior y
   rótulos DERECHO / IZQUIERDO que la vista Streamlit.
3. Debajo de la figura: % de pulmón comprometido, mL de lesión, vidrio esmerilado, consolidación,
   volumen pulmonar, severidad /25, resumen y tabla por lóbulo.
4. La vista de atención Grad-CAM se conserva como segunda opción.
5. Se indica que el caso de tomografía es una demostración precalculada y no corresponde a la
   radiografía cargada.

## Fuera de alcance
Procesar tomografías nuevas desde el frontend (MEDPSeg tarda minutos; sigue en `make ct-precompute`).

## Criterios de aceptación
- Pruebas de API para los tres endpoints, incluido el 404.
- Prueba estática del frontend (sin CDN externo).
- E2E con Playwright: la figura dibuja 5 trazas para `covid_ejemplo` sin errores de consola.
- `test_architecture` sigue pasando (la API no importa `neumonia.view`).
