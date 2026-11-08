# Drawing standards for quotation drawings

Read this when you prepare a drawing that a supplier will quote from, or when the user asks for a drawing that looks professional.

## 1. What a quotation drawing must contain

A molder, a PCBA house or a contract manufacturer quotes from the drawing plus the 3D file. The drawing package for a request for quotation (RFQ) contains:

1. **An exploded view with numbered balloons.** Every part that the supplier buys, makes or assembles has a number.
2. **A bill of materials (parts list)** with item, description, material or part number, specification and quantity per product.
3. **Overall dimensions** of the assembled product, in at least two orthographic views.
4. **A title block** with product name, revision, date, scale, units and sheet number.
5. **General notes:** general tolerance class, surface finish (SPI grade for molded parts), color or texture reference, marking method, and "dimensions in mm".
6. **Critical dimensions with tolerances** for each part that is to be tooled. Examples are wall thickness, snap-fit and press-fit features, mating features and window openings. These belong on part drawings, not on the assembly sheet. Generate them from the CAD model of the part.

Items 1–5 come from this skill. Item 6 needs the part's CAD model and a tolerance study (`enclosure-engineer`). State in the RFQ that the 3D file (STEP) is the master geometry and that the drawing controls only the dimensions marked on it.

## 2. Line types (ISO 128-2)

| Use | Line | Weight in this toolkit (virtual units ≈ mm on A3) |
|---|---|---|
| Visible outlines and silhouettes | continuous wide | 0.42 |
| Visible edges inside the outline (creases) | continuous narrow | 0.22 |
| Small electronic parts on a PCB | continuous narrow | 0.14 |
| Hidden edges (orthographic views only, optional) | dashed narrow | 0.16 |
| Dimension and extension lines, leaders | continuous narrow | 0.18–0.25 |

ISO 128 uses a 2:1 ratio between wide and narrow lines. The weights above keep that ratio for contour against detail.

## 3. Title block (ISO 7200)

ISO 7200 requires these fields: legal owner, title, drawing number, revision, date of issue, sheet number, document type, creator and approver. The toolkit's block shows:

- product and subtitle (document type);
- overall size;
- scale, with sheet size;
- units;
- revision;
- date;
- sheet.

Add the owner, approver and drawing number in `title.subtitle` or as extra text when a supplier needs them.

## 4. Scale (ISO 5455)

- **Enlargement:** 2:1, 5:1, 10:1, 20:1, 50:1.
- **Reduction:** 1:2, 1:5, 1:10, 1:20, 1:50, 1:100.
- With `standard_scale: true`, the scripts pick the largest standard scale that fits.

Small products often fill an A4 or Letter sheet better than A3, at the same scale.

## 5. Projection (ISO 128-30, ISO 5456-2)

- **First-angle projection** is standard in Europe and most of Asia. The top view goes below the front view, and the left view goes on the right.
- **Third-angle projection** is standard in the US. The top view goes above the front view, and the right view goes on the right.
- Always state the method in the title block. The scripts write it as text.

## 6. General tolerances (ISO 2768)

ISO 2768-1 sets linear tolerance classes f (fine), m (medium), c (coarse) and v (very coarse). For a 6–30 mm dimension:

| Class | Tolerance |
|---|---|
| f | ±0.1 mm |
| m | ±0.2 mm |
| c | ±0.5 mm |

Small molded consumer parts are usually quoted at ISO 2768-m. Critical features are toleranced individually. For plastics, the molder may cite ISO 20457 or DIN 16742 instead of ISO 2768. Ask the molder which standard they quote against.

## 7. Balloons and parts list (ISO 6433, ISO 7573)

- One balloon per item, a circle with the item number.
- The leader ends in a dot on a **visible** surface of the part. If no point of the part is visible in the view, the script draws the leader dashed and the dot hollow, and prints a warning. Fix this by increasing the explode offset or changing the view.
- Balloons sit in vertical columns outside the drawing. Leaders must not cross, and a leader must not pass over another item's dot.
- The parts list numbers items in assembly order: outer shell first, then the inside, then the closure. Quantity is per product.
- An envelope dimension is for **one physical unit**:
  - for a part used several times, the size of one ("each");
  - for an assembly bought as one item, such as a PCBA, the size of the whole assembly;
  - never the sum of all instances.

## 8. Sheet sizes

| Sheet | Size |
|---|---|
| A4 | 297 × 210 mm |
| A3 | 420 × 297 mm |
| A2 | 594 × 420 mm |
| Letter | 279.4 × 215.9 mm |
| Tabloid | 431.8 × 279.4 mm |

The scripts lay every sheet out in a 420-unit-wide virtual space, so line weights and fonts scale with the paper. On A4 the text is about 0.7× the A3 size; check that it stays legible (≥ 1.8 mm cap height for notes).
