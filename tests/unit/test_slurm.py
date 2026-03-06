from pathlib import Path

from ldsrs2_launcher.config.schema import EnvironmentConfig, SlurmConfig
from ldsrs2_launcher.slurm.spec import SlurmJobSpec, build_sbatch_command


def test_build_sbatch_command() -> None:
    spec = SlurmJobSpec(
        job_name="ldsrs2_patch_000001",
        script_path=Path("scripts/slurm_task_entrypoint.sh"),
        manifest_path=Path("runs/test/patches/patch_000001/manifest.yaml"),
        output_path=Path("runs/test/logs/slurm.out"),
        error_path=Path("runs/test/logs/slurm.err"),
        slurm=SlurmConfig(),
        environment=EnvironmentConfig(),
    )
    command = build_sbatch_command(spec)
    assert command[0] == "sbatch"
    assert not any(item.startswith("--partition=") for item in command)
    assert any(item.startswith("--export=") for item in command)
    assert str(spec.script_path) in command
