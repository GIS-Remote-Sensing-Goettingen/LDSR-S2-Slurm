from __future__ import annotations

import subprocess
from pathlib import Path

from ldsrs2_launcher.domain.manifests import write_json
from ldsrs2_launcher.slurm.spec import SlurmJobSpec, build_sbatch_command


def parse_job_id(stdout: str) -> str:
    parts = stdout.strip().split()
    if not parts:
        raise ValueError("Could not parse sbatch output")
    return parts[-1]


def submit_job(spec: SlurmJobSpec, submission_dir: Path, dry_run: bool = False) -> dict[str, str]:
    cmd = build_sbatch_command(spec)
    submission_dir.mkdir(parents=True, exist_ok=True)
    (submission_dir / "sbatch_command.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")

    if dry_run:
        payload = {"mode": "dry-run", "command": " ".join(cmd)}
        write_json(submission_dir / "slurm_job_ids.json", payload)
        return payload

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    job_id = parse_job_id(result.stdout)
    payload = {"job_id": job_id, "stdout": result.stdout.strip()}
    write_json(submission_dir / "slurm_job_ids.json", payload)
    return payload
