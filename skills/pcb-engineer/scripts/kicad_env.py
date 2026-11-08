"""Find KiCad, its bundled Python, its libraries, Java and Freerouting on macOS, Linux and Windows.

Every path can be overridden with an environment variable:
  KICAD_CLI, KICAD_PYTHON, KICAD_SYMBOL_DIR, KICAD_FOOTPRINT_DIR, KICAD_3DMODEL_DIR, JAVA, FREEROUTING_JAR, RSVG_CONVERT

Run `python3 kicad_env.py` to print what was found.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

MAC_APP = "/Applications/KiCad/KiCad.app"


def _first(paths):
    for p in paths:
        for hit in sorted(glob.glob(os.path.expanduser(p)), reverse=True):
            if os.path.exists(hit):
                return hit
    return None


def kicad_cli():
    return os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or _first([
        MAC_APP + "/Contents/MacOS/kicad-cli",
        "C:/Program Files/KiCad/*/bin/kicad-cli.exe",
        "/usr/bin/kicad-cli", "/usr/local/bin/kicad-cli"])


def kicad_python():
    """A Python interpreter that can `import pcbnew`."""
    env = os.environ.get("KICAD_PYTHON")
    if env:
        return env
    cand = _first([MAC_APP + "/Contents/Frameworks/Python.framework/Versions/Current/bin/python3",
                   MAC_APP + "/Contents/Frameworks/Python.framework/Versions/*/bin/python3",
                   "C:/Program Files/KiCad/*/bin/python.exe"])
    if cand:
        return cand
    # Linux: the distribution's python3 usually has pcbnew installed system-wide
    for py in ("python3", sys.executable):
        exe = shutil.which(py) or py
        try:
            subprocess.run([exe, "-c", "import pcbnew"], check=True, capture_output=True, timeout=60)
            return exe
        except Exception:
            continue
    return None


def _shared():
    return _first([MAC_APP + "/Contents/SharedSupport", "/usr/share/kicad", "/usr/local/share/kicad",
                   "C:/Program Files/KiCad/*/share/kicad"])


def symbol_dir():
    env = os.environ.get("KICAD_SYMBOL_DIR") or next((os.environ[k] for k in sorted(os.environ, reverse=True)
                                                     if k.startswith("KICAD") and k.endswith("_SYMBOL_DIR")), None)
    return env or (os.path.join(_shared(), "symbols") if _shared() else None)


def footprint_dir():
    env = os.environ.get("KICAD_FOOTPRINT_DIR") or next((os.environ[k] for k in sorted(os.environ, reverse=True)
                                                        if k.startswith("KICAD") and k.endswith("_FOOTPRINT_DIR")), None)
    return env or (os.path.join(_shared(), "footprints") if _shared() else None)


def model_dir():
    env = os.environ.get("KICAD_3DMODEL_DIR") or next((os.environ[k] for k in sorted(os.environ, reverse=True)
                                                      if k.startswith("KICAD") and k.endswith("_3DMODEL_DIR")), None)
    return env or (os.path.join(_shared(), "3dmodels") if _shared() else None)


def version():
    cli = kicad_cli()
    if not cli:
        return None
    try:
        return subprocess.run([cli, "--version"], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return None


def model_var():
    """Name of the 3D model path variable for this KiCad major version, e.g. KICAD10_3DMODEL_DIR."""
    v = version() or "10"
    major = v.split(".")[0]
    return "KICAD%s_3DMODEL_DIR" % major


JAVA_GLOBS = ["/opt/homebrew/opt/openjdk*/bin/java", "/usr/local/opt/openjdk*/bin/java",
              "/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java",
              "/usr/lib/jvm/*/bin/java", "C:/Program Files/Eclipse Adoptium/*/bin/java.exe",
              "C:/Program Files/Java/*/bin/java.exe"]


def java_major(exe):
    """Major Java version of an executable (8, 17, 21, 25...), or None. `java -version` prints to stderr."""
    import re
    try:
        r = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    m = re.search(r'version "(\d+)(?:\.(\d+))?', r.stderr + r.stdout)
    if not m:
        return None
    major = int(m.group(1))
    return int(m.group(2) or 0) if major == 1 else major       # "1.8.0" -> 8


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


def freerouting_version(jar):
    import re
    m = re.search(r"freerouting-(\d+\.\d+\.\d+)", os.path.basename(jar or ""))
    return m.group(1) if m else None


def _javas():
    seen, out = set(), []
    cands = [os.environ.get("JAVA"), shutil.which("java")]
    for p in JAVA_GLOBS:
        cands += sorted(glob.glob(os.path.expanduser(p)), reverse=True)
    for c in cands:
        if c and c not in seen and os.path.exists(c):
            seen.add(c)
            out.append(c)
    return out


def java(min_major=None):
    """A working Java. With min_major (default: what the Freerouting jar needs), the first one that meets it;
    else the first working one. macOS /usr/bin/java is a stub that fails without a JDK and is skipped."""
    if os.environ.get("JAVA"):
        return os.environ["JAVA"]
    need = min_major or jar_java_required(freerouting_jar() or "") or 0
    fallback = None
    for exe in _javas():
        m = java_major(exe)
        if m is None:
            continue
        if m >= need:
            return exe
        fallback = fallback or exe
    return fallback


def freerouting_jar():
    return os.environ.get("FREEROUTING_JAR") or _first([
        "~/.local/share/freerouting/freerouting-*.jar", "~/freerouting/freerouting-*.jar",
        "/opt/freerouting/freerouting-*.jar"])


def rsvg_convert():
    return os.environ.get("RSVG_CONVERT") or shutil.which("rsvg-convert")


def report():
    jar = freerouting_jar()
    j = java()
    return {"kicad_cli": kicad_cli(), "kicad_version": version(), "kicad_python": kicad_python(),
            "symbols": symbol_dir(), "footprints": footprint_dir(), "3dmodels": model_dir(),
            "model_var": model_var(), "java": j, "java_major": java_major(j) if j else None,
            "freerouting_jar": jar, "freerouting_version": freerouting_version(jar),
            "freerouting_needs_java": jar_java_required(jar) if jar else None, "rsvg_convert": rsvg_convert()}


def routing_status(r):
    if not (r["java"] and r["freerouting_jar"]):
        return "routing NOT available (Java/Freerouting)"
    need, have = r["freerouting_needs_java"], r["java_major"]
    if need and have and have < need:
        return "routing NOT available: Freerouting %s needs Java %d, found Java %d" % (r["freerouting_version"], need, have)
    return "routing available (Freerouting %s, Java %s)" % (r["freerouting_version"] or "?", have)


if __name__ == "__main__":
    r = report()
    print(json.dumps(r, indent=1))
    missing = [k for k in ("kicad_cli", "kicad_python", "symbols", "footprints") if not r[k]]
    print("kicad_env: " + ("missing " + ", ".join(missing) if missing else "KiCad found (%s)" % r["kicad_version"])
          + "; " + routing_status(r))
    sys.exit(1 if missing else 0)
