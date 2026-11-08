#!/usr/bin/env bash
# Install the Hardware Design Toolkit toolchain on macOS with Homebrew.
# Idempotent: every step checks first and skips what is already installed.
#
# usage: install_macos.sh [--dry-run] [--with-optional] [--with-cloud] [--with-assets] [--skip-blender-modules]
#   --dry-run               print every command, change nothing
#   --with-optional         also ffmpeg, ImageMagick, libheif, KiKit (panels) and FreeCAD (STEP viewer)
#   --with-cloud            also AWS CLI and the Session Manager plugin (cloud GPU rendering)
#   --with-assets           download the render wear textures (ambientCG) and a studio HDRI (Poly Haven)
#   --skip-blender-modules  do not pip-install scipy into Blender's Python
set -euo pipefail

# Freerouting 1.9.0 (Java 17+) routes dense small boards further than 2.5.0, which needs Java 25 and stops after
# ~19 passes. For 2.5.0: FREEROUTING_VERSION=2.5.0 FREEROUTING_SHA256=f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7
FREEROUTING_VERSION="${FREEROUTING_VERSION:-1.9.0}"
# sha256 of freerouting-1.9.0.jar from the GitHub release assets; change both together
FREEROUTING_SHA256="${FREEROUTING_SHA256:-9084a4888937a7f31f857ecc12aa7a37407f51160e4d2892dff9c9bb47ae3102}"
FREEROUTING_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/freerouting"
TOOLKIT_DATA="${XDG_DATA_HOME:-$HOME/.local/share}/hardware-design-toolkit"
CAD_VENV="$TOOLKIT_DATA/venv"          # build123d needs Python 3.10–3.13
ASSETS_DIR="$TOOLKIT_DATA/assets"

DRY=0; OPTIONAL=0; CLOUD=0; ASSETS=0; BLENDER_MODULES=1
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --with-optional) OPTIONAL=1 ;;
    --with-cloud) CLOUD=1 ;;
    --with-assets) ASSETS=1 ;;
    --skip-blender-modules) BLENDER_MODULES=0 ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

say()  { printf '\033[1m==>\033[0m %s\n' "$*"; }
skip() { printf '    %s (already installed)\n' "$*"; }
run()  {
  printf '    $ %s\n' "$*"
  if [ "$DRY" -eq 0 ]; then "$@"; fi
}

[ "$(uname -s)" = "Darwin" ] || { echo "This script is for macOS. Use install_linux.sh or install_windows.ps1." >&2; exit 2; }

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required and is not installed." >&2
  echo "Install it from https://brew.sh, open a new terminal, then run this script again." >&2
  exit 1
fi

brew_formula() {   # brew_formula <formula> [label]
  if brew list --formula "$1" >/dev/null 2>&1; then skip "${2:-$1}"; else run brew install "$1"; fi
}
brew_cask() {      # brew_cask <cask> <app path>
  if [ -e "$2" ] || brew list --cask "$1" >/dev/null 2>&1; then skip "$1"; else run brew install --cask "$1"; fi
}

say "KiCad (schematic, PCB, kicad-cli, pcbnew Python)"
brew_cask kicad "/Applications/KiCad/KiCad.app"

say "Blender (assembly, validation, Cycles renders)"
brew_cask blender "/Applications/Blender.app"

say "OpenJDK (runs Freerouting) and librsvg (SVG → PDF/PNG)"
brew_formula openjdk
brew_formula librsvg

say "git and Python 3.10+"
if command -v git >/dev/null 2>&1; then skip git; else brew_formula git; fi
if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  skip "python3 $(python3 -c 'import platform; print(platform.python_version())')"
else
  brew_formula python
fi

say "Freerouting ${FREEROUTING_VERSION} (autorouter)"
JAR="$FREEROUTING_DIR/freerouting-${FREEROUTING_VERSION}.jar"
if [ -f "$JAR" ] && [ "$(shasum -a 256 "$JAR" | cut -d' ' -f1)" = "$FREEROUTING_SHA256" ]; then
  skip "$JAR"
else
  URL="https://github.com/freerouting/freerouting/releases/download/v${FREEROUTING_VERSION}/freerouting-${FREEROUTING_VERSION}.jar"
  run mkdir -p "$FREEROUTING_DIR"
  run curl -fL --retry 3 -o "$JAR.part" "$URL"
  if [ "$DRY" -eq 0 ]; then
    GOT="$(shasum -a 256 "$JAR.part" | cut -d' ' -f1)"
    if [ "$GOT" != "$FREEROUTING_SHA256" ]; then
      rm -f "$JAR.part"
      echo "Checksum mismatch for $URL (got $GOT). Nothing installed." >&2
      exit 1
    fi
    mv "$JAR.part" "$JAR"
  else
    printf '    (verify sha256 = %s, then rename to %s)\n' "$FREEROUTING_SHA256" "$JAR"
  fi
fi

if [ "$BLENDER_MODULES" -eq 1 ]; then
  say "scipy in Blender's bundled Python (flood fill and distance transform)"
  BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
  BPY=""
  for cand in /Applications/Blender.app/Contents/Resources/*/python/bin/python3.*; do
    [ -x "$cand" ] && BPY="$cand"          # glob order is sorted; the last match is the newest
  done
  if [ -z "$BPY" ] && [ "$DRY" -eq 1 ]; then
    BPY="/Applications/Blender.app/Contents/Resources/<version>/python/bin/python3.x"
  fi
  if [ -z "$BPY" ]; then
    echo "    Blender's Python not found; run this script again after Blender is installed." >&2
  elif [ "$DRY" -eq 0 ] && "$BLENDER" -b --factory-startup --python-expr "import scipy" >/dev/null 2>&1; then
    skip "scipy"
  else
    # Blender ships numpy; install scipy without dependencies so the bundled numpy stays in use.
    run "$BPY" -m ensurepip --upgrade
    if [ "$DRY" -eq 1 ] || [ -w "$(dirname "$(dirname "$BPY")")/lib" ]; then
      run "$BPY" -m pip install --upgrade --no-deps scipy
    else
      MOD="$("$BLENDER" -b --factory-startup --python-expr \
        "import bpy; print('HDT_DIR=' + bpy.utils.user_resource('SCRIPTS', path='modules', create=True))" 2>/dev/null \
        | sed -n 's/^HDT_DIR=//p')"
      run "$BPY" -m pip install --upgrade --no-deps --target "$MOD" scipy
    fi
  fi
fi

say "CAD venv with build123d (enclosure STEP/STL/GLB) at $CAD_VENV"
if [ -x "$CAD_VENV/bin/python" ] && "$CAD_VENV/bin/python" -c "import build123d" >/dev/null 2>&1; then
  skip "build123d"
elif command -v uv >/dev/null 2>&1; then
  run uv venv -p 3.12 "$CAD_VENV"
  run uv pip install -p "$CAD_VENV/bin/python" build123d
else
  PY_CAD=""
  for v in 3.13 3.12 3.11 3.10; do command -v "python$v" >/dev/null 2>&1 && { PY_CAD="python$v"; break; }; done
  if [ -z "$PY_CAD" ]; then brew_formula python@3.12; PY_CAD="$(brew --prefix)/opt/python@3.12/bin/python3.12"; fi
  run "$PY_CAD" -m venv "$CAD_VENV"
  run "$CAD_VENV/bin/python" -m pip install --upgrade pip build123d
fi

say "Headless browser (presentation layout check and PDF)"
if [ -e "/Applications/Google Chrome.app" ] || [ -e "/Applications/Chromium.app" ] || [ -e "/Applications/Microsoft Edge.app" ]; then
  skip "Chrome/Chromium"
else
  run brew install --cask google-chrome
fi

if [ "$OPTIONAL" -eq 1 ]; then
  say "Optional: ffmpeg, ImageMagick, libheif, FreeCAD, KiKit"
  brew_formula ffmpeg
  brew_formula imagemagick
  brew_formula libheif
  brew_cask freecad "/Applications/FreeCAD.app"
  KPY=""
  for cand in /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/*/bin/python3; do
    [ -x "$cand" ] && KPY="$cand"
  done
  if command -v kikit >/dev/null 2>&1 || { [ -n "$KPY" ] && "$KPY" -c "import kikit" >/dev/null 2>&1; }; then
    skip "KiKit"
  elif [ -n "$KPY" ] || [ "$DRY" -eq 1 ]; then
    run "${KPY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/<ver>/bin/python3}" -m pip install --user kikit
  else
    echo "    KiCad's Python not found; install KiCad first, then rerun with --with-optional." >&2
  fi
fi

if [ "$ASSETS" -eq 1 ]; then
  say "Render assets into $ASSETS_DIR (ambientCG CC0 textures, Poly Haven CC0 HDRI)"
  fetch_zip() {     # fetch_zip <set> <variant>
    if [ -d "$ASSETS_DIR/textures/$1" ]; then skip "$1"; return; fi
    run mkdir -p "$ASSETS_DIR/textures/$1"
    run curl -fL --retry 3 -o "$ASSETS_DIR/textures/$1.zip" "https://ambientcg.com/get?file=$1_$2.zip"
    run unzip -q -o "$ASSETS_DIR/textures/$1.zip" -d "$ASSETS_DIR/textures/$1"
    run rm -f "$ASSETS_DIR/textures/$1.zip"
  }
  fetch_zip Fingerprints009 2K-PNG
  fetch_zip Smear003 2K-JPG
  fetch_zip Scratches005 2K-PNG
  fetch_zip SurfaceImperfections015 2K-PNG
  HDR="$ASSETS_DIR/hdri/studio_small_09_2k.exr"
  if [ -f "$HDR" ]; then skip "studio_small_09"; else
    run mkdir -p "$ASSETS_DIR/hdri"
    run curl -fL --retry 3 -o "$HDR" "https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/2k/studio_small_09_2k.exr"
  fi
fi

if [ "$CLOUD" -eq 1 ]; then
  say "Cloud rendering: AWS CLI and Session Manager plugin"
  brew_formula awscli
  if command -v session-manager-plugin >/dev/null 2>&1; then skip session-manager-plugin
  else run brew install --cask session-manager-plugin; fi
fi

say "Check"
DOCTOR="$(cd "$(dirname "$0")" && pwd)/doctor.py"
if [ "$DRY" -eq 1 ]; then
  printf '    $ python3 %s\n' "$DOCTOR"
  echo "install_macos: dry run finished, nothing changed"
else
  python3 "$DOCTOR" || true
  echo "install_macos: finished"
fi
