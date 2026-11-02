#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m tools.gen_sample examples/sample_evidence.json
python3 -m evrev examples/sample_evidence.json --as-of 2026-10-23 --out-dir examples
python3 -m unittest discover -s tests
