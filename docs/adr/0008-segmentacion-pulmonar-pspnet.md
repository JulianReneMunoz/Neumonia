# ADR-0008 · Segmentación pulmonar real con PSPNet (TorchXRayVision), opcional y aislada

- **Estado**: propuesto (rama `feature/segmentacion-pulmonar`) · **Fecha**: 2026-11-12
- **Reemplaza en parte**: las zonas geométricas de ADR-0007 (que quedan como respaldo)

## Contexto
ADR-0007 resume la atención del modelo en seis zonas **geométricas** (rectángulos fijos). En placas
reales el pulmón no ocupa esos rectángulos: el fondo, los hombros o el corazón quedan "dentro" y
partes del pulmón quedan "fuera". Eso distorsiona las zonas, la extensión y la alerta de atajo.

Se evaluaron opciones (ver la hoja de ruta de la sustentación M3):

| Opción | Resultado |
|---|---|
| SAM 3 (Meta) con texto ("lung") | 860 M de parámetros, GPU en la práctica, licencia SAM; en datos médicos rinde mal sin cajas guía. Reservado para refinar cajas de un detector (fase 3) |
| U-Net propia (JSRT / Montgomery / Shenzhen) | Muy buena, pero exige entrenar y validar (días, GPU) |
| **PSPNet preentrenada de TorchXRayVision** | 14 estructuras torácicas a 512×512 (incluye pulmón derecho e izquierdo), sin entrenar, CPU ≈ 3 s/imagen |

## Decisión
1. **Estrategia `LungSegmenter`** (`model/lung_segmentation.py`) con tres implementaciones:
   `GeometricLungSegmenter` (por defecto, sin dependencias), `XrvLungSegmenter` (PSPNet) y el
   decorador `QualityCheckedSegmenter`, que vuelve al geométrico si la segmentación falla o no es
   plausible, y deja la razón en el informe.
2. **Control de calidad**: cada pulmón ≥ 4 % de la imagen, ambos ≥ 12 %, el derecho del paciente a la
   izquierda de la imagen y sin superposición. Las zonas se calculan en tercios de la **altura de
   cada pulmón**.
3. **Aislamiento de proceso** (`IsolatedLungSegmenter` + `python -m neumonia.model.lung_worker`):
   TensorFlow y las compilaciones de PyTorch que traen `triton` registran las mismas opciones de LLVM
   y el proceso aborta ("LLVM ERROR: inconsistency in registered CommandLine options"). PSPNet corre
   en un proceso hijo persistente, comunicado por tuberías; si muere, se recrea.
4. **Dependencia opcional**: extra `seg` (`torchxrayvision`, que trae PyTorch). No entra en CI, Docker
   ni `make install`. Se activa con `make seg` y `NEUMONIA_LUNG_SEGMENTER=pspnet` (`make ui-seg`).
5. **Integridad**: los pesos (`pspnet_chestxray_best_model_4.pth`, 273 MB) se verifican con SHA-256,
   igual que `conv_MLP_84.h5`.
6. **Convención anatómica verificada**: en TorchXRayVision "Right Lung" es el pulmón derecho del
   **paciente**, que aparece a la izquierda de la imagen (centroides x ≈ 0.3 y 0.65 en las muestras).

## Consecuencias
- (+) Zonas, extensión y alerta de atajo sobre la silueta real del paciente; la vista muestra el
  contorno para que el médico verifique la segmentación.
- (+) Sin riesgo para lo existente: por defecto todo sigue igual; si falta el extra o la segmentación
  no es confiable, el informe lo dice y usa las zonas geométricas.
- (−) **Limitación clínica clave**: la consolidación densa (justo la neumonía) se parece a tejido
  blando y la red tiende a recortar esa parte del pulmón. En `viral (3).dcm` (pediátrica, rotada,
  opacidad basal) un pulmón ocupa solo el 2 % y el control de calidad la descarta.
- (−) Más peso: PyTorch (cientos de MB en CPU) y 273 MB de pesos; primera predicción ≈ 10 s
  (arranque del proceso hijo), luego ≈ 3 s adicionales por imagen en CPU.
- (−) Sigue sin localizar lesiones: segmenta **pulmones**. La lesión requiere la fase 3 (detector
  entrenado con las cajas de RSNA + SAM 3 con caja).

## Verificación
`tests/test_segmentacion_pulmonar.py` (spec 006), reglas de arquitectura (PyTorch solo perezoso y
nunca en vista/controlador) y prueba real con PSPNet marcada `model` (se omite sin el extra).
