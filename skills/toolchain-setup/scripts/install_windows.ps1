<#
.SYNOPSIS
  Install the Hardware Design Toolkit toolchain on Windows 10/11 with winget.

.DESCRIPTION
  Idempotent: every step checks first and skips what is already installed.
  Installs KiCad, Blender, Temurin JRE 21, Git, Python 3.12, MSYS2 + librsvg (rsvg-convert),
  the Freerouting jar (checksum verified) and scipy in Blender's bundled Python.

.PARAMETER DryRun
  Print every command, change nothing.
.PARAMETER WithOptional
  Also ffmpeg, ImageMagick, FreeCAD (STEP viewer) and KiKit (panels, into KiCad's Python).
.PARAMETER WithAssets
  Download the render wear textures (ambientCG) and a studio HDRI (Poly Haven).
.PARAMETER WithCloud
  Also AWS CLI v2 and the Session Manager plugin (cloud GPU rendering).
.PARAMETER WithGpu
  Also cupy (CUDA 12) in Blender's Python, for NVIDIA machines.
.PARAMETER SkipBlenderModules
  Do not pip-install scipy into Blender's Python.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File install_windows.ps1 -DryRun
#>
[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$WithOptional,
  [switch]$WithAssets,
  [switch]$WithCloud,
  [switch]$WithGpu,
  [switch]$SkipBlenderModules
)
$ErrorActionPreference = 'Stop'

# Freerouting 1.9.0 (Java 17+) routes dense small boards further than 2.5.0 (Java 25, stops after ~19 passes)
$FreeroutingVersion = if ($env:FREEROUTING_VERSION) { $env:FREEROUTING_VERSION } else { '1.9.0' }
$FreeroutingSha256 = if ($env:FREEROUTING_SHA256) { $env:FREEROUTING_SHA256 } else { '9084a4888937a7f31f857ecc12aa7a37407f51160e4d2892dff9c9bb47ae3102' }
$FreeroutingDir = Join-Path $env:LOCALAPPDATA 'freerouting'
$ToolkitData = Join-Path $env:LOCALAPPDATA 'hardware-design-toolkit'
$CadVenv = Join-Path $ToolkitData 'venv'          # build123d needs Python 3.10-3.13
$AssetsDir = Join-Path $ToolkitData 'assets'

function Say($msg)  { Write-Host "==> $msg" -ForegroundColor White }
function Skip($msg) { Write-Host "    $msg (already installed)" }
function Run([string]$exe, [string[]]$argv) {
  Write-Host ("    > " + $exe + " " + ($argv -join ' '))
  if (-not $DryRun) {
    & $exe @argv
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "$exe failed with exit code $LASTEXITCODE" }
  }
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Error 'winget is required (App Installer from the Microsoft Store). Install it and run this script again.'
  exit 1
}

function WingetInstalled([string]$id) {
  $out = winget list --id $id --exact --accept-source-agreements 2>$null | Out-String
  return $out -match [regex]::Escape($id)
}
function Winget([string]$id, [string]$label) {
  if (WingetInstalled $id) { Skip $label; return }
  Run 'winget' @('install', '--id', $id, '--exact', '--silent', '--accept-package-agreements', '--accept-source-agreements')
}

Say 'KiCad (schematic, PCB, kicad-cli, pcbnew Python)'
Winget 'KiCad.KiCad' 'KiCad'

Say 'Blender (assembly, validation, Cycles renders)'
Winget 'BlenderFoundation.Blender' 'Blender'

Say 'Java 21 (runs Freerouting), Git, Python 3.12'
Winget 'EclipseAdoptium.Temurin.21.JRE' 'Temurin JRE 21'
Winget 'Git.Git' 'Git'
$py = Get-Command python -ErrorAction SilentlyContinue
$pyOk = $false
if ($py) { & python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null; $pyOk = ($LASTEXITCODE -eq 0) }
if ($pyOk) { Skip 'python 3.10+' } else { Winget 'Python.Python.3.12' 'Python 3.12' }

Say 'librsvg (rsvg-convert, SVG -> PDF/PNG) through MSYS2'
$rsvg = @('C:\msys64\ucrt64\bin\rsvg-convert.exe', 'C:\msys64\mingw64\bin\rsvg-convert.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($rsvg -or (Get-Command rsvg-convert -ErrorAction SilentlyContinue)) { Skip 'rsvg-convert' }
else {
  Winget 'MSYS2.MSYS2' 'MSYS2'
  Run 'C:\msys64\usr\bin\bash.exe' @('-lc', 'pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-librsvg')
  Write-Host '    doctor.py finds C:\msys64\ucrt64\bin\rsvg-convert.exe; add that folder to PATH to use it elsewhere.'
}

Say "Freerouting $FreeroutingVersion (autorouter)"
$jar = Join-Path $FreeroutingDir "freerouting-$FreeroutingVersion.jar"
if ((Test-Path $jar) -and ((Get-FileHash $jar -Algorithm SHA256).Hash.ToLower() -eq $FreeroutingSha256)) { Skip $jar }
else {
  $url = "https://github.com/freerouting/freerouting/releases/download/v$FreeroutingVersion/freerouting-$FreeroutingVersion.jar"
  Write-Host "    > download $url -> $jar"
  if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $FreeroutingDir | Out-Null
    $part = "$jar.part"
    Invoke-WebRequest -Uri $url -OutFile $part -UseBasicParsing
    $got = (Get-FileHash $part -Algorithm SHA256).Hash.ToLower()
    if ($got -ne $FreeroutingSha256) { Remove-Item $part; throw "Checksum mismatch for $url (got $got). Nothing installed." }
    Move-Item -Force $part $jar
  } else { Write-Host "    (verify sha256 = $FreeroutingSha256)" }
}

if (-not $SkipBlenderModules) {
  Say "scipy (and cupy with -WithGpu) in Blender's bundled Python"
  $blender = Get-ChildItem -Path "$env:ProgramFiles\Blender Foundation\Blender*\blender.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName | Select-Object -Last 1
  if (-not $blender) {
    Write-Host "    Blender not found yet; run this script again after Blender is installed."
  } elseif ($DryRun) {
    Write-Host "    > <Blender's python.exe> -m ensurepip --upgrade"
    Write-Host "    > <Blender's python.exe> -m pip install --upgrade --no-deps --target <Blender user scripts\modules> scipy"
  } else {
    $expr = "import sys, bpy; print('HDT_PY=' + sys.executable); print('HDT_DIR=' + bpy.utils.user_resource('SCRIPTS', path='modules', create=True))"
    $info = & $blender.FullName -b --factory-startup --python-expr $expr 2>$null | Out-String
    $bpy = ([regex]::Match($info, 'HDT_PY=(.+)')).Groups[1].Value.Trim()
    $mod = ([regex]::Match($info, 'HDT_DIR=(.+)')).Groups[1].Value.Trim()
    if (-not $bpy) { Write-Host '    Could not start Blender headless.' }
    else {
      Run $bpy @('-m', 'ensurepip', '--upgrade')
      # numpy is bundled with Blender; --no-deps keeps the bundled one in use.
      Run $bpy @('-m', 'pip', 'install', '--upgrade', '--no-deps', '--target', $mod, 'scipy')
      if ($WithGpu) {
        if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
          Run $bpy @('-m', 'pip', 'install', '--upgrade', '--target', $mod, 'cupy-cuda12x', 'fastrlock')
        } else { Write-Host '    -WithGpu: no nvidia-smi found, cupy skipped' }
      }
    }
  }
}

Say "CAD venv with build123d (enclosure STEP/STL/GLB) at $CadVenv"
$cadPy = Join-Path $CadVenv 'Scripts\python.exe'
$hasB123 = $false
if (Test-Path $cadPy) { & $cadPy -c 'import build123d' 2>$null; $hasB123 = ($LASTEXITCODE -eq 0) }
if ($hasB123) { Skip 'build123d' }
elseif (Get-Command uv -ErrorAction SilentlyContinue) {
  Run 'uv' @('venv', '-p', '3.12', $CadVenv)
  Run 'uv' @('pip', 'install', '-p', $cadPy, 'build123d')
} else {
  Winget 'Python.Python.3.12' 'Python 3.12'
  Run 'py' @('-3.12', '-m', 'venv', $CadVenv)
  Run $cadPy @('-m', 'pip', 'install', '--upgrade', 'pip', 'build123d')
}

Say 'Headless browser (presentation layout check and PDF)'
$browsers = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
              "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe")
if ($browsers | Where-Object { Test-Path $_ }) { Skip 'Chrome/Edge' } else { Winget 'Google.Chrome' 'Google Chrome' }

if ($WithOptional) {
  Say 'Optional: ffmpeg, ImageMagick, FreeCAD, KiKit'
  Winget 'Gyan.FFmpeg' 'ffmpeg'
  Winget 'ImageMagick.ImageMagick' 'ImageMagick'
  Winget 'FreeCAD.FreeCAD' 'FreeCAD'
  $kpy = Get-ChildItem -Path "$env:ProgramFiles\KiCad\*\bin\python.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName | Select-Object -Last 1
  if ($kpy) { Run $kpy.FullName @('-m', 'pip', 'install', '--user', 'kikit') }
  else { Write-Host "    KiCad's Python not found; install KiCad first, then rerun with -WithOptional." }
}

if ($WithAssets) {
  Say "Render assets into $AssetsDir (ambientCG CC0 textures, Poly Haven CC0 HDRI)"
  $sets = [ordered]@{ 'Fingerprints009' = '2K-PNG'; 'Smear003' = '2K-JPG'; 'Scratches005' = '2K-PNG'; 'SurfaceImperfections015' = '2K-PNG' }
  foreach ($name in $sets.Keys) {
    $dir = Join-Path $AssetsDir "textures\$name"
    if (Test-Path $dir) { Skip $name; continue }
    $zip = "$dir.zip"
    $url = "https://ambientcg.com/get?file=$($name)_$($sets[$name]).zip"
    Write-Host "    > download $url"
    if (-not $DryRun) {
      New-Item -ItemType Directory -Force -Path $dir | Out-Null
      Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
      Expand-Archive -Path $zip -DestinationPath $dir -Force
      Remove-Item $zip
    }
  }
  $hdr = Join-Path $AssetsDir 'hdri\studio_small_09_2k.exr'
  if (Test-Path $hdr) { Skip 'studio_small_09' } else {
    Write-Host '    > download https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/2k/studio_small_09_2k.exr'
    if (-not $DryRun) {
      New-Item -ItemType Directory -Force -Path (Split-Path $hdr) | Out-Null
      Invoke-WebRequest -Uri 'https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/2k/studio_small_09_2k.exr' -OutFile $hdr -UseBasicParsing
    }
  }
}

if ($WithCloud) {
  Say 'Cloud rendering: AWS CLI v2 and Session Manager plugin'
  Winget 'Amazon.AWSCLI' 'AWS CLI'
  Winget 'Amazon.SessionManagerPlugin' 'Session Manager plugin'
}

Say 'Check'
$doctor = Join-Path $PSScriptRoot 'doctor.py'
if ($DryRun) {
  Write-Host "    > python $doctor"
  Write-Host 'install_windows: dry run finished, nothing changed'
} else {
  Write-Host '    Open a new terminal so PATH changes apply, then run:'
  Write-Host "    python `"$doctor`""
  Write-Host 'install_windows: finished'
}
