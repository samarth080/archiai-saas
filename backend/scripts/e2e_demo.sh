#!/usr/bin/env bash
# Unix wrapper for the cross-platform Phase 4 live smoke runner.
set -euo pipefail
python "$(dirname "$0")/e2e_demo.py"
