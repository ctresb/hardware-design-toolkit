# Free-space map and fitting flex circuits

## The free-space map (`scripts/free_space.py`)

The idea is to pour a liquid into the cavity and let it fill every reachable gap.

1. **Rasterize fixed surfaces.** Each triangle of every fixed part is sampled at half the voxel size and marked in a boolean grid. Sampling runs in chunks, so large faces leave no gaps and memory stays bounded.
2. **Dilate once.** Diagonal voxel gaps otherwise let the liquid leak through a closed wall.
3. **Flood fill from a seed in the cavity.** With scipy or cupy this is connected-component labelling; without them, a vectorized breadth-first search.
   - If no seed is given, the largest enclosed region is used.
   - If the cavity air reaches the border of the grid, the enclosure has an opening: a **leak**.
4. **Distance transform over the cavity air.** Each voxel stores its distance to the nearest solid. Outside the cavity counts as solid, so parts are pushed back inside the shell. The gradient points away from collisions.
5. **Exact distance near surfaces.** Within 3 voxels of a surface, the BVH of the fixed triangles gives the exact distance. The sign comes from the grid gradient, not from mesh normals: imported vendor models often have inverted normals. Without a grid (numpy-only backend), the sign comes from the air mask far from surfaces and from ray parity near them.

Voxel size and backends:

| Backend | Practical grid | Note |
|---|---|---|
| numpy | ≤ ~8 M voxels | fine for checks and coarse fits |
| scipy | ≤ ~60 M voxels | about 0.1 mm over a 40 × 30 × 15 mm enclosure |
| cupy (GPU) | ~300 M voxels | about 0.03 mm over a 30 × 30 × 9 mm device; free GPU memory between steps, use float32 distances, fall back to CPU if out of memory |

Use the finest grid that matters: the voxel should be at most about half the smallest clearance you need to verify.

### Leak findings

A leak is real until proven otherwise. Typical causes:

- a seam modelled with a gap instead of face contact or an adhesive bead;
- a port without its membrane;
- a cord tunnel that opens into the cavity;
- a missing lid.

Close the cause in the model, or decide in `hw/decisions.md` that the cavity is intentionally open (for example a vented product).

## Rigid fit (`fit_rigid`)

For each movable object:

1. Sample points on its surfaces.
2. Query distance and escape direction.
3. Move the object along the escape direction of its worst point, by the missing clearance × 1.1, clamped to `max_step`.
4. Repeat until the worst point has the clearance (within 0.004 mm) or the iterations run out.

Use `lock=(0, 0, 1)` when the part may only move along one axis, for example a battery in a stack.

The fit moves parts out of fixed parts. Two movable parts do not see each other, so fit them one at a time and add the first to the fixed set before you fit the second. Always finish with the validator.

## Flex circuits that drape over components

A flex circuit is not rigid. It bends between components and stays flat under stiffened areas. A method that worked in practice:

1. **Keep flat coordinates.** When the flex is formed (bent around the shell), store each vertex's position in the flat layout as mesh attributes, for example `flat_x` and `flat_y`. Store each component's flat position and half-size as custom properties.
2. **Make a 2D displacement field over the flat layout.** Use a grid with cells of about 0.1 mm. Each colliding flex vertex and each colliding component writes a 3D push vector into its flat cell. A component writes one vector over its whole footprint plus a margin.
3. **Smooth the field to model bending stiffness.** Take the maximum envelope over a radius of about 0.45 mm, then apply a Gaussian blur. The flex bends gradually instead of kinking.
4. **Keep rigid areas rigid.**
   - Under each component, the flex moves with the component, with a short transition of about 0.3 mm.
   - Components that share a stiffener move with one shared vector: the largest in the group.
   - Group stiffeners only by real overlap, and cap the group size. A chained, oversized stiffener drags unrelated parts with it.
5. **Hold the mated end fixed.** The area under a mated connector gets zero displacement. If the optimizer can move it, it will pull the plug out of its socket.
6. **Iterate about 8 times, or until the worst intrusion is under 0.004 mm.** Then validate.

If the field cannot resolve a collision, the flex layout or the shell needs a pocket. That is a design finding.

## Pockets for components that protrude

When a component on a board or flex must sit inside a fixed wall, cut a local pocket:

- footprint plus a margin;
- the **full** component height plus clearance (about 0.03 mm);
- a pocket through the whole wall only if the wall stays at least the minimum moldable thickness. Otherwise, move the component.

A pocket that covers only the top of the part leaves the sides colliding.
