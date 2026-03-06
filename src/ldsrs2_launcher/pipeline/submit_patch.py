from __future__ import annotations

from pathlib import Path
from typing import Any

from ldsrs2_launcher.config.loader import runtime_config_to_dict
from ldsrs2_launcher.config.schema import RuntimeConfig
from ldsrs2_launcher.data.staging import stage_cutout
from ldsrs2_launcher.domain.manifests import new_run_id, write_yaml
from ldsrs2_launcher.domain.naming import patch_dir, resolve_run_dir
from ldsrs2_launcher.domain.patching import Patch
from ldsrs2_launcher.slurm.spec import SlurmJobSpec
from ldsrs2_launcher.slurm.submit import submit_job


def _patch_manifest(
    *,
    patch: Patch,
    run_id: str,
    run_dir: Path,
    input_tif: Path,
    start_date: str,
    end_date: str,
    config: RuntimeConfig,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "patch_id": patch.patch_id,
        "latitude": patch.latitude,
        "longitude": patch.longitude,
        "edge_size": patch.edge_size,
        "start_date": start_date,
        "end_date": end_date,
        "paths": {
            "run_dir": "../..",
            "input_tif": "inputs/lr.tif",
            "output_dir": "outputs",
            "metadata_dir": "metadata",
        },
        "config": runtime_config_to_dict(config),
    }


def submit_patch_run(
    *,
    config: RuntimeConfig,
    patch: Patch,
    start_date: str,
    end_date: str,
    script_path: Path,
    dry_run: bool = False,
) -> tuple[str, Path, dict[str, str]]:
    run_id = new_run_id(config.project_name)
    run_dir = resolve_run_dir(config.output_root, run_id)
    patch_root = patch_dir(run_dir, patch.patch_id)
    input_tif = patch_root / "inputs" / "lr.tif"

    run_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(run_dir / "resolved_config.yaml", runtime_config_to_dict(config))

    if not dry_run:
        stage_cutout(
            latitude=patch.latitude,
            longitude=patch.longitude,
            start_date=start_date,
            end_date=end_date,
            config=config.staging,
            output_path=input_tif,
        )
    else:
        input_tif.parent.mkdir(parents=True, exist_ok=True)

    manifest = _patch_manifest(
        patch=patch,
        run_id=run_id,
        run_dir=run_dir,
        input_tif=input_tif,
        start_date=start_date,
        end_date=end_date,
        config=config,
    )
    write_yaml(
        run_dir / "run_manifest.yaml",
        {
            "run_id": run_id,
            "mode": "patch",
            "patch_count": 1,
            "tasks": [{"patch_id": patch.patch_id, "manifest": f"patches/{patch.patch_id}/manifest.yaml"}],
        },
    )
    manifest_path = patch_root / "manifest.yaml"
    write_yaml(manifest_path, manifest)

    spec = SlurmJobSpec(
        job_name=f"ldsrs2_{patch.patch_id}",
        script_path=script_path,
        manifest_path=manifest_path,
        output_path=run_dir / "logs" / f"slurm_{patch.patch_id}.out",
        error_path=run_dir / "logs" / f"slurm_{patch.patch_id}.err",
        slurm=config.slurm,
        environment=config.environment,
    )
    submission = submit_job(spec, run_dir / "submission", dry_run=dry_run)
    return run_id, run_dir, submission
