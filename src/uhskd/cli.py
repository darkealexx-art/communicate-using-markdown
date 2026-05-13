from __future__ import annotations

import argparse
from pathlib import Path

from uhskd.config import AppConfig, load_config
from uhskd.delta.processor import DeltaLogicProcessor
from uhskd.ingestion.file_watcher import FileIngestionSource, FolderWatcher
from uhskd.ingestion.youtube import YouTubeIngestionSource
from uhskd.knowledge_vault.chroma import ChromaKnowledgeVault
from uhskd.logging_utils import setup_logging
from uhskd.orchestration.pipeline import Pipeline
from uhskd.output.markdown import MarkdownOutputGenerator
from uhskd.transcription.faster_whisper import FasterWhisperTranscriber


def build_pipeline(config: AppConfig) -> Pipeline:
    transcriber = FasterWhisperTranscriber(
        model_size=config.transcription.model_size,
        device=config.transcription.device,
        compute_type=config.transcription.compute_type,
        beam_size=config.transcription.beam_size,
        vad_filter=config.transcription.vad_filter,
    )
    vault = ChromaKnowledgeVault(
        persist_dir=config.vault.persist_dir,
        collection_name=config.vault.collection_name,
    )
    delta = DeltaLogicProcessor(vault, config.delta)
    output = MarkdownOutputGenerator(
        output_dir=config.output.output_dir,
        template_path=config.output.template_path,
    )
    return Pipeline(transcriber=transcriber, delta_processor=delta, output_generator=output)


def _run_file(args: argparse.Namespace, config: AppConfig) -> None:
    pipeline = build_pipeline(config)
    source = FileIngestionSource([Path(args.path)])
    for result in pipeline.run_source(source):
        print(f"Processed {result.item.local_path} -> {result.output_path}")


def _run_watch(args: argparse.Namespace, config: AppConfig) -> None:
    pipeline = build_pipeline(config)
    source = FolderWatcher(Path(args.path), extensions=config.ingestion.extensions)
    for result in pipeline.run_source(source):
        print(f"Processed {result.item.local_path} -> {result.output_path}")


def _run_youtube(args: argparse.Namespace, config: AppConfig) -> None:
    pipeline = build_pipeline(config)
    source = YouTubeIngestionSource(urls=args.url, download_dir=config.ingestion.download_dir)
    for result in pipeline.run_source(source):
        print(f"Processed {result.item.source_uri} -> {result.output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="UHSKD CLI")
    parser.add_argument("--config", type=Path, help="Ruta a config.toml")
    parser.add_argument("--log-level", default="INFO")

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_file = subparsers.add_parser("run-file", help="Procesar un archivo local")
    run_file.add_argument("path")

    watch = subparsers.add_parser("watch", help="Observar una carpeta")
    watch.add_argument("path")

    youtube = subparsers.add_parser("youtube", help="Procesar URLs de YouTube")
    youtube.add_argument("--url", action="append", required=True)

    args = parser.parse_args()
    setup_logging(args.log_level)

    config = load_config(args.config)

    if args.command == "run-file":
        _run_file(args, config)
    elif args.command == "watch":
        _run_watch(args, config)
    elif args.command == "youtube":
        _run_youtube(args, config)


if __name__ == "__main__":
    main()
