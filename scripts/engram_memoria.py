"""Siembra la memoria persistente del proyecto en Engram (decisiones, arquitectura, hallazgos).

Engram (Gentleman Programming) da memoria entre sesiones a los agentes de código vía MCP.
Este script es la **fuente versionada** de esa memoria: cada entrada se revisa por PR como el código.

Uso (requiere el binario `engram` en el PATH):
    uv run python scripts/engram_memoria.py            # guarda en la BD local y exporta a .engram/
    engram sync --import                               # en otra máquina: importa .engram/chunks
    engram search "umbral" --project neumonia          # consultar

Tipos de Engram: decision | architecture | bugfix | pattern | config | discovery | learning.
`topic` es estable: volver a ejecutar actualiza la memoria en vez de duplicarla.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = "neumonia"
ROOT = Path(__file__).resolve().parents[1]

MEMORIAS: list[tuple[str, str, str, str]] = [
    # (tipo, topic_key, título, contenido)
    (
        "architecture",
        "architecture/mvc-estrategia-dip",
        "Arquitectura MVC + Estrategia + DIP",
        "src/neumonia: model/ (readers, preprocessing, classifier, gradcam, metadata), controller/ "
        "(service, decision, factory, gateways, report, errors), view/ (streamlit_app + presenter). "
        "Adaptadores api/ (FastAPI) y grpc_api/. Protocolos: ImageReader, Classifier, Explainer, "
        "DecisionPolicy, PredictionGateway, Tracker. Solo controller/factory.py instancia clases concretas. "
        "La vista nunca importa neumonia.model/TensorFlow/OpenCV; lo verifica tests/test_architecture.py. "
        "Ver docs/arquitectura/DESIGN.md y ADR-0001.",
    ),
    (
        "architecture",
        "architecture/contrato-api",
        "Contrato estable de POST /predict",
        "Claves mínimas del curso: label (NORMAL|PNEUMONIA), probability, gradcam_url. Aditivas: subtype, "
        "class_probabilities, metadata, model_version, request_id. 422 entrada inválida con detail[].msg; "
        "500 {error}. Fuente de verdad api/openapi.yaml. Cambios incompatibles solo en /v2.",
    ),
    (
        "decision",
        "decision/modelo-preentrenado",
        "Se reutiliza conv_MLP_84.h5 (no se reentrena)",
        "El curso evalúa contrato y despliegue, no la métrica. Release modelo-v1, SHA-256 "
        "d9548ff6fd2c29cdd15328ff95e1ad1fc8c7226e04e86c5890526bea2215e18e, 118 MB, 9.8M parámetros, "
        "entrada 512x512x1, softmax 3 clases (bacteriana, normal, viral). Descarga: make model. ADR-0002.",
    ),
    (
        "decision",
        "decision/politica-umbral",
        "Política 3 clases -> contrato binario",
        "P(neumonía)=P(bacteriana)+P(viral); PNEUMONIA si >= NEUMONIA_THRESHOLD (0.5). probability es la de "
        "la etiqueta devuelta. Grad-CAM sobre la clase de subtype. No usar argmax: (0.3,0.4,0.3) diría normal "
        "con 0.6 de neumonía. controller/decision.py, ADR-0003.",
    ),
    (
        "decision",
        "decision/dataset-rsna",
        "Dataset con metadatos: RSNA Pneumonia 2018",
        "26 684 DICOM con PatientAge, PatientSex, ViewPosition; etiquetas de radiólogos y cajas. Los DICOM del "
        "aula son RSNA. Kermany (CC BY 4.0) como complemento por subtipo. make dataset-rsna requiere "
        "kaggle.json y aceptar reglas. Submuestras estratificadas seed=42. docs/dataset.md, ADR-0004.",
    ),
    (
        "config",
        "config/preprocesamiento",
        "NO cambiar el preprocesamiento",
        "512x512 -> gris -> CLAHE(clip 2.0, rejilla 4x4) -> /255 -> (1,512,512,1). Es el del entrenamiento; "
        "cambiarlo produce training-serving skew. model/preprocessing.py.",
    ),
    (
        "decision",
        "decision/ui-gateway",
        "UI Streamlit con pasarela Local/HTTP",
        "La vista usa PredictionGateway: LocalGateway (mismo proceso) o HttpGateway si NEUMONIA_API_URL está "
        "definida (Docker Compose: ui -> api). PDF con fpdf2 desde datos, no capturas. ADR-0005.",
    ),
    (
        "decision",
        "decision/mlflow-sqlite",
        "MLflow con backend SQLite",
        "MLflow 3 dejó el file store en mantenimiento: MLFLOW_TRACKING_URI=sqlite:///mlflow.db. make evaluate, "
        "make mlflow. Se registran métricas globales y recall por sexo, age_group y view_position. ADR-0006.",
    ),
    (
        "pattern",
        "pattern/pruebas-aaa",
        "Pruebas pytest AAA con dobles",
        "309 pruebas, cobertura 98 %, compuerta 80 %. Dobles en tests/conftest.py: FakeClassifier, FakeExplainer, "
        "ExplodingClassifier, make_dicom_bytes, tiny_keras_model. Marcas model y slow; make test-fast las excluye.",
    ),
    (
        "config",
        "config/comandos",
        "Comandos del proyecto (uv, prohibido pip)",
        "make install | model | smoke | check | ui | api | grpc | evaluate | mlflow | grafo | memoria | "
        "diagramas | docker-build | docker-up | docker-smoke. Ruta local C:\\Neumonia. Python 3.13 vía uv.",
    ),
    (
        "decision",
        "decision/privacidad",
        "Privacidad: nunca exponer PHI",
        "model/metadata.py SAFE_FIELDS (lista blanca: edad, sexo, proyección, modalidad, región, fotometría, "
        "filas, columnas). PatientID/PatientName nunca salen del lector. Ley 1581/2012. Pruebas anti-fuga.",
    ),
    (
        "discovery",
        "discovery/gradcam-atajos",
        "Grad-CAM revela posible aprendizaje por atajos",
        "En viral (3).dcm (RSNA, AP, 6 años) el calor cae en el marcador de lateralidad y los bordes de la placa, "
        "no en los pulmones. Riesgo R-05. docs/img/gradcam_viral.png. Mitigación futura: recorte pulmonar.",
    ),
    (
        "discovery",
        "discovery/falso-positivo",
        "Falso positivo con alta confianza",
        "NORMAL2-IM-1147-0001.jpeg (normal) -> PNEUMONIA/viral p=0.983. Las probabilidades no están calibradas.",
    ),
    (
        "learning",
        "learning/metricas-aula",
        "Métricas del aula están infladas",
        "Aula (16): exactitud 0.94, recall 1.00, especificidad 0.83, AUC 0.98. Posible solapamiento con el "
        "entrenamiento (Kermany). La evaluación honesta es RSNA por subgrupos (pendiente run_id en Model Card).",
    ),
    (
        "config",
        "config/ci-cd",
        "CI/CD con compuertas",
        "GitHub Actions (M1): ruff -> pytest Ubuntu+Windows cov>=80 + smoke -> docker build + container_smoke. "
        "GitLab (M4): ruff -> pytest -> build/push -> Trivy -> deploy manual Droplet -> smoke producción. "
        "Variables DROPLET_HOST, DROPLET_USER, SSH_PRIVATE_KEY (File), SSH_KNOWN_HOSTS protegidas.",
    ),
    (
        "decision",
        "decision/metodologias",
        "Metodologías del proyecto",
        "CRISP-DM+MLOps, Data Thinking, DAMA-DMBOK, Kanban, BMC+OKR/KPI, riesgos ISO 31000 + EU AI Act, MVC, "
        "SOLID (Estrategia+DIP), Humble Object, contract-first, pirámide de pruebas AAA, uv+12-factor+Docker, "
        "Gitflow, CI/CD+DevSecOps, Grad-CAM, evaluación por subgrupos, MLflow, Model Card, privacidad, "
        "spec-driven con agentes. Trazabilidad: docs/arquitectura/METODOLOGIAS_ARQUITECTURA.md.",
    ),
    (
        "config",
        "config/entregables",
        "Entregables y fechas del curso",
        "M1 25 % (31/10), M2 35 % (31/10), M3 25 % sustentación 14/11/2026, M4 15 % sustentación 28/11/2026. "
        "Checklist en la skill entregables-curso.",
    ),
    (
        "config",
        "config/herramientas-agente",
        "Herramientas agénticas del proyecto",
        "Claude Code con CLAUDE.md, 10 skills (incl. graphify), 2 subagentes, hooks (ruff, guard_bash, graphify). "
        "graphify: grafo en graphify-out/ (make grafo). Engram: memoria del proyecto 'neumonia' en .engram/ "
        "(make memoria).",
    ),
    (
        "decision",
        "decision/hallazgos-3d",
        "Informe de hallazgos por zonas y vistas 3D (ADR-0007)",
        "Grad-CAM 31x31 resumido en 6 zonas geometricas (derecho = izquierda de la imagen), lateralidad por la "
        "zona mas intensa de cada lado, extension (atencion >= 0.5) y alerta de atajo si la densidad fuera/dentro "
        "de los pulmones >= 1.0 (tope 99). Vistas 3D Plotly: relieve de atencion y esquema no anatomico. "
        "No es segmentacion ni reconstruccion 3D (la radiografia es 2D). Campo aditivo findings en /predict.",
    ),
    (
        "decision",
        "decision/segmentacion-pulmonar",
        "Segmentacion pulmonar PSPNet opcional y aislada (ADR-0008)",
        "LungSegmenter: geometrica por defecto o PSPNet de TorchXRayVision (extra seg, make seg, "
        "NEUMONIA_LUNG_SEGMENTER=pspnet). Control de calidad (cada pulmon >= 4 %, ambos >= 12 %, lados "
        "correctos) con respaldo geometrico y nota. PSPNet en proceso hijo lung_worker: TensorFlow y "
        "torchvision/triton abortan juntos (LLVM). Nunca importar torch en el proceso principal ni con "
        "importorskip. Pesos SHA-256 019b167e. La consolidacion densa queda fuera de la mascara.",
    ),
    (
        "decision",
        "decision/localizacion-rsna",
        "Grad-CAM contra las cajas de RSNA (ADR-0009)",
        "make evaluate-loc: 300 casos con cajas (semilla 42). Metricas con linea base de azar: pointing "
        "game (region >= 99 % del maximo, IC de Wilson), enriquecimiento = energia en cajas / area "
        "(1.0 = azar) e IoU de la region >= 0.5. Reportar global y tp_ (clasificados neumonia). Cajas "
        "reescaladas a 512 sin recorte. Cifras pendientes en la Model Card hasta tener RSNA.",
    ),
    (
        "decision",
        "decision/prototipo-tomografia",
        "Prototipo de tomografia 3D con MEDPSeg (ADR-0010)",
        "Radiografia = 2D, no hay 3D real; con CT si. MEDPSeg (MIT, commit 1e6617dc, pesos SHA b0890cd4) "
        "en .medpseg/env, invocado como proceso externo con medpseg_runner.py (medpseg_cpu importa "
        "Tkinter). Remuestreo 1.5 mm; ~7 s/corte en 2 nucleos CPU. Lobulos: 1 LUL 2 LLL 3 RUL 4 RML 5 RLL. "
        "Severidad 0-5 por lobulo (0-25). Cache npz para demo instantanea: make ct-precompute + make ui-ct.",
    ),
]


def main() -> int:
    engram = os.environ.get("ENGRAM_BIN") or shutil.which("engram")
    if engram is None:
        print(
            "✗ No se encontró `engram` en el PATH. Instálelo: https://github.com/Gentleman-Programming/engram"
        )
        return 1
    if not (ROOT / ".engram" / "config.json").exists():
        subprocess.run([engram, "init", PROJECT], cwd=ROOT, check=True)
    for kind, topic, title, content in MEMORIAS:
        subprocess.run(
            [
                engram,
                "save",
                title,
                content,
                "--type",
                kind,
                "--project",
                PROJECT,
                "--topic",
                topic,
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        print(f"✓ [{kind}] {title}")
    subprocess.run([engram, "sync", "--project", PROJECT], cwd=ROOT, check=True)
    print(f"✓ {len(MEMORIAS)} memorias guardadas y exportadas a .engram/ (versionar con Git)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
