# news_analyst

Sistema automatizado para recopilar, validar, deduplicar, clasificar y analizar noticias recientes en cuatro segmentos: México, internacionales, tecnología y ciencia. El resultado es un informe ejecutivo en formato Word (.docx) con un tono formal y orientado a la toma de decisiones.

## Arquitectura (análisis breve)

El sistema se divide en cuatro capas principales: configuración, ingesta, procesamiento/analítica y reporte. La configuración centraliza las fuentes y parámetros en `config.yaml`. La ingesta obtiene noticias desde RSS/JSON/CSV con reintentos y timeouts, transformándolas en un modelo uniforme. El procesamiento aplica validación, deduplicación y scoring de relevancia/impacto. Finalmente, el módulo de reporte sintetiza hallazgos y genera el documento Word con citas de fuentes.

## Funcionalidades clave

- Obtención de noticias desde RSS, JSON o CSV.
- Validación de campos mínimos (título y URL).
- Deduplicación por similitud textual.
- Puntuación de relevancia (1–5) y nivel de impacto.
- Síntesis ejecutiva y análisis por segmento.
- Identificación de tendencias, riesgos y oportunidades.
- Registro de errores y continuidad ante fallas de fuentes.
- Exportación a Word (.docx) con citas explícitas.

## Requisitos

- Python 3.9+
- Dependencias en `requirements.txt`

## Instalación

```bash
python -m pip install -r requirements.txt
```

Para pruebas:

```bash
python -m pip install -r requirements-dev.txt
```

## Configuración

Edite `config.yaml` para ajustar fuentes, filtros y salida del reporte.

Parámetros principales:

- `report`: título, idioma, periodo, rango de fechas, salida.
- `filters`: puntaje mínimo y umbral de deduplicación.
- `logging`: nivel y ruta de log.
- `segments`: fuentes por segmento y sus tipos.

## Uso

```bash
python -m news_analyst --config config.yaml
```

El reporte se generará en la ruta indicada por `report.output_path`.

## Documentación adicional

- [Arquitectura del proyecto](docs/architecture.md)

## Pruebas

```bash
pytest
```

## Notas de cumplimiento

- Se evita el scraping agresivo.
- No se evaden paywalls ni se replican artículos completos.
- Se respetan timeouts y reintentos controlados.
- El sistema continúa con las demás fuentes si una falla.
