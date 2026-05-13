# Arquitectura del proyecto

## Componentes principales

- **config**: carga y valida los parámetros de `config.yaml`.
- **sources**: ingesta desde RSS, JSON o CSV con manejo de errores.
- **processing**: deduplicación, scoring de relevancia e impacto.
- **analysis**: síntesis ejecutiva y detección de tendencias.
- **report**: generación del documento Word con citas de fuentes.
- **cli**: orquestación de la ejecución y logging.

## Flujo de datos

1. Se carga el archivo de configuración.
2. Se consulta cada fuente habilitada y se normalizan las noticias.
3. Se calcula relevancia, impacto y se deduplican entradas similares.
4. Se generan resúmenes ejecutivos por segmento.
5. Se construye el reporte Word final.

## Manejo de errores

Las fallas de una fuente se registran en logs y no detienen el resto del proceso.
