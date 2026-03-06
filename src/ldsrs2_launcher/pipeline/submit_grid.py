from __future__ import annotations

from pathlib import Path

from ldsrs2_launcher.config.loader import runtime_config_to_dict
from ldsrs2_launcher.config.schema import RuntimeConfig
from ldsrs2_launcher.data.staging import stage_cutout
from ldsrs2_launcher.domain.manifests import new_run_id, write_yaml
from ldsrs2_launcher.domain.naming import patch_dir, resolve_run_dir
from ldsrs2_launcher.domain.patching import Patch
from ldsrs2_launcher.slurm.spec import SlurmJobSpec
from ldsrs2_launcher.slurm.submit import submit_job


def submit_grid_run(
    *,
    config: RuntimeConfig,
    patches: list[Patch],
    start_date: str,
    end_date: str,
    script_path: Path,
    dry_run: bool = False,
) -> tuple[str, Path, dict[str, str]]:
    run_id = new_run_id(config.project_name)
    run_dir = resolve_run_dir(config.output_root, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(run_dir / "resolved_config.yaml", runtime_config_to_dict(config))

    manifests_dir = run_dir / "patches"
    tasks: list[dict[str, object]] = []
    for patch in patches:
        patch_root = patch_dir(run_dir, patch.patch_id)
        input_tif = patch_root / "inputs" / "lr.tif"
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

        manifest = {
            "run_id": run_id,
            "patch_id": patch.patch_id,
            "patch_index": len(tasks),
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
        write_yaml(patch_root / "manifest.yaml", manifest)
        tasks.append(manifest)

    run_manifest = {
        "run_id": run_id,
        "mode": "grid",
        "patch_count": len(tasks),
        "start_date": start_date,
        "end_date": end_date,
        "tasks": [
            {"patch_id": str(task["patch_id"]), "manifest": f"patches/{task['patch_id']}/manifest.yaml"}
            for task in tasks
        ],
    }
    write_yaml(run_dir / "run_manifest.yaml", run_manifest)

    spec = SlurmJobSpec(
        job_name=f"ldsrs2_{run_id}",
        script_path=script_path,
        manifest_path=run_dir / "run_manifest.yaml",
        output_path=run_dir / "logs" / "slurm_%A_%a.out",
        error_path=run_dir / "logs" / "slurm_%A_%a.err",
        slurm=config.slurm,
        environment=config.environment,
        array=f"0-{len(tasks) - 1}" if tasks else None,
    )
    submission = submit_job(spec, run_dir / "submission", dry_run=dry_run)
    return run_id, run_dir, submission
