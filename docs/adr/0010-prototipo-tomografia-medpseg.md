# ADR-0010 · Prototipo de tomografía: reconstrucción 3D real con MEDPSeg

- **Estado**: experimental (rama `feature/prototipo-tomografia`) · **Fecha**: 2026-11-12

## Contexto
Con radiografías no se puede reconstruir la anatomía en 3D: una placa es una proyección 2D
(ADR-0007). Se pidió una vista como las de TotalSegmentator: pulmones, vía aérea, vasos y la lesión
**del paciente** en 3D, con su porcentaje por lóbulo. Eso exige **tomografía (CT)**, que es un
volumen. El caso del curso es la radiografía; esto se construye como prototipo aparte, sin tocar la
app principal.

Opciones evaluadas:

| Opción | Resultado |
|---|---|
| Entrenar un segmentador de lesiones en CT | Días/semanas y GPU; fuera de alcance |
| TotalSegmentator | Lóbulos, vía aérea y vasos (abiertos, Apache-2.0), pero **no** lesiones de neumonía |
| **MEDPSeg** (Carmo et al., SPIE Medical Imaging 2026; MIT) | Preentrenado con más de 6000 CT: pulmón izq./der., lesión, vidrio esmerilado, consolidación, vía aérea, arteria pulmonar y **lóbulos** en una sola herramienta |

## Decisión
1. **MEDPSeg en su propio entorno** (`make ct-setup`: commit fijo, pesos con SHA-256, uv). Usa
   PyTorch 2.8; la app nunca lo importa: lo invoca como **proceso externo** con
   `model/medpseg_runner.py`, que llama al pipeline sin su GUI (el comando `medpseg_cpu` importa
   Tkinter y falla en servidores).
2. **Remuestreo a 1.5 mm** antes de segmentar (configurable): baja memoria y tiempo en CPU
   (MEDPSeg pide 16 GB de RAM a resolución completa).
3. **Informe cuantitativo** (`controller/ct_analysis.py`): volúmenes, % de cada pulmón y lóbulo con
   lesión, vidrio esmerilado vs. consolidación y **puntaje de severidad tomográfica** por lóbulo
   (0–5, total 0–25). Siempre con la nota "prototipo sin validación clínica".
4. **Mallas 3D** con *marching cubes* (scikit-image) en RAS+ y vista anterior (el derecho del paciente
   a la izquierda), y cortes axial/coronal con la lesión superpuesta.
5. **Caché por caso** (`.npz` de pocos MB): la segmentación (minutos en CPU) se hace antes con
   `make ct-precompute`; la demo (`make ui-ct`) carga al instante y no necesita MEDPSeg.
6. **App separada** (`view/ct_app.py`, puerto 8502). Extra `ct` liviano (nibabel + scikit-image),
   instalado por defecto; MVC respetado: la vista pide el segmentador al controlador.

## Verificación con datos reales
Tomografía de tórax de prueba (repositorio de TotalSegmentator, sana): volúmenes de MEDPSeg
reproducidos (derecho 2126 vs. 2092 mL; lesión 0.34 % vs. 0.33 %), lóbulos 1–2 en el pulmón izquierdo
y 3–5 en el derecho, corte coronal con el corazón a la izquierda del paciente, puntaje 0/25.

## Consecuencias
- (+) Reconstrucción 3D **real** de la lesión del paciente, cuantificada por lóbulo, sin entrenar nada.
- (+) Aislado: no cambia la API, la app de radiografía, Docker ni el contrato.
- (−) Lento en CPU: medido 29 min para una tomografía de 233×167×191 a 1.5 mm con 2 núcleos
  (≈ 7 s por corte, pico de ≈ 3.5 GB de RAM); con GPU, segundos. Por eso la caché (1.4 MB por caso,
  se construye en 1 s) y la demo precalculada.
- (−) MEDPSeg marca densidades mínimas incluso en pulmones sanos (0.25 % en la tomografía de prueba):
  se aplica un umbral de ruido del 1 % por lóbulo para el puntaje de severidad.
- (−) El archivo de lóbulos de MEDPSeg (guardado con MONAI) trae metadatos de orientación
  inconsistentes; se usa la geometría del archivo de pulmones, que comparte la rejilla de vóxeles.
- (−) Sin validación local: hay que medir contra las máscaras de radiólogos del dataset
  COVID-19-CT-Seg (20 CT, Zenodo 3757476, CC BY-NC-SA) antes de reportar cifras.
- (−) Pesos y datos con licencias propias (MEDPSeg MIT; dataset no comercial): no se versionan.
