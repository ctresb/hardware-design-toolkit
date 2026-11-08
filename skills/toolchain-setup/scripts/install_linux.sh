#!/usr/bin/env bash
# Install the Hardware Design Toolkit toolchain on Linux (apt, dnf or pacman; Flatpak for the GUI apps).
# Idempotent: every step checks first and skips what is already installed. Uses sudo for system packages.
#
# usage: install_linux.sh [--dry-run] [--flatpak] [--with-optional] [--with-cloud] [--with-gpu] [--with-assets]
#                         [--skip-blender-modules]
#   --dry-run               print every command, change nothing
#   --flatpak               install KiCad and Blender from Flathub instead of the distribution packages
#   --with-optional         also ffmpeg, ImageMagick, libheif, KiKit (panels) and FreeCAD (STEP viewer)
#   --with-assets           download the render wear textures (ambientCG) and a studio HDRI (Poly Haven)
#   --with-cloud            also AWS CLI v2 and the Session Manager plugin (cloud GPU rendering)
#   --with-gpu              also cupy (CUDA 12) in Blender's Python, for NVIDIA machines
#   --skip-blender-modules  do not pip-install scipy into Blender's Python
#
# KiCad: distribution packages are often one major version behind. On Ubuntu/Debian this script adds the
# official KiCad PPA (ppa:kicad/kicad-10.0-releases). KiCad 9 or newer is required.
# Blender: distribution packages lag too; --flatpak or the official tarball (blender.org) gives the current LTS.
set -euo pipefail

# Freerouting 1.9.0 (Java 17+) routes dense small boards further than 2.5.0, which needs Java 25 and stops after
# ~19 passes. For 2.5.0: FREEROUTING_VERSION=2.5.0 FREEROUTING_SHA256=f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7
FREEROUTING_VERSION="${FREEROUTING_VERSION:-1.9.0}"
FREEROUTING_SHA256="${FREEROUTING_SHA256:-9084a4888937a7f31f857ecc12aa7a37407f51160e4d2892dff9c9bb47ae3102}"
FREEROUTING_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/freerouting"
TOOLKIT_DATA="${XDG_DATA_HOME:-$HOME/.local/share}/hardware-design-toolkit"
CAD_VENV="$TOOLKIT_DATA/venv"          # build123d needs Python 3.10–3.13
ASSETS_DIR="$TOOLKIT_DATA/assets"
KICAD_PPA="${KICAD_PPA:-ppa:kicad/kicad-10.0-releases}"

DRY=0; FLATPAK=0; OPTIONAL=0; CLOUD=0; GPU=0; ASSETS=0; BLENDER_MODULES=1
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --flatpak) FLATPAK=1 ;;
    --with-optional) OPTIONAL=1 ;;
    --with-cloud) CLOUD=1 ;;
    --with-gpu) GPU=1 ;;
    --with-assets) ASSETS=1 ;;
    --skip-blender-modules) BLENDER_MODULES=0 ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

say()  { printf '\033[1m==>\033[0m %s\n' "$*"; }
skip() { printf '    %s (already installed)\n' "$*"; }
run()  {
  printf '    $ %s\n' "$*"
  if [ "$DRY" -eq 0 ]; then "$@"; fi
}
have() { command -v "$1" >/dev/null 2>&1; }

[ "$(uname -s)" = "Linux" ] || { echo "This script is for Linux." >&2; exit 2; }

if have apt-get; then PM=apt
elif have dnf; then PM=dnf
elif have pacman; then PM=pacman
else echo "No supported package manager (apt, dnf, pacman) found." >&2; exit 1
fi
SUDO=(); [ "$(id -u)" -eq 0 ] || SUDO=(sudo)

APT_UPDATED=0
pkg() {   # pkg <command to test> <apt name> <dnf name> <pacman name>
  if have "$1"; then skip "$1"; return; fi
  case "$PM" in
    apt)
      if [ "$APT_UPDATED" -eq 0 ]; then run "${SUDO[@]}" apt-get update; APT_UPDATED=1; fi
      run "${SUDO[@]}" apt-get install -y "$2" ;;
    dnf) run "${SUDO[@]}" dnf install -y "$3" ;;
    pacman) run "${SUDO[@]}" pacman -S --needed --noconfirm "$4" ;;
  esac
}

flatpak_app() {   # flatpak_app <app id>
  pkg flatpak flatpak flatpak flatpak
  run flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
  if [ "$DRY" -eq 0 ] && flatpak info "$1" >/dev/null 2>&1; then skip "$1"; else run flatpak install --user -y flathub "$1"; fi
}

say "git, Python 3.10+, OpenJDK 21+, librsvg"
pkg git git git git
pkg python3 python3 python3 python
pkg rsvg-convert librsvg2-bin librsvg2-tools librsvg
JAVA_MAJOR=0
if have java; then JAVA_MAJOR="$(java -version 2>&1 | sed -n 's/.*version "\([0-9]*\).*/\1/p' | head -1 || true)"; fi
if [ "${JAVA_MAJOR:-0}" -ge 21 ]; then skip "java $JAVA_MAJOR"
else
  case "$PM" in
    apt) run "${SUDO[@]}" apt-get install -y openjdk-21-jre-headless ;;
    dnf) run "${SUDO[@]}" dnf install -y java-21-openjdk-headless ;;
    pacman) run "${SUDO[@]}" pacman -S --needed --noconfirm jre21-openjdk-headless ;;
  esac
fi
case "$FREEROUTING_VERSION" in
  1.*)                                   # Freerouting 1.x opens a window: headless runs need a virtual display
    if have xvfb-run; then skip "xvfb-run"
    else
      case "$PM" in
        apt) run "${SUDO[@]}" apt-get install -y xvfb ;;
        dnf) run "${SUDO[@]}" dnf install -y xorg-x11-server-Xvfb ;;
        pacman) run "${SUDO[@]}" pacman -S --needed --noconfirm xorg-server-xvfb ;;
      esac
    fi ;;
  2.*) say "note: Freerouting ${FREEROUTING_VERSION} needs the Java its jar was built for (2.5.0: Java 25); doctor checks it" ;;
esac

say "KiCad 9+ (kicad-cli, pcbnew Python)"
if [ "$FLATPAK" -eq 1 ]; then
  flatpak_app org.kicad.KiCad
elif have kicad-cli; then
  skip "kicad-cli $(kicad-cli --version 2>/dev/null || true)"
else
  case "$PM" in
    apt)
      if grep -qi ubuntu /etc/os-release 2>/dev/null; then
        pkg add-apt-repository software-properties-common software-properties-common software-properties-common
        run "${SUDO[@]}" add-apt-repository -y "$KICAD_PPA"
        run "${SUDO[@]}" apt-get update
      fi
      run "${SUDO[@]}" apt-get install -y --install-recommends kicad ;;
    dnf) run "${SUDO[@]}" dnf install -y kicad ;;
    pacman) run "${SUDO[@]}" pacman -S --needed --noconfirm kicad kicad-library ;;
  esac
fi

say "Blender (assembly, validation, Cycles renders)"
if [ "$FLATPAK" -eq 1 ]; then
  flatpak_app org.blender.Blender
elif have blender; then
  skip "blender"
elif have snap; then
  run "${SUDO[@]}" snap install blender --classic
else
  case "$PM" in
    apt) run "${SUDO[@]}" apt-get install -y blender ;;
    dnf) run "${SUDO[@]}" dnf install -y blender ;;
    pacman) run "${SUDO[@]}" pacman -S --needed --noconfirm blender ;;
  esac
  echo "    Distribution Blender may be old. Blender 4.2 LTS or newer is required; the official tarball is at"
  echo "    https://www.blender.org/download/ (unpack it and put the 'blender' binary on PATH)."
fi

say "Freerouting ${FREEROUTING_VERSION} (autorouter)"
JAR="$FREEROUTING_DIR/freerouting-${FREEROUTING_VERSION}.jar"
if [ -f "$JAR" ] && [ "$(sha256sum "$JAR" | cut -d' ' -f1)" = "$FREEROUTING_SHA256" ]; then
  skip "$JAR"
else
  URL="https://github.com/freerouting/freerouting/releases/download/v${FREEROUTING_VERSION}/freerouting-${FREEROUTING_VERSION}.jar"
  pkg curl curl curl curl
  run mkdir -p "$FREEROUTING_DIR"
  run curl -fL --retry 3 -o "$JAR.part" "$URL"
  if [ "$DRY" -eq 0 ]; then
    GOT="$(sha256sum "$JAR.part" | cut -d' ' -f1)"
    if [ "$GOT" != "$FREEROUTING_SHA256" ]; then
      rm -f "$JAR.part"; echo "Checksum mismatch for $URL (got $GOT). Nothing installed." >&2; exit 1
    fi
    mv "$JAR.part" "$JAR"
  else
    printf '    (verify sha256 = %s, then rename to %s)\n' "$FREEROUTING_SHA256" "$JAR"
  fi
fi

blender_cmd() {
  if [ "$FLATPAK" -eq 1 ]; then echo "flatpak run org.blender.Blender"; else echo "blender"; fi
}

if [ "$BLENDER_MODULES" -eq 1 ]; then
  say "scipy (and cupy with --with-gpu) in Blender's bundled Python"
  BL="$(blender_cmd)"
  if [ "$DRY" -eq 1 ]; then
    BPY="<Blender's python, read with: $BL -b --python-expr 'import sys; print(sys.executable)'>"
    MOD="<Blender user scripts/modules folder>"
  else
    # shellcheck disable=SC2086
    INFO="$($BL -b --factory-startup --python-expr \
      "import sys, bpy; print('HDT_PY=' + sys.executable); print('HDT_DIR=' + bpy.utils.user_resource('SCRIPTS', path='modules', create=True))" 2>/dev/null || true)"
    BPY="$(printf '%s\n' "$INFO" | sed -n 's/^HDT_PY=//p')"
    MOD="$(printf '%s\n' "$INFO" | sed -n 's/^HDT_DIR=//p')"
  fi
  if [ -z "$BPY" ]; then
    echo "    Could not start Blender headless; run this script again after Blender is installed." >&2
  elif [ "$FLATPAK" -eq 1 ]; then
    echo "    Flatpak Blender: install modules from inside the sandbox:"
    echo "    flatpak run --command=sh org.blender.Blender -c 'python3 -m pip install --user --no-deps scipy'"
  else
    run "$BPY" -m ensurepip --upgrade
    # numpy is bundled with Blender; --no-deps keeps the bundled one in use.
    run "$BPY" -m pip install --upgrade --no-deps --target "$MOD" scipy
    if [ "$GPU" -eq 1 ]; then
      if have nvidia-smi; then run "$BPY" -m pip install --upgrade --target "$MOD" cupy-cuda12x fastrlock
      else echo "    --with-gpu: no nvidia-smi found, cupy skipped"; fi
    fi
  fi
fi

say "CAD venv with build123d (enclosure STEP/STL/GLB) at $CAD_VENV"
if [ -x "$CAD_VENV/bin/python" ] && "$CAD_VENV/bin/python" -c "import build123d" >/dev/null 2>&1; then
  skip "build123d"
elif have uv; then
  run uv venv -p 3.12 "$CAD_VENV"
  run uv pip install -p "$CAD_VENV/bin/python" build123d
else
  PY_CAD=""
  for v in 3.13 3.12 3.11 3.10; do have "python$v" && { PY_CAD="python$v"; break; }; done
  if [ -z "$PY_CAD" ]; then
    echo "    No Python 3.10–3.13 found. Install uv (https://docs.astral.sh/uv/) or python3.12, then rerun." >&2
  else
    if [ "$PM" = apt ] && ! "$PY_CAD" -c "import ensurepip" >/dev/null 2>&1; then
      run "${SUDO[@]}" apt-get install -y "${PY_CAD}-venv"      # Debian/Ubuntu split venv out of python3.x
    fi
    run "$PY_CAD" -m venv "$CAD_VENV"
    run "$CAD_VENV/bin/python" -m pip install --upgrade pip build123d
  fi
fi

say "Headless browser (presentation layout check and PDF)"
if have google-chrome || have google-chrome-stable || have chromium || have chromium-browser || have microsoft-edge; then
  skip "Chrome/Chromium"
elif [ "$FLATPAK" -eq 1 ]; then
  flatpak_app org.chromium.Chromium
else
  pkg chromium chromium chromium chromium
fi

if [ "$OPTIONAL" -eq 1 ]; then
  say "Optional: ffmpeg, ImageMagick, libheif, FreeCAD, KiKit"
  pkg ffmpeg ffmpeg ffmpeg ffmpeg
  if have magick || have convert; then skip imagemagick; else pkg magick imagemagick ImageMagick imagemagick; fi
  pkg heif-convert libheif-examples libheif-tools libheif
  if [ "$FLATPAK" -eq 1 ]; then flatpak_app org.freecad.FreeCAD; else pkg freecadcmd freecad freecad freecad; fi
  if have kikit || python3 -c "import pcbnew, kikit" >/dev/null 2>&1; then skip KiKit
  else run python3 -m pip install --user kikit; fi      # KiKit needs the Python that imports pcbnew
fi

if [ "$ASSETS" -eq 1 ]; then
  say "Render assets into $ASSETS_DIR (ambientCG CC0 textures, Poly Haven CC0 HDRI)"
  pkg unzip unzip unzip unzip
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
  say "Cloud rendering: AWS CLI v2 and Session Manager plugin"
  ARCH="$(uname -m)"
  if have aws; then skip aws
  else
    pkg unzip unzip unzip unzip
    if [ "$DRY" -eq 0 ]; then TMP="$(mktemp -d)"; else TMP="/tmp/hdt-awscli"; fi
    run curl -fL -o "$TMP/awscliv2.zip" "https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip"
    run unzip -q "$TMP/awscliv2.zip" -d "$TMP"
    run "${SUDO[@]}" "$TMP/aws/install"
  fi
  if have session-manager-plugin; then skip session-manager-plugin
  else
    BASE="https://s3.amazonaws.com/session-manager-downloads/plugin/latest"
    if [ "$PM" = apt ]; then
      D="ubuntu_64bit"; [ "$ARCH" = aarch64 ] && D="ubuntu_arm64"
      run curl -fL -o /tmp/session-manager-plugin.deb "$BASE/$D/session-manager-plugin.deb"
      run "${SUDO[@]}" dpkg -i /tmp/session-manager-plugin.deb
    else
      D="linux_64bit"; [ "$ARCH" = aarch64 ] && D="linux_arm64"
      run "${SUDO[@]}" dnf install -y "$BASE/$D/session-manager-plugin.rpm"
    fi
  fi
fi

say "Check"
DOCTOR="$(cd "$(dirname "$0")" && pwd)/doctor.py"
if [ "$DRY" -eq 1 ]; then
  printf '    $ python3 %s\n' "$DOCTOR"
  echo "install_linux: dry run finished, nothing changed"
else
  python3 "$DOCTOR" || true
  echo "install_linux: finished"
fi
