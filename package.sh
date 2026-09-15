#!/usr/bin/env bash
# Builds the proxy DLL and packs the release archive. usage: ./package.sh <version>
set -euo pipefail
cd "$(dirname "$0")"
VERSION="${1:-dev}"
OUT="dist"
STAGE="$OUT/JC4-FovAlways-$VERSION"

./build.sh
rm -rf "$OUT"
mkdir -p "$STAGE"
cp oo2core_7_win64.dll "$STAGE/"
cp installer/install.bat installer/uninstall.bat installer/jc4fov.sh "$STAGE/"
echo 100 > "$STAGE/jc4_fov.txt"
sed "s/@VERSION@/$VERSION/g" installer/README.txt > "$STAGE/README.txt"
(cd "$STAGE" && zip -q -r "../JC4-FovAlways-$VERSION.zip" .)
echo "$OUT/JC4-FovAlways-$VERSION.zip"
