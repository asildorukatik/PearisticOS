#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "AppleOS: http://127.0.0.1:4173/"
python3 -m http.server 4173 --bind 127.0.0.1
