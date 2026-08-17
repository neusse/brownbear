# Updating brownbear data

Maintainers refresh market data, universe galaxies, fundamentals, and portfolio
notebooks using the steps below. For a restartable batch run, use
[tools/update-universe.sh](tools/update-universe.sh) — it executes steps 1–4 and
records progress in `tools/.update-universe.state` (gitignored).

## Prerequisites

From the repo root, with the project virtual environment activated:

```bash
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e .
```

`update-universe.sh` requires `jupyter` (see [requirements.txt](requirements.txt)).

## Automated run

```bash
./tools/update-universe.sh --full      # first run: clean caches, run all steps
./tools/update-universe.sh             # resume after an error
```

| Flag | Effect |
|------|--------|
| `--full` | `--delete-symbol-cache`, `--reset-fundamentals-cache`, and `--reset-progress` |
| `--delete-symbol-cache` | Step 0: delete `symbol-cache/`, reset fundamentals cache, and clear progress |
| `--reset-fundamentals-cache` | Delete `fundamentals_cache.json` before step 3 |
| `--reset-progress` | Ignore the checkpoint file and re-run all steps |

Completed notebooks are skipped on re-run. Notebooks use `refresh_timeseries=False`
by default; missing symbols in `symbol-cache/` are still downloaded automatically.

See [tools/README.md](tools/README.md) for Schwab scripts and the monthly strategy
workflow.

## Manual steps

Run these in order when you are not using `update-universe.sh`, or when you need
to run a single step by hand.

### Step 0 — Reset symbol cache (optional)

Delete `symbol-cache/` and its contents for a full rebuild from Yahoo Finance.
This also resets `tools/symbol-cache/fundamentals_cache.json` and
`fundamentals.csv`.

```bash
rm -rf symbol-cache/
```

Or use `./tools/update-universe.sh --delete-symbol-cache`.

### Step 1 — Asset class galaxy

Run [universe/asset-class-galaxy/asset-classes.ipynb](universe/asset-class-galaxy/asset-classes.ipynb).

- Builds `asset-classes.csv` (correlations) and `investment-options.csv`
- Set `refresh_timeseries = True` to force fresh downloads; `False` reuses the cache
  (missing symbols are still fetched)

### Step 2 — Universe galaxies

For each remaining folder under [universe/](universe/), run constituent index
notebooks (if present), then `investment-options.ipynb`.

| Galaxy | Index notebook | Investment options |
|--------|----------------|----------------------|
| `alabama-galaxy` | — | `investment-options.ipynb` |
| `dow30-galaxy` | `dow30.ipynb` | `investment-options.ipynb` |
| `etf-galaxy` | — | `investment-options.ipynb` |
| `extra-auto-galaxy` | — | `investment-options.ipynb` |
| `extra-manual-galaxy` | — | `investment-options.ipynb` |
| `nasdaq100-galaxy` | `nasdaq100.ipynb` | `investment-options.ipynb` |
| `sp400-galaxy` | `sp400.ipynb` | `investment-options.ipynb` |
| `sp500-galaxy` | `sp500.ipynb` | `investment-options.ipynb` |
| `sp600-galaxy` | `sp600.ipynb` | `investment-options.ipynb` |

**`extra-manual-galaxy`** — edit `investment-options.csv` by hand before running
`investment-options.ipynb` (metrics are not filled in automatically).

See [universe/README.md](universe/README.md) for `investment-options-in.csv` and
rebuild details.

### Step 3 — Symbol fundamentals

Run [tools/symbol-cache/get-symbol-fundamentals.ipynb](tools/symbol-cache/get-symbol-fundamentals.ipynb),
or let `update-universe.sh` call `bb.get_symbol_fundamentals()` directly.

Writes:

| File | Purpose |
|------|---------|
| `tools/symbol-cache/fundamentals.csv` | Used by `bb.add_fundamental_columns()` |
| `tools/symbol-cache/fundamentals_cache.json` | Incremental cache for fundamentals |

Reset the fundamentals cache with `bb.reset_fundamentals_cache()` or
`./tools/update-universe.sh --reset-fundamentals-cache`. Deleting `symbol-cache/`
(`--full` or `--delete-symbol-cache`) also resets fundamentals.

See [tools/symbol-cache/README.md](tools/symbol-cache/README.md).

### Step 4 — Portfolios

For each folder under [portfolios/](portfolios/), run `investment-options.ipynb`
(if present), then `portfolio.ipynb`.

| Portfolio | Investment options notebook |
|-----------|----------------------------|
| `florida-retirement-system` | `investment-options.ipynb` (manual CSV — see [portfolios/README.md](portfolios/README.md)) |
| All other portfolios | — (metrics come from universe galaxies) |

## Between notebook runs

If Jupyter kernels hang or pile up during a long batch:

```bash
./tools/cleanup-kernels.sh
```

`update-universe.sh` runs this automatically after each notebook.

## Related

- [symbol-cache/](symbol-cache/) — cached Yahoo daily timeseries (working data)
- [tools/symbol-cache/](tools/symbol-cache/) — cache maintenance notebooks
- [portfolios/README.md](portfolios/README.md) — portfolio notebook workflow
