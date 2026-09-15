#!/usr/bin/env bash
# Builds the proxy DLL. Needs mingw-w64.
set -euo pipefail
cd "$(dirname "$0")"
x86_64-w64-mingw32-gcc -O2 -shared -o oo2core_7_win64.dll src/fovhook.c src/oo2core_7_win64.def
echo "built oo2core_7_win64.dll"
