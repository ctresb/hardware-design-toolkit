---
name: toolchain-setup
description: Installs and checks the software the Hardware Design Toolkit needs (KiCad, Freerouting with Java, Blender with numpy/scipy, a build123d CAD venv, a headless browser, librsvg, git, Python), and records the tool paths for the other skills. Use on first use of the toolkit, when a script cannot find KiCad, Blender, Java or rsvg-convert, or when the user asks to install or check the tools ("install KiCad", "set up the toolchain", "doctor").
---

# Toolchain setup

Installs the toolkit's software, checks it, and writes `toolchain.json` with every tool path. Other skills read that file instead of guessing paths.

Talk to the user in the user's language. Commands and file names stay as they are.

## Inputs

- None required.
- `hw/` in the current project, if it exists. Doctor then also writes `hw/toolchain.json`.

## Outputs

- `~/.config/hardware-design-toolkit/toolchain.json`. On Windows, `%APPDATA%\hardware-design-toolkit\toolchain.json`. `XDG_CONFIG_HOME` is respected.
- `hw/toolchain.json` when the project has a `hw/` folder. This copy overrides the user-level one.

## Gate

`scripts/doctor.py` exits with 0 and prints `required: OK`. Until then, no other skill runs a script that needs a missing tool.

## Procedure

1. **Check first.** Run `python3 ${CLAUDE_SKILL_DIR}/scripts/doctor.py` from the project root. On Windows use `python`. It takes about 5 s, because it starts Blender headless once to read its Python, modules and GPU.
2. **If `required: OK`,** stop. Tell the user, in one line, which optional tools are missing and what they would add.
3. **If something required is missing, ask before installing anything.** Installing changes the user's system. Show the user:
   - the list of what will be installed and why: one line per tool from the doctor table and `references/software.md`;
   - the approximate download size: KiCad ~1.5 GB with libraries, Blender ~400 MB, JRE ~50 MB, Freerouting jar ~65 MB, scipy ~40 MB;
   - that a password (sudo) may be asked;
   - the dry run output of the installer (step 4).

   Install only after the user says yes.
4. **Show the plan.** Run the installer for the OS with `--dry-run` (PowerShell: `-DryRun`):

   | OS | Command |
   |---|---|
   | macOS | `bash ${CLAUDE_SKILL_DIR}/scripts/install_macos.sh --dry-run` (needs Homebrew; if it is missing, the script points to https://brew.sh) |
   | Linux | `bash ${CLAUDE_SKILL_DIR}/scripts/install_linux.sh --dry-run` (apt, dnf or pacman; add `--flatpak` to get the current KiCad and Blender from Flathub) |
   | Windows | `powershell -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/scripts/install_windows.ps1" -DryRun` (winget) |

5. **Install.** Run the same command without the dry-run flag. Add flags only when the user wants them:
   - `--with-optional`: ffmpeg (turntable videos), ImageMagick, libheif (HEIC phone photos as references), KiKit (PCB panels, into KiCad's Python), FreeCAD (STEP viewer).
   - `--with-assets`: the render wear textures (ambientCG CC0: Fingerprints009, Smear003, Scratches005, SurfaceImperfections015) and the studio HDRI `studio_small_09` (Poly Haven CC0), into `~/.local/share/hardware-design-toolkit/assets/` (`%LOCALAPPDATA%` on Windows). `product-render` reads them from `tc["assets"]`.
   - `--with-cloud`: AWS CLI and Session Manager plugin, for rendering on a cloud GPU. Never install these unless the user plans to render in the cloud.
   - `--with-gpu` (Linux, Windows): cupy for NVIDIA GPUs. It speeds up the free-space flood fill.
6. **Verify.** Run `scripts/doctor.py` again. Report the table in a short form: ✓ for found, ✗ for required and missing, – for optional and missing.
7. **Fix what remains by hand.** The common cases are in "Taste and pitfalls" below.

The installers are idempotent. Running them again skips what is installed and verifies the Freerouting checksum.

## How other skills use `toolchain.json`

Read the project file first, then the user file:

```python
import json, os, subprocess
def toolchain():
    base = os.environ.get("APPDATA") if os.name == "nt" else \
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    for p in ("hw/toolchain.json", os.path.join(base, "hardware-design-toolkit", "toolchain.json")):
        if os.path.isfile(p):
            return json.load(open(p))
    raise SystemExit("toolchain.json not found: run the toolchain-setup skill (scripts/doctor.py)")

tc = toolchain()
subprocess.run(tc["cmd"]["kicad_cli"] + ["pcb", "drc", "board.kicad_pcb"])   # cmd is an argv list
```

- Use `tc["cmd"][id]`, an argv list, to run a tool. It also covers Flatpak installs, where the "path" is `flatpak run …`.
- Use `tc["paths"][id]` when a plain file path is needed, for example the Freerouting jar.
- If a key is `null`, the tool is missing. Tell the user to run this skill. Do not guess a path.

Schema (`"schema": "hardware-design-toolkit/toolchain@1"`):

```json
{
  "schema": "hardware-design-toolkit/toolchain@1",
  "generated_at": "2026-01-01T12:00:00+00:00",
  "os": "macos | linux | windows",
  "arch": "arm64",
  "ok": true,
  "missing_required": [],
  "paths":    {"<id>": "/abs/path or null"},
  "cmd":      {"<id>": ["argv", "list"] },
  "versions": {"<id>": "x.y.z or null"},
  "blender_gpu": [{"type": "OPTIX | CUDA | METAL | HIP | ONEAPI", "devices": ["name"]}],
  "assets":   {"Fingerprints009": "/abs/.../textures/Fingerprints009", "studio_small_09": "/abs/.../hdri/studio_small_09_2k.exr"},
  "tools": {"<id>": {"id": "", "found": true, "path": "", "cmd": [], "version": "", "required": true,
                     "ok": true, "note": "", "purpose": ""}}
}
```

Tool ids:

- **Required:** `kicad_cli`, `kicad_python` (a Python that can `import pcbnew`), `blender`, `blender_python`, `blender_numpy`, `blender_scipy`, `java` (17 or newer; the Java the Freerouting jar needs: 17 for 1.9.0, 25 for 2.5.0), `freerouting_jar`, `python` (3.10 or newer), `cad_python` (the build123d venv, Python 3.10–3.13), `git`, `rsvg_convert`, `chrome` (headless browser for the presentation layout check and PDF).
- **Optional:** `blender_cupy`, `kikit`, `freecad`, `ffmpeg`, `imagemagick`, `heic_converter` (sips on macOS), `render_assets`, `gh`, `aws`, `session_manager_plugin`.

Environment overrides, checked before the search: `KICAD_CLI`, `KICAD_PYTHON`, `BLENDER`, `JAVA` or `JAVA_HOME`, `FREEROUTING_JAR`, `RSVG_CONVERT`, `CHROME`, `CAD_PYTHON`, `FREECAD`.

## Taste and pitfalls

- **Never install without consent.** Show the dry run first. Do not add `--with-cloud` "just in case".
- **macOS `/usr/bin/java` is a stub.** It prints "Unable to locate a Java Runtime" even when Homebrew's OpenJDK is installed. Homebrew's OpenJDK is keg-only: it lives in `/opt/homebrew/opt/openjdk/bin/java` and is not on PATH. Doctor checks that location. Scripts must use `tc["cmd"]["java"]`, not `java`.
- **KiCad's Python is not the system Python.** On macOS and Windows, `pcbnew` imports only in KiCad's bundled interpreter. On Linux it imports in the system `python3`, from the `kicad` package. Run board scripts with `tc["cmd"]["kicad_python"]`.
- **Blender ignores the user's site-packages.** Install modules with Blender's own Python. Use `--no-deps`, so pip does not install a second numpy that shadows the bundled one and breaks the ABI. If the app bundle is read-only, the installers install into Blender's user `scripts/modules` folder, which Blender puts on `sys.path`.
- **Distribution packages lag.** Ubuntu's own KiCad and Blender can be a major version behind. Use the KiCad PPA or `--flatpak`. The toolkit needs KiCad 9 or newer, and Blender 4.2 LTS or newer; it is tested on KiCad 10 and Blender 5.2.
- **Pin Freerouting and verify it.** The installers download 1.9.0 and check its SHA-256 (why 1.9.0: `references/software.md`). To upgrade, change `FREEROUTING_VERSION` and `FREEROUTING_SHA256` together. The digest is listed on the GitHub release page.
- **No GPU listed in `blender_gpu`** means Cycles renders on the CPU. That works, but slowly. For 4K or turntables, suggest a machine with an NVIDIA (OptiX) or Apple Silicon (Metal) GPU, or a cloud GPU (`product-render`).
- **build123d needs Python 3.10–3.13.** It has no wheels for newer Pythons, so pip on the system Python 3.14+ fails to resolve it. The installers create a dedicated venv at `~/.local/share/hardware-design-toolkit/venv`. They prefer `uv` (`uv venv -p 3.12 <venv> && uv pip install -p <venv>/bin/python build123d`), which also downloads Python 3.12 when needed. Without uv they fall back to `python3.12`/`python3.13 -m venv` + pip. Run CAD scripts with `tc["cmd"]["cad_python"]`.
- **Windows `rsvg-convert` comes from MSYS2** (`C:\msys64\ucrt64\bin`). Doctor finds it there, even when it is not on PATH.

## References

- `references/software.md`: every tool, its role in the toolkit, minimum version, license and official download page. Read it when you explain to the user what will be installed.
