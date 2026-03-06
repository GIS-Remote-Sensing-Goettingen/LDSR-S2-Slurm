# Architecture

The launcher is built around a manifest-driven two-step workflow.

1. The submission side computes patch geometry and stages low-resolution Sentinel-2 cutouts.
2. The launcher writes immutable run and task manifests into a run directory.
3. Slurm executes inference-only tasks using those manifests.
4. Outputs, logs, and metadata remain grouped by run and by patch.

## Design goals

- keep all real logic in Python modules under `src/`
- keep shell thin and cluster-specific
- avoid writing generated assets into the repository
- keep every task reproducible from a manifest snapshot
- isolate Slurm-specific logic from data staging and model execution

## Main modules

- `config` - typed configuration loading and validation
- `domain` - patch planning, path naming, raster metadata, manifests
- `data` - cutout staging from `cubo`
- `model` - checkpoint resolution and LDSR-S2 inference adapter
- `slurm` - `sbatch` command generation and job submission
- `pipeline` - user-facing workflows
- `observability` - logs and metadata files
