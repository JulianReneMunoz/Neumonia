# Modelo — conv_MLP_84.h5

| Campo | Valor |
|---|---|
| Estado | ✅ descarga automática y verificada |
| Archivo | `artifacts/model/conv_MLP_84.h5` (118 MB, **ignorado por Git**) |
| Fuente | Release público `modelo-v1`: <https://github.com/jorgeenrgutierrez-gif/uao-neumonia/releases/tag/modelo-v1> |
| SHA-256 | `d9548ff6fd2c29cdd15328ff95e1ad1fc8c7226e04e86c5890526bea2215e18e` |
| Arquitectura | CNN con conexiones *skip* (Pasa et al., 2019), 9,8 M de parámetros, 512×512×1 → 3 clases |
| Licencia | Uso académico (caso base del curso) |

```powershell
make model                                   # o: uv run python scripts/fetch_model.py
$env:NEUMONIA_MODEL_PATH = "D:\otro\modelo.h5"   # para usar otra ruta
```
Sin internet: copie el `.h5` del aula a esta carpeta; `make model` verificará el hash y no lo volverá a descargar.
Ficha completa: [`docs/model_card.md`](../../docs/model_card.md).
