# Benchmarks

`benchmark.py` times a set of workloads that run unchanged on both the 4.x line
and 5.0, so the two can be compared directly. It has no third-party
dependencies and does no `sys.path` manipulation - it measures whichever
`bitstring` is first on `sys.path`, and prints the resolved path in its header.

This is separate from `tests/test_benchmarks.py`, which uses pytest-benchmark
and can only ever measure one installed version.

## Comparing 4.x with 5.0

Use two environments, since the versions cannot coexist:

```bash
# 4.x, from PyPI
python -m venv /tmp/v4 && /tmp/v4/bin/pip install "bitstring<5"
cd /tmp && /tmp/v4/bin/python /path/to/benchmarks/benchmark.py --json old.json
```

```bash
# 5.0, from this checkout
uv run python benchmarks/benchmark.py --json new.json
```

```bash
python benchmarks/benchmark.py --compare old.json new.json
```

Run the 4.x copy from outside the repository, or the checkout shadows the
installed package and 5.0 gets measured twice. Use the same interpreter and an
otherwise idle machine for both halves.

## Options

- `--scale F` - multiply every workload size by `F`. Sizes are tuned so each
  workload takes roughly 0.03-0.6s per repeat on 5.0; drop to e.g. `0.1` when
  iterating. Checksums are only verified at `--scale 1.0`, and comparing runs
  at different scales is meaningless (the tool warns).
- `--repeat N` - repeats per workload, default 5. The comparison uses the best
  time, which is the most stable statistic here.
- `--only NAME` - run a single workload; repeatable. `--list` shows the names.
- `--verbose` - print checksums and every individual timing.

## Adding a workload

Write a function taking `scale` and returning a checksum, then add it to
`WORKLOADS` with its expected value at scale 1.0. The checksum assertion is what
stops a version that quietly does less work from looking faster. Use only API
present in both lines, or add a shim next to `zeros()`/`reader()` - those use
feature detection (`hasattr`) rather than version numbers.
