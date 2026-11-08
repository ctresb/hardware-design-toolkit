#!/bin/sh
# Builds the fictional test assembly and draws it. usage: scripts/selftest.sh [out_dir] [blender_binary]
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-./td-selftest}"
BL="${2:-${BLENDER:-blender}}"
mkdir -p "$OUT"
"$BL" -b --python-exit-code 1 --python "$HERE/make_test_scene.py" -- "$OUT/test_assembly.blend" | grep "TEST SCENE"
"$BL" -b "$OUT/test_assembly.blend" --python-exit-code 1 --python "$HERE/blueprint.py" -- \
  "$HERE/../templates/blueprint.example.json" "$OUT/puck" | grep "BLUEPRINT"
"$BL" -b "$OUT/test_assembly.blend" --python-exit-code 1 --python "$HERE/ortho_views.py" -- \
  "$HERE/../templates/blueprint.example.json" "$OUT/puck" | grep "ORTHO"
echo "SELFTEST ok -> $OUT"
