#!/usr/bin/env python3
"""Find, check and record every tool the Hardware Design Toolkit uses.

The script detects the OS and looks for each tool on PATH and in the usual install locations. It prints a
table of tools, versions and status, then writes the resolved paths to a JSON file that the other skills read.

Output files:
  ~/.config/hardware-design-toolkit/toolchain.json   (always, unless --no-write)
  hw/toolchain.json                                    (also, when a hw/ folder exists in the current directory,
                                                        or when --project DIR is given)

Environment overrides, checked first: KICAD_CLI, KICAD_PYTHON, BLENDER, JAVA (or JAVA_HOME), FREEROUTING_JAR,
RSVG_CONVERT, CHROME, CAD_PYTHON, FREECAD.

Also recorded: `cad_python` (the build123d venv, default ~/.local/share/hardware-design-toolkit/venv), `kikit`
(panelization), and `assets` (render textures and HDRI downloaded by the installers with --with-assets, default
~/.local/share/hardware-design-toolkit/assets/).

Exit code: 0 when every required tool passes, 1 when a required tool is missing or too old.
Standard library only. Tested on macOS 15 with KiCad 10.0 and Blender 5.2.
"""
import argparse
import datetime
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys

SCHEMA = "hardware-design-toolkit/toolchain@1"
HOME = os.path.expanduser("~")


def system():
    s = platform.system()
    return {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}.get(s, s.lower())


OS = system()
EXE = ".exe" if OS == "windows" else ""


def config_dir():
    if OS == "windows":
        base = os.environ.get("APPDATA", os.path.join(HOME, "AppData", "Roaming"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config"))
    return os.path.join(base, "hardware-design-toolkit")


def data_dir(name):
    if OS == "windows":
        base = os.environ.get("LOCALAPPDATA", os.path.join(HOME, "AppData", "Local"))
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share"))
    return os.path.join(base, name)


def run(cmd, timeout=60):
    """Run a command; return (exit code, stdout + stderr). Never raises."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.SubprocessError) as ex:
        return -1, str(ex)


def vkey(path):
    """Sort key that puts the highest version number found in a path last."""
    nums = re.findall(r"\d+", path)
    return [int(n) for n in nums[-4:]] if nums else [0]


def first_existing(patterns):
    """First existing file among glob patterns; within one pattern, the highest version wins."""
    for pat in patterns:
        hits = [h for h in glob.glob(os.path.expanduser(pat)) if os.path.isfile(h)]
        if hits:
            return sorted(hits, key=vkey)[-1]
    return None


def find(names, env=None, patterns=()):
    if env and os.environ.get(env) and os.path.isfile(os.environ[env]):
        return os.environ[env]
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return first_existing(patterns)


def pf(*parts):
    """Patterns under every Windows Program Files root."""
    roots = [os.environ.get(k) for k in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LOCALAPPDATA")]
    roots = [r for r in roots if r] or [r"C:\Program Files"]
    return [os.path.join(r, *parts) for r in roots]


def tool(id_, path, version=None, required=True, ok=None, note="", cmd=None, purpose=""):
    found = bool(path)
    return {
        "id": id_,
        "found": found,
        "path": path,
        "cmd": cmd if cmd is not None else ([path] if path else None),
        "version": version,
        "required": required,
        "ok": (found if ok is None else (found and ok)),
        "note": note,
        "purpose": purpose,
    }


def first_line_version(cmd, rx=r"(\d+\.\d+(?:\.\d+)?)"):
    code, out = run(cmd)
    m = re.search(rx, out)
    return m.group(1) if m else None


# --------------------------------------------------------------------------- KiCad
def kicad():
    flatpak = None
    if OS == "macos":
        pats = ["/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
                "~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"]
        py_pats = ["/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/*/bin/python3",
                   "~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/*/bin/python3"]
    elif OS == "windows":
        pats = pf("KiCad", "*", "bin", "kicad-cli.exe")
        py_pats = pf("KiCad", "*", "bin", "python.exe")
    else:
        pats = ["/usr/bin/kicad-cli", "/usr/local/bin/kicad-cli", "/snap/bin/kicad-cli"]
        py_pats = []
    cli = find(["kicad-cli"], "KICAD_CLI", pats)
    cli_cmd = [cli] if cli else None
    if not cli and OS == "linux" and shutil.which("flatpak"):
        code, out = run(["flatpak", "info", "org.kicad.KiCad"])
        if code == 0:
            flatpak = ["flatpak", "run", "--command=kicad-cli", "org.kicad.KiCad"]
            cli, cli_cmd = "flatpak:org.kicad.KiCad", flatpak
    ver = first_line_version(cli_cmd + ["--version"]) if cli_cmd else None
    okv = bool(ver) and int(ver.split(".")[0]) >= 9
    t_cli = tool("kicad_cli", cli, ver, ok=okv, cmd=cli_cmd,
                 note="" if okv or not ver else "KiCad 9 or newer is required",
                 purpose="ERC, DRC, netlist, Gerber, STEP/GLB export")

    # Python that can import pcbnew: KiCad's bundled interpreter on macOS/Windows, the system one on Linux.
    cands = []
    if os.environ.get("KICAD_PYTHON"):
        cands.append(os.environ["KICAD_PYTHON"])
    p = first_existing(py_pats)
    if p:
        cands.append(p)
    if OS == "linux":
        cands += [x for x in ("/usr/bin/python3", shutil.which("python3")) if x]
    py, pver = None, None
    for c in dict.fromkeys(cands):
        code, out = run([c, "-c", "import pcbnew; print('PCBNEW', pcbnew.Version())"])
        m = re.search(r"PCBNEW (\S+)", out)
        if code == 0 and m:
            py, pver = c, m.group(1)
            break
    py_cmd = [py] if py else None
    if not py and flatpak:
        py, py_cmd, pver = "flatpak:org.kicad.KiCad", ["flatpak", "run", "--command=python3", "org.kicad.KiCad"], None
    t_py = tool("kicad_python", py, pver, cmd=py_cmd,
                note="" if py else "no Python that can 'import pcbnew' (install KiCad with its scripting support)",
                purpose="board generation and placement scripts (pcbnew API)")
    return [t_cli, t_py]


# --------------------------------------------------------------------------- Blender
PROBE = r"""
import sys, json, importlib
r = {"python": sys.executable, "python_version": sys.version.split()[0], "modules": {}, "gpu": []}
try:
    import bpy
    r["blender_version"] = bpy.app.version_string
except Exception:
    pass
for m in ("numpy", "scipy", "cupy"):
    try:
        r["modules"][m] = getattr(importlib.import_module(m), "__version__", "yes")
    except Exception:
        r["modules"][m] = None
try:
    import bpy
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA", "METAL", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            devs = [d.name for d in prefs.devices if d.type == kind]
            if devs:
                r["gpu"].append({"type": kind, "devices": devs})
        except Exception:
            pass
except Exception:
    pass
print("HDT_PROBE" + json.dumps(r))
"""


def blender():
    if OS == "macos":
        pats = ["/Applications/Blender.app/Contents/MacOS/Blender", "~/Applications/Blender.app/Contents/MacOS/Blender",
                "/Applications/Blender*.app/Contents/MacOS/Blender"]
    elif OS == "windows":
        pats = pf("Blender Foundation", "Blender*", "blender.exe")
    else:
        pats = ["/usr/bin/blender", "/snap/bin/blender", "/opt/blender*/blender", "~/blender*/blender",
                "/var/lib/flatpak/exports/bin/org.blender.Blender", "~/.local/share/flatpak/exports/bin/org.blender.Blender"]
    b = find(["blender"], "BLENDER", pats)
    if not b:
        return [tool("blender", None, purpose="3D assembly, validation, Cycles renders, drawings"),
                tool("blender_python", None, purpose="numpy/scipy for validator and free-space map"),
                tool("blender_numpy", None), tool("blender_scipy", None),
                tool("blender_cupy", None, required=False)], {}
    code, out = run([b, "-b", "--factory-startup", "--python-expr", PROBE], timeout=180)
    m = re.search(r"HDT_PROBE(\{.*\})", out)
    info = json.loads(m.group(1)) if m else {}
    ver = info.get("blender_version") or first_line_version([b, "--version"])
    okv = bool(ver) and int(ver.split(".")[0]) >= 4
    mods = info.get("modules", {})
    bpy_ = info.get("python")
    gpus = info.get("gpu", [])
    gnote = ", ".join(f"{g['type']}: {', '.join(g['devices'])}" for g in gpus) or "no GPU device (CPU render only)"
    out_t = [
        tool("blender", b, ver, ok=okv, note=gnote + ("" if okv else "; Blender 4.2 LTS or newer is required"),
             purpose="3D assembly, validation, Cycles renders, drawings"),
        tool("blender_python", bpy_, info.get("python_version"),
             note="" if bpy_ else "could not start Blender headless to read its Python",
             purpose="Blender's bundled interpreter (pip target for numpy/scipy)"),
        tool("blender_numpy", bpy_ if mods.get("numpy") else None, mods.get("numpy"),
             note="" if mods.get("numpy") else "numpy missing in Blender's Python", purpose="mesh math"),
        tool("blender_scipy", bpy_ if mods.get("scipy") else None, mods.get("scipy"),
             note="" if mods.get("scipy") else "run the installer: it pip-installs scipy into Blender's Python",
             purpose="flood fill and distance transform (free-space map)"),
        tool("blender_cupy", bpy_ if mods.get("cupy") else None, mods.get("cupy"), required=False,
             note="" if mods.get("cupy") else "optional: GPU flood fill on NVIDIA (CUDA) machines",
             purpose="GPU flood fill / distance transform"),
    ]
    return out_t, {"gpu": gpus}


# --------------------------------------------------------------------------- Java + Freerouting
def java():
    cands = []
    if os.environ.get("JAVA") and os.path.isfile(os.environ["JAVA"]):
        cands.append(os.environ["JAVA"])
    if os.environ.get("JAVA_HOME"):
        cands.append(os.path.join(os.environ["JAVA_HOME"], "bin", "java" + EXE))
    if OS == "macos":
        cands += ["/opt/homebrew/opt/openjdk/bin/java", "/usr/local/opt/openjdk/bin/java"]
        cands += sorted(glob.glob("/opt/homebrew/opt/openjdk@*/bin/java") + glob.glob("/usr/local/opt/openjdk@*/bin/java"),
                        key=vkey, reverse=True)
        cands += sorted(glob.glob("/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java"), key=vkey, reverse=True)
    elif OS == "windows":
        for pat in pf("Eclipse Adoptium", "*", "bin", "java.exe") + pf("Microsoft", "jdk-*", "bin", "java.exe") \
                + pf("Java", "*", "bin", "java.exe"):
            cands += sorted(glob.glob(pat), key=vkey, reverse=True)
    else:
        cands += sorted(glob.glob("/usr/lib/jvm/*/bin/java"), key=vkey, reverse=True)
    w = shutil.which("java")
    if w:
        cands.append(w)
    best = None
    for c in dict.fromkeys(cands):
        if not os.path.isfile(c):
            continue
        code, out = run([c, "-version"])
        m = re.search(r'version "(\d+)(?:\.(\d+))?', out)
        if code == 0 and m:
            major = int(m.group(1)) if m.group(1) != "1" else int(m.group(2) or 0)
            ver = re.search(r'version "([^"]+)"', out).group(1)
            if best is None or major > best[1]:
                best = (c, major, ver)
    if not best:
        return tool("java", None, note="no working Java runtime (macOS /usr/bin/java is only a stub)",
                    purpose="runs Freerouting (autorouter)")
    ok = best[1] >= 17
    return tool("java", best[0], best[2], ok=ok, note="" if ok else "Java 17 or newer is required (Freerouting 1.9.0; 2.5.0 needs 25)",
                purpose="runs Freerouting (autorouter)")


def jar_java_required(jar):
    """Java version a jar needs: class-file version of its Main-Class (69 -> Java 25). Bundled libraries
    can be much older, so the first class in the jar is not enough."""
    import struct
    import zipfile
    try:
        with zipfile.ZipFile(jar) as z:
            names = []
            try:
                man = z.read("META-INF/MANIFEST.MF").decode("utf-8", "ignore")
                main = [ln.split(":", 1)[1].strip() for ln in man.splitlines() if ln.startswith("Main-Class:")]
                names = [main[0].replace(".", "/") + ".class"] if main else []
            except KeyError:
                pass
            names = names or [n for n in z.namelist() if n.endswith(".class")]     # else: the newest class file
            best = None
            for n in names:
                head = z.open(n).read(8)
                if head[:4] == b"\xca\xfe\xba\xbe":
                    v = struct.unpack(">H", head[6:8])[0] - 44
                    best = v if best is None else max(best, v)
            return best
    except Exception:
        return None


def freerouting(java_tool=None):
    """Freerouting jar, and whether the Java found can run it. 1.9.0 (Java 17+, needs a display: xvfb-run on a
    headless Linux machine) routes dense small boards further than 2.5.0 (Java 25, stops after ~19 passes)."""
    env = os.environ.get("FREEROUTING_JAR")
    jar = env if env and os.path.isfile(env) else first_existing([
        os.path.join(data_dir("freerouting"), "freerouting-*.jar"),
        "~/.local/share/freerouting/freerouting-*.jar",
        "/opt/freerouting/freerouting-*.jar",
    ])
    ver = None
    if jar:
        m = re.search(r"freerouting-(\d+\.\d+\.\d+)", os.path.basename(jar))
        ver = m.group(1) if m else None
    if not jar:
        return tool("freerouting_jar", None, note=f"expected in {data_dir('freerouting')}/freerouting-<version>.jar",
                    purpose="autorouter (Specctra DSN in, SES out)")
    need = jar_java_required(jar)
    have = None
    if java_tool and java_tool.get("version"):
        mv = re.match(r"(\d+)(?:\.(\d+))?", java_tool["version"])
        if mv:
            have = int(mv.group(1)) if mv.group(1) != "1" else int(mv.group(2) or 0)
    notes = []
    ok = True
    if need and have is not None and have < need:
        ok = False
        notes.append(f"this jar needs Java {need}; found Java {have} (install Java {need}+, or use Freerouting 1.9.0)")
    elif need:
        notes.append(f"needs Java {need}")
    if ver and ver.startswith("1.") and OS == "linux" and not shutil.which("xvfb-run"):
        notes.append("1.x opens a window: install xvfb (xvfb-run) for headless runs")
    if ver and ver.startswith("2."):
        notes.append("2.x stops after ~19 passes when the score stops improving; 1.9.0 routes dense boards further")
    return tool("freerouting_jar", jar, ver, ok=ok, note="; ".join(notes),
                purpose="autorouter (Specctra DSN in, SES out)")


# --------------------------------------------------------------------------- Others
def simple(id_, names, env=None, pats=(), vcmd=("--version",), required=True, purpose="", rx=None, note_missing=""):
    p = find(names, env, pats)
    ver = None
    if p:
        ver = first_line_version([p, *vcmd], rx) if rx else first_line_version([p, *vcmd])
    return tool(id_, p, ver, required=required, purpose=purpose, note="" if p else note_missing)


def chrome():
    if OS == "macos":
        pats = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    elif OS == "windows":
        pats = pf("Google", "Chrome", "Application", "chrome.exe") + pf("Microsoft", "Edge", "Application", "msedge.exe")
    else:
        pats = []
    p = find(["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"], "CHROME", pats)
    ver = first_line_version([p, "--version"]) if p and OS != "windows" else None
    return tool("chrome", p, ver, purpose="headless browser: presentation layout check (a gate) and PDF export",
                note="" if p else "install Chrome or Chromium: the presentation's layout check needs a headless browser")


# --------------------------------------------------------------------------- CAD, panelization, viewers, assets
TOOLKIT_DATA = data_dir("hardware-design-toolkit")
VENV = os.path.join(TOOLKIT_DATA, "venv")
ASSETS_DIR = os.path.join(TOOLKIT_DATA, "assets")
# render assets used by product-render: ambientCG wear sets and one Poly Haven studio HDRI
ASSETS = {
    "Fingerprints009": "textures/Fingerprints009",
    "Smear003": "textures/Smear003",
    "Scratches005": "textures/Scratches005",
    "SurfaceImperfections015": "textures/SurfaceImperfections015",
    "studio_small_09": "hdri/studio_small_09_2k.exr",
}


def cad_python():
    """Python of the build123d venv (Python 3.10–3.13; build123d has no wheels for newer versions)."""
    exe = os.path.join(VENV, "Scripts", "python.exe") if OS == "windows" else os.path.join(VENV, "bin", "python")
    cands = [c for c in (os.environ.get("CAD_PYTHON"), exe) if c and os.path.isfile(c)]
    for c in cands:
        code, out = run([c, "-c", "import sys, build123d; print('B123D', build123d.__version__, sys.version.split()[0])"],
                        timeout=120)
        m = re.search(r"B123D (\S+) (\S+)", out)
        if code == 0 and m:
            return tool("cad_python", c, m.group(1), purpose="enclosure CAD (build123d): STEP, STL, GLB, DFM check",
                        note=f"build123d {m.group(1)} on Python {m.group(2)}")
    return tool("cad_python", None, purpose="enclosure CAD (build123d): STEP, STL, GLB, DFM check",
                note=f"no build123d venv at {VENV} (the installers create it with uv, or python3.12/3.13 -m venv)")


def kikit():
    p = find(["kikit"], None, ["~/.local/bin/kikit", "~/.local/pipx/venvs/kikit/bin/kikit"])
    if p:
        return tool("kikit", p, first_line_version([p, "--version"]), required=False,
                    purpose="PCB panelization for assembly minimum sizes")
    return tool("kikit", None, required=False, purpose="PCB panelization for assembly minimum sizes",
                note="optional: pipx install kikit (or pip install kikit into KiCad's Python)")


def freecad():
    if OS == "macos":
        pats = ["/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd",
                "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD"]
    elif OS == "windows":
        pats = pf("FreeCAD*", "bin", "FreeCADCmd.exe")
    else:
        pats = []
    p = find(["freecadcmd", "FreeCADCmd", "freecad"], "FREECAD", pats)
    return tool("freecad", p, None, required=False, purpose="STEP viewer and CAD hand-off checks (optional)",
                note="" if p else "optional: FreeCAD opens the STEP files for a visual check")


def assets():
    found = {k: os.path.join(ASSETS_DIR, rel) for k, rel in ASSETS.items() if os.path.exists(os.path.join(ASSETS_DIR, rel))}
    t = tool("render_assets", ASSETS_DIR if found else None, f"{len(found)}/{len(ASSETS)}", required=False,
             ok=len(found) == len(ASSETS), purpose="wear textures and studio HDRI for product-render",
             note="" if len(found) == len(ASSETS) else "optional: run the installer with --with-assets")
    return t, found


def python_self():
    v = platform.python_version()
    ok = sys.version_info >= (3, 10)
    return tool("python", sys.executable, v, ok=ok, purpose="standalone toolkit scripts",
                note="" if ok else "Python 3.10 or newer is required")


def heic():
    if OS == "macos":
        return simple("heic_converter", ["sips"], required=False, vcmd=("--help",), rx=r"sips-(\d+)",
                      purpose="HEIC phone photos → PNG/JPEG for reference images")
    t = simple("heic_converter", ["heif-convert", "magick"], required=False, vcmd=("--version",),
               purpose="HEIC phone photos → PNG/JPEG for reference images",
               note_missing="optional: libheif (heif-convert) or ImageMagick 7")
    return t


def collect():
    tools = []
    tools += kicad()
    btools, binfo = blender()
    tools += btools
    jt = java()
    tools.append(jt)
    tools.append(freerouting(jt))
    tools.append(python_self())
    tools.append(cad_python())
    tools.append(kikit())
    tools.append(freecad())
    tools.append(simple("git", ["git"], purpose="versioning of every project",
                        note_missing="install git"))
    tools.append(simple("rsvg_convert", ["rsvg-convert"], "RSVG_CONVERT", vcmd=("--version",),
                        pats=[r"C:\msys64\ucrt64\bin\rsvg-convert.exe", r"C:\msys64\mingw64\bin\rsvg-convert.exe"]
                        if OS == "windows" else [],
                        purpose="SVG drawings → PDF/PNG", note_missing="install librsvg"))
    tools.append(simple("ffmpeg", ["ffmpeg"], vcmd=("-version",), required=False,
                        purpose="turntable videos from frame sequences", note_missing="optional"))
    tools.append(simple("imagemagick", ["magick", "convert"] if OS != "windows" else ["magick"], vcmd=("-version",),
                        required=False, purpose="image contact sheets, crops, format conversion",
                        note_missing="optional"))
    tools.append(heic())
    tools.append(chrome())
    tools.append(simple("gh", ["gh"], vcmd=("--version",), required=False, purpose="GitHub CLI (optional)",
                        note_missing="optional"))
    tools.append(simple("aws", ["aws"], vcmd=("--version",), required=False, rx=r"aws-cli/(\S+)",
                        purpose="cloud GPU rendering (optional)", note_missing="optional, install with --with-cloud"))
    tools.append(simple("session_manager_plugin", ["session-manager-plugin"], required=False,
                        pats=["~/.local/bin/session-manager-plugin",
                              "/usr/local/sessionmanagerplugin/bin/session-manager-plugin"],
                        vcmd=("--version",), purpose="AWS SSM sessions to render machines (optional)",
                        note_missing="optional, install with --with-cloud"))
    t_assets, found = assets()
    tools.append(t_assets)
    binfo = dict(binfo, assets=found)
    return tools, binfo


def table(tools):
    w = max(len(t["id"]) for t in tools)
    vw = max(len(t["version"] or "missing") for t in tools)
    lines = []
    for t in tools:
        mark = "✓" if t["ok"] else ("✗" if t["required"] else "–")
        req = "required" if t["required"] else "optional"
        ver = t["version"] or ("found" if t["found"] else "missing")
        path = t["path"] or ""
        lines.append(f" {mark} {t['id']:<{w}}  {req:<8}  {ver:<{vw}}  {path}")
        if t["note"] and not (t["ok"] and not t["note"]):
            lines.append(f"   {'':<{w}}  {t['note']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Check the Hardware Design Toolkit toolchain and write toolchain.json.")
    ap.add_argument("--project", help="project folder; writes <project>/hw/toolchain.json too")
    ap.add_argument("--out", help="write the JSON to this path instead of the user config folder")
    ap.add_argument("--no-write", action="store_true", help="only print, write no file")
    ap.add_argument("--json", action="store_true", help="print the JSON instead of the table")
    ap.add_argument("--quiet", action="store_true", help="print only the summary line")
    a = ap.parse_args()

    tools, binfo = collect()
    by = {t["id"]: t for t in tools}
    missing = [t["id"] for t in tools if t["required"] and not t["ok"]]
    doc = {
        "schema": SCHEMA,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "os": OS,
        "arch": platform.machine(),
        "ok": not missing,
        "missing_required": missing,
        "paths": {t["id"]: t["path"] for t in tools},
        "cmd": {t["id"]: t["cmd"] for t in tools},
        "versions": {t["id"]: t["version"] for t in tools},
        "blender_gpu": binfo.get("gpu", []),
        "assets": binfo.get("assets", {}),
        "tools": by,
    }

    written = []
    if not a.no_write:
        targets = [a.out] if a.out else [os.path.join(config_dir(), "toolchain.json")]
        proj = a.project or (os.getcwd() if os.path.isdir("hw") else None)
        if proj:
            targets.append(os.path.join(proj, "hw", "toolchain.json"))
        for p in targets:
            os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            written.append(p)

    if a.json:
        print(json.dumps(doc, indent=2, ensure_ascii=False))
    elif not a.quiet:
        print(f"Hardware Design Toolkit · toolchain on {OS} ({platform.machine()})\n")
        print(table(tools))
        print()
    n_ok = sum(1 for t in tools if t["ok"])
    status = "OK" if not missing else "MISSING " + ", ".join(missing)
    where = (" → " + ", ".join(written)) if written else ""
    print(f"doctor: {n_ok}/{len(tools)} tools ok; required: {status}{where}")
    sys.exit(0 if not missing else 1)


if __name__ == "__main__":
    main()
