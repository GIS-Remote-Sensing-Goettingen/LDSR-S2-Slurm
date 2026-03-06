# LDSR-S2 Slurm Launcher

`ldsrs2-launcher` is a production-oriented Slurm launcher for the LDSR-S2 super-resolution workflow.
It is based on the model of https://github.com/ESAOpenSR/opensr-model (check it out!) 

The repository is organized around a Python package, immutable run manifests, and run-centric output directories. The launcher stages Sentinel-2 cutouts on the submission side and submits inference-only Slurm jobs for maintainable, reproducible cluster execution.

## Repository layout

- `src/ldsrs2_launcher/` - application package
- `configs/` - model and runtime configuration
- `scripts/slurm_task_entrypoint.sh` - thin Slurm task entrypoint
- `tests/` - unit and integration tests
- `docs/` - architecture and operations notes

## Installation

```bash
python -m pip install -e .
```

For direct module execution without installation, set `PYTHONPATH=src`.

## CLI

```bash
ldsrs2 validate-config --config configs/runtime/default.yaml
ldsrs2 submit patch --config configs/runtime/default.yaml --lat 51.5413 --lon 9.9158 --start-date 2025-08-18 --end-date 2025-08-19
ldsrs2 submit grid --config configs/runtime/default.yaml --lat1 51.4 --lon1 11.0 --lat2 54.0 --lon2 15.0 --start-date 2025-07-01 --end-date 2025-07-03
ldsrs2 collect --run-dir runs/<run_id>
ldsrs2 status --run-dir runs/<run_id>
```

## Execution model

- submission host stages low-resolution Sentinel-2 GeoTIFF inputs
- each submission writes a resolved run manifest and per-patch task manifests
- Slurm executes inference-only tasks from those manifests
- outputs, logs, metadata, and submission details live under one run directory

## Run layout

```text
runs/<run_id>/
  run_manifest.yaml
  resolved_config.yaml
  submission/
  logs/
  patches/
    patch_000001/
      manifest.yaml
      inputs/lr.tif
      outputs/
      metadata/
```

## Notes

- checkpoints are configured explicitly and are not expected in the repository root
- generated assets and legacy experiment outputs are intentionally excluded from source control
- cluster-specific settings live in runtime config, not in hardcoded shell scripts
- staging retries rate-limited API requests after `15`, `30`, `60`, `120`, `120`, and `120` seconds before failing
