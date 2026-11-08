# Rendering on a cloud GPU

A final 4K product shot takes about 1–2 minutes on a data-center GPU. On a laptop it can take an hour, while
the session is running on the same machine and its memory runs out. For finals, and for heavy scene building
(cloth and cord simulation, large boolean operations), use a cloud GPU or a strong workstation. Light work,
such as editing scripts, looking at images or converting files, stays local.

This guide uses AWS EC2. The same steps work on any provider with NVIDIA GPUs.

## Instance choice (Cycles + OptiX)

| Instance | GPUs | Indicative speed (relative) | Notes |
|---|---|---|---|
| g6.xlarge | 1× L4 24 GB | 1× | cheap, often available; good for previews |
| g6.12xlarge | 4× L4 | ~3.5× | good default for batches (one process per GPU) |
| g6e.xlarge / 12xlarge | 1× / 4× L40S 48 GB | ~2× / ~7× | big scenes, faster; capacity varies by zone |
| g7e (RTX PRO 6000 Blackwell) | 1–8 | ~2.5× per GPU vs L4 | the fastest in this list for Cycles; check region availability |
| p5 / p6 (H100/B200) | 8 | poor value | compute GPUs without RT cores; Cycles gains little |

Prices change, so check the provider's current on-demand price. As a reference point, one test measured a
3024×4032 frame at 512 spp in 4 min 45 s on one L40S. The same frame was estimated at ~50 min on a laptop.

## Setup pattern

1. **Machine.**
   - Launch from an image with NVIDIA drivers, for example a "Deep Learning Base" AMI.
   - Give it a role (instance profile) that grants only Systems Manager (SSM) and one S3 bucket or prefix.
     Do not open SSH: drive it by SSM.
   - Add a shutdown timer and terminate-on-shutdown in the user data, so a forgotten machine dies by itself:
     ```sh
     shutdown -h +180
     ```
     and set `InstanceInitiatedShutdownBehavior=terminate`.
2. **Blender.**
   - Download the official Linux tarball once, and cache it in your bucket. Some download mirrors serve an
     HTML page instead of the tarball to cloud IP ranges, so check the file type.
   - Install Python packages into Blender's own Python, if a script needs them:
     ```sh
     ./blender-*/5.*/python/bin/python3.* -m pip install scipy
     ```
3. **Files.**
   - Pack the `.blend`, so textures and HDRIs travel with it:
     ```sh
     blender -b scene.blend --python-expr "import bpy; bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath='scene_packed.blend', copy=True)"
     ```
   - Upload the packed `.blend` and the scripts to S3. Use presigned URLs if the local machine has no AWS
     CLI.
4. **Render through SSM Run Command:**
   ```sh
   cd /opt/r && aws s3 cp s3://<bucket>/<job>/ . --recursive
   ./blender/blender -b scene_packed.blend --python studio.py -- --target Product --recipe dark-studio \
       --format 4k-vertical --preset final --validator-json assembly.json --out out/hero.png
   aws s3 cp out/ s3://<bucket>/<job>/out/ --recursive
   ```
   - **Multi-GPU:** run one Blender process per GPU, each on its own shot or frame range, with
     `CUDA_VISIBLE_DEVICES=i`. This scales better than one process on all GPUs for several shots.
   - **Watch for results** by listing the output prefix (S3 `ListObjectsV2`). Download each image as it
     appears, and show it to the user at once. Polling a single presigned URL can miss the result.
5. **Terminate** the instance when the batch is done. Do not leave it idle "in case". If another job may come
   soon, keep the shutdown timer short and extend it only when needed.

## Tested commands (Linux + NVIDIA, Blender 5.2 LTS, OptiX)

These commands ran as written on Ubuntu with 4× NVIDIA L4 (g6.12xlarge), using the official Linux Blender
tarball. `studio.py` picks OptiX, then CUDA, HIP, Metal and oneAPI, in that order. It falls back to the CPU
and logs the device it used. The HIP warning on NVIDIA machines is harmless.

```sh
# 0. once per machine: check that Blender, the GPU and every script work (≈20 s, thumbnails only)
BL=/opt/r/blender-5.2.3-linux-x64/blender          # wherever the tarball was unpacked
$BL -b --factory-startup --python scripts/selftest.py -- /tmp/hdt_selftest --units mm --samples 16
#    expect: "SELFTEST ok" and "STUDIO rendered … OPTIX ×N" lines

# 1. materials on the frozen, validated assembly
$BL -b base.blend --python scripts/materials.py -- \
    --assign "Enclosure*=plastic_black:wear=0.4" "Window*=plastic_clear:wear=0.6" \
    --wear-textures /opt/r/textures --save look.blend

# 2. solder (only if the shot shows boards; normally done before validation, in the build)
$BL -b look.blend --python scripts/solder.py -- --pads pads.json --board main="Main board" --save look.blend

# 3. final render, gated by the validator report
$BL -b look.blend --python scripts/studio.py -- --target "Product" --recipe dark-studio --view hero \
    --format 4k-vertical --preset final --emit "LED*=1,0.86,0.70:60" \
    --validator-json assembly.json --out out/hero_dark.png

# one process per GPU for a batch of shots
VIEWS=(hero front three-quarter side)
for i in 0 1 2 3; do
  CUDA_VISIBLE_DEVICES=$i $BL -b look.blend --python scripts/studio.py -- --target Product \
      --view "${VIEWS[$i]}" --format 4k-vertical --preset final --validator-json assembly.json \
      --out "out/shot_$i.png" > "log_$i.txt" 2>&1 &
done; wait
```

Measured on 4× L4 at 480×640, 48 spp: about 2.3 s per recipe, including scene setup. A 4K final at 512 spp
takes a few minutes per GPU, depending on how much clear plastic the scene has.

## Speed levers, in order of value

1. Previews at low resolution and 64 spp before any final. Most rounds are spent on decisions, not pixels.
2. Adaptive sampling plus the denoiser (on by default in `studio.py`).
3. One process per GPU across shots.
4. A faster GPU class (L40S, then Blackwell RTX PRO).
5. Lower bounces only if the product has no clear parts.

## Cycles or LuxCore?

An A/B test on a studio product scene, at the same samples on 4× L4, gave:

| Engine | Time per view | Notes |
|---|---|---|
| Cycles | about 6 s | |
| LuxCore, warm kernel cache | 12–20 s | |
| LuxCore, cold cache | about 690 s | the NVIDIA OpenCL kernel recompiles for every new scene or resolution, about 170 s per GPU in series |

Image quality was nearly the same. LuxCore also lacks some Principled features: thin film (lens
anti-reflective coatings) and coat IOR.

**Decision: use Cycles.** Consider LuxCore only for shots that depend on real caustics or light tracing, such
as light through a lens onto a surface, and budget the kernel compile time for them.
