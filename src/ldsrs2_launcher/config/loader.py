from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from ldsrs2_launcher.config.schema import (
    EnvironmentConfig,
    InferenceConfig,
    ModelConfig,
    RuntimeConfig,
    SlurmConfig,
    StagingConfig,
)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at {path}, got {type(data).__name__}")
    return data


def _merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _runtime_from_mapping(data: dict[str, Any]) -> RuntimeConfig:
    environment = EnvironmentConfig(**data.get("environment", {}))
    model = ModelConfig(**data.get("model", {}))
    staging = StagingConfig(**data.get("staging", {}))
    inference_data = dict(data.get("inference", {}))
    if "window_size" in inference_data:
        inference_data["window_size"] = tuple(inference_data["window_size"])
    inference = InferenceConfig(**inference_data)
    slurm = SlurmConfig(**data.get("slurm", {}))
    output_root = Path(data.get("output_root", "runs"))
    return RuntimeConfig(
        project_name=data.get("project_name", "ldsrs2"),
        output_root=output_root,
        environment=environment,
        model=model,
        staging=staging,
        inference=inference,
        slurm=slurm,
    )


def load_runtime_config(config_path: str | Path, overrides: dict[str, Any] | None = None) -> RuntimeConfig:
    path = Path(config_path).resolve()
    data = _read_yaml(path)
    if overrides:
        data = _merge(data, overrides)
    config = _runtime_from_mapping(data)
    base_dir = Path.cwd().resolve()
    if not config.output_root.is_absolute():
        config.output_root = (base_dir / config.output_root).resolve()
    model_config_path = Path(config.model.config_path)
    if not model_config_path.is_absolute():
        config.model.config_path = str((base_dir / model_config_path).resolve())
    if config.model.checkpoint_path is not None:
        checkpoint_path = Path(config.model.checkpoint_path).expanduser()
        if not checkpoint_path.is_absolute():
            config.model.checkpoint_path = str((base_dir / checkpoint_path).resolve())
    validate_runtime_config(config)
    return config


def validate_runtime_config(config: RuntimeConfig) -> None:
    if config.staging.edge_size <= 0:
        raise ValueError("staging.edge_size must be positive")
    if config.staging.resolution <= 0:
        raise ValueError("staging.resolution must be positive")
    if config.staging.overlap_meters < 0:
        raise ValueError("staging.overlap_meters must be non-negative")
    if any(delay <= 0 for delay in config.staging.rate_limit_retry_delays_seconds):
        raise ValueError("staging.rate_limit_retry_delays_seconds must contain positive integers")
    if config.inference.factor <= 0:
        raise ValueError("inference.factor must be positive")
    if len(config.inference.window_size) != 2 or min(config.inference.window_size) <= 0:
        raise ValueError("inference.window_size must contain two positive integers")
    if config.slurm.gpus < 0:
        raise ValueError("slurm.gpus must be non-negative")
    if config.slurm.mem_gb <= 0:
        raise ValueError("slurm.mem_gb must be positive")
    if config.slurm.cpus_per_task <= 0:
        raise ValueError("slurm.cpus_per_task must be positive")


def runtime_config_to_dict(config: RuntimeConfig) -> dict[str, Any]:
    data = asdict(config)
    cwd = Path.cwd().resolve()
    try:
        data["output_root"] = str(config.output_root.resolve().relative_to(cwd))
    except ValueError:
        data["output_root"] = str(config.output_root)
    model_config_path = Path(config.model.config_path).resolve()
    try:
        data["model"]["config_path"] = str(model_config_path.relative_to(cwd))
    except ValueError:
        data["model"]["config_path"] = str(model_config_path)
    data["inference"]["window_size"] = list(config.inference.window_size)
    return data
