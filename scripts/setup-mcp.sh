#!/usr/bin/env bash
# Set up the KiCad MCP server (mixelpixx/KiCAD-MCP-Server, git submodule) for this repo.
# - Python env on KiCad's bundled Python (needed for the pcbnew SWIG API)
# - Node build of the MCP server
# Safe to re-run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRV="$ROOT/tools/kicad-mcp-server"
KICAD_PY="${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}"

command -v node >/dev/null || { echo "node (18+) not found" >&2; exit 1; }
[[ -x "$KICAD_PY" ]] || { echo "KiCad Python not found at $KICAD_PY (set KICAD_PY)" >&2; exit 1; }

git -C "$ROOT" submodule update --init tools/kicad-mcp-server

"$KICAD_PY" -c "import pcbnew; print('pcbnew', pcbnew.GetBuildVersion())"

if [[ ! -x "$SRV/venv/bin/python3" ]]; then
  "$KICAD_PY" -m venv --system-site-packages "$SRV/venv"
fi
"$SRV/venv/bin/python3" -m pip install -q --upgrade pip
"$SRV/venv/bin/python3" -m pip install -q -r "$SRV/requirements.txt"

(cd "$SRV" && npm ci --no-audit --no-fund)

echo "KiCad MCP server ready: $SRV/dist/index.js"
