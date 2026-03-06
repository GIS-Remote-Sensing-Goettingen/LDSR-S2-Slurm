from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ldsrs2_launcher.config.loader import load_runtime_config, validate_runtime_config
from ldsrs2_launcher.domain.patching import Patch, build_patches
from ldsrs2_launcher.observability.logging import configure_logging
from ldsrs2_launcher.pipeline.collect import collect_outputs
from ldsrs2_launcher.pipeline.run_task import run_task
from ldsrs2_launcher.pipeline.submit_grid import submit_grid_run
from ldsrs2_launcher.pipeline.submit_patch import submit_patch_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ldsrs2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-config")
    validate_parser.add_argument("--config", required=True)

    submit_parser = subparsers.add_parser("submit")
    submit_subparsers = submit_parser.add_subparsers(dest="submit_command", required=True)

    patch_parser = submit_subparsers.add_parser("patch")
    _add_submit_common_args(patch_parser)
    patch_parser.add_argument("--lat", type=float, required=True)
    patch_parser.add_argument("--lon", type=float, required=True)

    grid_parser = submit_subparsers.add_parser("grid")
    _add_submit_common_args(grid_parser)
    grid_parser.add_argument("--lat1", type=float, required=True)
    grid_parser.add_argument("--lon1", type=float, required=True)
    grid_parser.add_argument("--lat2", type=float, required=True)
    grid_parser.add_argument("--lon2", type=float, required=True)

    run_parser = subparsers.add_parser("run")
    run_subparsers = run_parser.add_subparsers(dest="run_command", required=True)
    task_parser = run_subparsers.add_parser("task")
    task_parser.add_argument("--manifest", required=True)
    task_parser.add_argument("--task-index", type=int)

    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--run-dir", required=True)
    collect_parser.add_argument("--dest")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--run-dir", required=True)

    return parser


def _add_submit_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--script-path", default="scripts/slurm_task_entrypoint.sh")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")


def _patch_from_args(args: argparse.Namespace, edge_size: int) -> Patch:
    return Patch(
        patch_id="patch_000001",
        latitude=args.lat,
        longitude=args.lon,
        edge_size=edge_size,
        row_index=0,
        row_count=1,
        column_index=0,
        column_count=1,
    )


def _handle_validate(args: argparse.Namespace) -> int:
    config = load_runtime_config(args.config)
    validate_runtime_config(config)
    print(f"Configuration valid: {Path(args.config).resolve()}")
    return 0


def _handle_submit_patch(args: argparse.Namespace) -> int:
    logger = configure_logging(verbose=args.verbose)
    config = load_runtime_config(args.config)
    patch = _patch_from_args(args, config.staging.edge_size)
    run_id, run_dir, submission = submit_patch_run(
        config=config,
        patch=patch,
        start_date=args.start_date,
        end_date=args.end_date,
        script_path=Path(args.script_path).resolve(),
        dry_run=args.dry_run,
    )
    logger.info("submitted patch run_id=%s run_dir=%s", run_id, run_dir)
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "submission": submission}, indent=2))
    return 0


def _handle_submit_grid(args: argparse.Namespace) -> int:
    logger = configure_logging(verbose=args.verbose)
    config = load_runtime_config(args.config)
    patches = build_patches(
        args.lat1,
        args.lon1,
        args.lat2,
        args.lon2,
        config.staging.edge_size,
        float(config.staging.resolution),
        config.staging.overlap_meters,
    )
    run_id, run_dir, submission = submit_grid_run(
        config=config,
        patches=patches,
        start_date=args.start_date,
        end_date=args.end_date,
        script_path=Path(args.script_path).resolve(),
        dry_run=args.dry_run,
    )
    logger.info("submitted grid run_id=%s run_dir=%s patches=%d", run_id, run_dir, len(patches))
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "patches": len(patches), "submission": submission}, indent=2))
    return 0


def _handle_run_task(args: argparse.Namespace) -> int:
    task_index = args.task_index
    if task_index is None and os.environ.get("SLURM_ARRAY_TASK_ID"):
        task_index = int(os.environ["SLURM_ARRAY_TASK_ID"])
    output = run_task(Path(args.manifest).resolve(), task_index=task_index)
    print(output)
    return 0


def _handle_collect(args: argparse.Namespace) -> int:
    destination, copied = collect_outputs(Path(args.run_dir).resolve(), Path(args.dest).resolve() if args.dest else None)
    print(json.dumps({"destination": str(destination), "copied": copied}, indent=2))
    return 0


def _handle_status(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    payload = {
        "run_dir": str(run_dir),
        "resolved_config": str(run_dir / "resolved_config.yaml"),
        "run_manifest": str(run_dir / "run_manifest.yaml"),
        "logs_dir": str(run_dir / "logs"),
        "patch_count": len(list((run_dir / "patches").glob("patch_*"))) if (run_dir / "patches").exists() else 0,
    }
    print(json.dumps(payload, indent=2))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "validate-config":
        return _handle_validate(args)
    if args.command == "submit" and args.submit_command == "patch":
        return _handle_submit_patch(args)
    if args.command == "submit" and args.submit_command == "grid":
        return _handle_submit_grid(args)
    if args.command == "run" and args.run_command == "task":
        return _handle_run_task(args)
    if args.command == "collect":
        return _handle_collect(args)
    if args.command == "status":
        return _handle_status(args)
    parser.error("Unhandled command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
