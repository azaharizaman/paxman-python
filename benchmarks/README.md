# Benchmarks (Item 7, W5)

One scenario per capability, deterministic per (input, contract, library snapshot).

Run:
  uv run python -m benchmarks.harness --iterations 200
  uv run python -m benchmarks.harness --output bench.json
  uv run python -m benchmarks.harness --update-baseline  # refresh committed baseline.json

CI runs 50 iterations informational (non-blocking). Baseline is tracked but not gated.
Add a new capability: add one entry to `benchmarks/scenarios.py` with `register` + `contract_factory`.
