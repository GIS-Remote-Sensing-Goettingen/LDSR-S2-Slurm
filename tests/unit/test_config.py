from pathlib import Path

from ldsrs2_launcher.config.loader import load_runtime_config


def test_load_runtime_config() -> None:
    config = load_runtime_config(Path("configs/runtime/default.yaml"))
    assert config.project_name == "ldsrs2"
    assert config.staging.edge_size == 4096
    assert config.inference.window_size == (128, 128)
    assert config.staging.rate_limit_retry_delays_seconds == [15, 30, 60, 120, 120, 120]
    assert config.slurm.partition is None
