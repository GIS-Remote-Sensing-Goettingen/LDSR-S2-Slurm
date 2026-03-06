from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_RATE_LIMIT_RETRY_DELAYS_SECONDS = [15, 30, 60, 120, 120, 120]


@dataclass(slots=True)
class EnvironmentConfig:
    python_executable: str = "python"
    modules: list[str] = field(default_factory=list)
    conda_env: str | None = None


@dataclass(slots=True)
class ModelConfig:
    config_path: str = "configs/model/opensr_ldsrs2_v1.yaml"
    checkpoint_path: str | None = None


@dataclass(slots=True)
class StagingConfig:
    collection: str = "sentinel-2-l2a"
    bands: list[str] = field(default_factory=lambda: ["B04", "B03", "B02", "B08"])
    image_index: int = 0
    edge_size: int = 4096
    resolution: int = 10
    nodata: int = 0
    output_dtype: str = "uint16"
    compression: str = "deflate"
    overlap_meters: float = 128.0
    retry_on_rate_limit: bool = True
    rate_limit_retry_delays_seconds: list[int] = field(
        default_factory=lambda: list(DEFAULT_RATE_LIMIT_RETRY_DELAYS_SECONDS)
    )


@dataclass(slots=True)
class InferenceConfig:
    factor: int = 4
    window_size: tuple[int, int] = (128, 128)
    overlap: int = 12
    eliminate_border_px: int = 2
    gpus: int = 0
    save_preview: bool = False


@dataclass(slots=True)
class SlurmConfig:
    partition: str | None = None
    gpu_type: str | None = None
    gpus: int = 1
    cpus_per_task: int = 8
    mem_gb: int = 128
    time: str = "01:00:00"
    account: str | None = None
    qos: str | None = None
    extra_args: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RuntimeConfig:
    project_name: str = "ldsrs2"
    output_root: Path = Path("runs")
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    staging: StagingConfig = field(default_factory=StagingConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    slurm: SlurmConfig = field(default_factory=SlurmConfig)
