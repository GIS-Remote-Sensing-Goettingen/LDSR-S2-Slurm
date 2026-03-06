# Operations

## Validate configuration

```bash
ldsrs2 validate-config --config configs/runtime/default.yaml
```

## Submit one patch

```bash
ldsrs2 submit patch \
  --config configs/runtime/default.yaml \
  --lat 51.5413 \
  --lon 9.9158 \
  --start-date 2025-08-18 \
  --end-date 2025-08-19
```

## Submit a grid

```bash
ldsrs2 submit grid \
  --config configs/runtime/default.yaml \
  --lat1 51.4 --lon1 11.0 \
  --lat2 54.0 --lon2 15.0 \
  --start-date 2025-07-01 \
  --end-date 2025-07-03
```

## Dry runs

Add `--dry-run` to `submit patch` or `submit grid` to validate config, compute paths, and render Slurm plans without staging or submitting jobs.

## Status

```bash
ldsrs2 status --run-dir runs/<run_id>
```

## Collect outputs

```bash
ldsrs2 collect --run-dir runs/<run_id>
```
