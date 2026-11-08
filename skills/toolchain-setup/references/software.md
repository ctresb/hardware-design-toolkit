# Software used by the toolkit

Versions are the minimum the toolkit supports. "Tested" is the version the scripts were run with.

## Required

| Tool (doctor id) | Role in the toolkit | Minimum (tested) | License | Official download |
|---|---|---|---|---|
| KiCad: `kicad-cli` (`kicad_cli`) | ERC, DRC, netlists, Gerber/drill, BOM, STEP/GLB/VRML export of boards | 9.0 (10.0) | GPL-3.0 | https://www.kicad.org/download/ |
| KiCad Python with `pcbnew` (`kicad_python`) | scripted footprint placement, outlines, keepouts, zones, DSN export for routing | ships with KiCad | GPL-3.0 | included with KiCad |
| Freerouting (`freerouting_jar`) | autorouter: Specctra DSN in, SES out | 1.9 (1.9.0 pinned; 2.5.0 optional) | GPL-3.0 | https://github.com/freerouting/freerouting/releases |
| Java runtime, OpenJDK/Temurin (`java`) | runs Freerouting | 17 for 1.9.0, 25 for 2.5.0 (21, 25, 27) | GPL-2.0 with Classpath Exception | https://adoptium.net/ or `brew install openjdk` |
| Blender (`blender`) | 3D assembly, geometry validator, free-space map, solder simulation, Cycles renders, vector drawings | 4.2 LTS (5.2 LTS) | GPL-2.0-or-later | https://www.blender.org/download/ |
| numpy in Blender's Python (`blender_numpy`) | mesh math in every Blender script | bundled with Blender | BSD-3-Clause | bundled |
| scipy in Blender's Python (`blender_scipy`) | flood fill (`ndimage.label`), distance transform, interpolation in the free-space map | 1.11 | BSD-3-Clause | https://pypi.org/project/scipy/ |
| Python (`python`) | standalone scripts: doctor, power budget, battery sizing, cost model, presentation builder | 3.10 | PSF-2.0 | https://www.python.org/downloads/ |
| git (`git`) | every hardware project is a git repository | 2.30 | GPL-2.0 | https://git-scm.com/downloads |
| build123d in a dedicated venv (`cad_python`) | parametric enclosure CAD: STEP for molders, STL for prints, GLB for Blender, DFM check | build123d 0.13 on Python 3.10–3.13 (0.13 on 3.12) | Apache-2.0 | https://github.com/gumyr/build123d (installed with `uv` from https://docs.astral.sh/uv/, or pip) |
| Chrome / Chromium / Edge (`chrome`) | headless browser: presentation layout check (part of its gate) and HTML → PDF | any current | proprietary / BSD | https://www.google.com/chrome/ or https://www.chromium.org/ |
| librsvg: `rsvg-convert` (`rsvg_convert`) | SVG drawings and labels → PDF/PNG | 2.50 | LGPL-2.1-or-later | https://gitlab.gnome.org/GNOME/librsvg (Homebrew, apt `librsvg2-bin`, MSYS2 `mingw-w64-ucrt-x86_64-librsvg`) |

## Optional

| Tool (doctor id) | Role | Install flag | License | Official download |
|---|---|---|---|---|
| cupy (`blender_cupy`) | GPU flood fill and distance transform on NVIDIA; the free-space map falls back to scipy on the CPU | `--with-gpu` | MIT | https://cupy.dev/ |
| ffmpeg (`ffmpeg`) | turntable and motion videos from rendered frames | `--with-optional` | LGPL/GPL | https://ffmpeg.org/download.html |
| ImageMagick (`imagemagick`) | contact sheets, crops, format conversion of renders | `--with-optional` | ImageMagick License | https://imagemagick.org/script/download.php |
| HEIC converter: `sips` on macOS, `heif-convert` from libheif elsewhere (`heic_converter`) | phone photos (HEIC) used as reference or backplates | `--with-optional` (libheif) | LGPL-3.0 (libheif) | https://github.com/strukturag/libheif |
| KiKit (`kikit`) | PCB panelization to meet assembly minimum sizes | `--with-optional` | MIT | https://github.com/yaqwsx/KiKit |
| FreeCAD (`freecad`) | STEP viewer for a visual check of CAD hand-off files | `--with-optional` | LGPL-2.0-or-later | https://www.freecad.org/downloads.php |
| Render assets (`render_assets`) | ambientCG wear textures (Fingerprints009, Smear003, Scratches005, SurfaceImperfections015) and the Poly Haven HDRI studio_small_09 | `--with-assets` | CC0 | https://ambientcg.com/ and https://polyhaven.com/ |
| GitHub CLI (`gh`) | publishing a project, issues, releases | install by hand | MIT | https://cli.github.com/ |
| AWS CLI v2 (`aws`) | cloud GPU rendering: S3 transfers, instance start/stop | `--with-cloud` | Apache-2.0 | https://aws.amazon.com/cli/ |
| AWS Session Manager plugin (`session_manager_plugin`) | shell on the render machine without SSH keys or open ports | `--with-cloud` | Apache-2.0 | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html |

## Where doctor looks

| Tool | macOS | Linux | Windows |
|---|---|---|---|
| kicad-cli | PATH, `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` | PATH, `/usr/bin`, `/snap/bin`, Flatpak `org.kicad.KiCad` | `Program Files\KiCad\<ver>\bin\kicad-cli.exe` |
| KiCad Python | `KiCad.app/Contents/Frameworks/Python.framework/Versions/*/bin/python3` | system `python3` that can `import pcbnew` | `Program Files\KiCad\<ver>\bin\python.exe` |
| Blender | PATH, `/Applications/Blender.app/Contents/MacOS/Blender` | PATH, `/snap/bin`, `/opt/blender*`, `~/blender*`, Flatpak exports | `Program Files\Blender Foundation\Blender <ver>\blender.exe` |
| Java | `JAVA_HOME`, `/opt/homebrew/opt/openjdk`, `/usr/local/opt/openjdk`, `/Library/Java/JavaVirtualMachines/*` | `JAVA_HOME`, `/usr/lib/jvm/*`, PATH | `JAVA_HOME`, `Program Files\Eclipse Adoptium`, `Microsoft\jdk-*`, PATH |
| Freerouting jar | `~/.local/share/freerouting/freerouting-<ver>.jar` | same, or `$XDG_DATA_HOME/freerouting` | `%LOCALAPPDATA%\freerouting\` |
| rsvg-convert | PATH | PATH | PATH, `C:\msys64\ucrt64\bin`, `C:\msys64\mingw64\bin` |

When several versions are installed, doctor picks the highest. Override any tool with its environment variable; the list is in SKILL.md.

## Freerouting version

The installers pin **1.9.0**. On a dense 28 mm 4-layer board it routed to 4 open connections, while 2.5.0 stopped after about 19 passes with 26 to 35 open. 1.9.0 needs Java 17+ and opens a window: on a headless Linux machine it runs under `xvfb-run` (the Linux installer adds `xvfb`). 2.5.0 is headless but needs Java 25, because its classes are compiled for class-file version 69. `doctor.py` reads the version each jar needs from its Main-Class and flags a Java that is too old. To use 2.5.0, set `FREEROUTING_VERSION=2.5.0` and `FREEROUTING_SHA256=f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`, and install Java 25.
