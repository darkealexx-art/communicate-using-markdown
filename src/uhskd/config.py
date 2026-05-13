from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib

from uhskd.delta.processor import DeltaConfig


@dataclass(frozen=True)
class IngestionConfig:
    watch_path: Path | None = None
    download_dir: Path = Path("resources/downloads")
    extensions: tuple[str, ...] = (".mp3", ".wav", ".m4a", ".mp4", ".mkv")


@dataclass(frozen=True)
class TranscriptionConfig:
    model_size: str = "base"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 5
    vad_filter: bool = True


@dataclass(frozen=True)
class VaultConfig:
    persist_dir: Path = Path("resources/vault")
    collection_name: str = "uhskd"


@dataclass(frozen=True)
class OutputConfig:
    output_dir: Path = Path("outputs")
    template_path: Path | None = None


@dataclass(frozen=True)
class AppConfig:
    ingestion: IngestionConfig = IngestionConfig()
    transcription: TranscriptionConfig = TranscriptionConfig()
    vault: VaultConfig = VaultConfig()
    output: OutputConfig = OutputConfig()
    delta: DeltaConfig = DeltaConfig()


def _read_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def load_config(config_path: Path | None = None) -> AppConfig:
    data = _read_toml(config_path) if config_path else {}

    ingestion_data = data.get("ingestion", {})
    watch_path = ingestion_data.get("watch_path") or _env("UHSKD_WATCH_PATH")
    download_dir = ingestion_data.get("download_dir") or _env("UHSKD_DOWNLOAD_DIR")

    ingestion = IngestionConfig(
        watch_path=Path(watch_path) if watch_path else None,
        download_dir=Path(download_dir) if download_dir else IngestionConfig().download_dir,
        extensions=tuple(ingestion_data.get("extensions", IngestionConfig().extensions)),
    )

    transcription_data = data.get("transcription", {})
    transcription = TranscriptionConfig(
        model_size=transcription_data.get("model_size", TranscriptionConfig().model_size),
        device=transcription_data.get("device", TranscriptionConfig().device),
        compute_type=transcription_data.get("compute_type", TranscriptionConfig().compute_type),
        beam_size=int(transcription_data.get("beam_size", TranscriptionConfig().beam_size)),
        vad_filter=bool(transcription_data.get("vad_filter", TranscriptionConfig().vad_filter)),
    )

    vault_data = data.get("vault", {})
    vault = VaultConfig(
        persist_dir=Path(vault_data.get("persist_dir", VaultConfig().persist_dir)),
        collection_name=vault_data.get("collection_name", VaultConfig().collection_name),
    )

    output_data = data.get("output", {})
    template_path = output_data.get("template_path") or _env("UHSKD_TEMPLATE_PATH")
    output = OutputConfig(
        output_dir=Path(output_data.get("output_dir", OutputConfig().output_dir)),
        template_path=Path(template_path) if template_path else None,
    )

    delta_data = data.get("delta", {})
    delta = DeltaConfig(
        novelty_similarity_threshold=float(
            delta_data.get("novelty_similarity_threshold", DeltaConfig().novelty_similarity_threshold)
        ),
        reinforcement_similarity_threshold=float(
            delta_data.get(
                "reinforcement_similarity_threshold",
                DeltaConfig().reinforcement_similarity_threshold,
            )
        ),
        min_characters=int(delta_data.get("min_characters", DeltaConfig().min_characters)),
        min_confidence=float(delta_data.get("min_confidence", DeltaConfig().min_confidence)),
        top_k=int(delta_data.get("top_k", DeltaConfig().top_k)),
    )

    return AppConfig(
        ingestion=ingestion,
        transcription=transcription,
        vault=vault,
        output=output,
        delta=delta,
    )
