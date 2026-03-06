from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldsrs2_launcher.config.schema import EnvironmentConfig, SlurmConfig


@dataclass(slots=True)
class SlurmJobSpec:
    job_name: str
    script_path: Path
    manifest_path: Path
    output_path: Path
    error_path: Path
    slurm: SlurmConfig
    environment: EnvironmentConfig
    array: str | None = None


def build_sbatch_command(spec: SlurmJobSpec) -> list[str]:
    exports = ["ALL", f"LDSRS2_PYTHON={spec.environment.python_executable}"]
    if spec.environment.modules:
        exports.append(f"LDSRS2_MODULES={','.join(spec.environment.modules)}")
    if spec.environment.conda_env:
        exports.append(f"LDSRS2_CONDA_ENV={spec.environment.conda_env}")

    cmd = [
        "sbatch",
        f"--job-name={spec.job_name}",
        f"--output={spec.output_path}",
        f"--error={spec.error_path}",
        f"--export={','.join(exports)}",
        f"--cpus-per-task={spec.slurm.cpus_per_task}",
        f"--mem={spec.slurm.mem_gb}G",
        f"--time={spec.slurm.time}",
    ]
    if spec.slurm.partition:
        cmd.append(f"--partition={spec.slurm.partition}")
    if spec.slurm.gpus:
        if spec.slurm.gpu_type:
            cmd.append(f"--gpus={spec.slurm.gpu_type}:{spec.slurm.gpus}")
        else:
            cmd.append(f"--gpus={spec.slurm.gpus}")
    if spec.slurm.account:
        cmd.append(f"--account={spec.slurm.account}")
    if spec.slurm.qos:
        cmd.append(f"--qos={spec.slurm.qos}")
    if spec.array:
        cmd.append(f"--array={spec.array}")
    cmd.extend(spec.slurm.extra_args)
    cmd.append(str(spec.script_path))
    cmd.append(str(spec.manifest_path))
    return cmd
