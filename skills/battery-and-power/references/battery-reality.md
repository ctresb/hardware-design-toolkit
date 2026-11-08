# Battery reality

Read this before you choose, size or draw a cell. Most early hardware concepts get the battery wrong in the same few ways. The first draft is a blob that fills the leftover space and is credited with the energy density of a phone battery. A real cell is a straight-edged pouch with a sealed border. It swells over its life, and a vendor has to quote it.

## 1. The five ways a battery concept goes wrong

| Mistake | What it looks like | Correction |
|---|---|---|
| Free-form shape | The cell follows the curves of the enclosure and fills every gap | Use a rectangle, or at most one step. Shape the product around the cell, not the cell around the product |
| Large-cell energy density | Capacity is computed with 600+ Wh/L | Small pouch cells reach about 180–320 Wh/L on the envelope `[estimate]`. Seals and tabs take 25–40 % of a 20 mm cell |
| No seals or tabs | Capacity = outline area × thickness × density | Subtract the tab side (2–4 mm, plus the protection board), the side seals (0.5–1.5 mm folded) and the bottom seal |
| No swelling or tolerance | Cell thickness = pocket height | Thickness = (height − z clearance − tolerance) / (1 + swelling). Swelling is 5–10 % over life `[estimate]`, more when hot |
| Cut before measured | Cell size is frozen before the firmware's current has been measured | Measure first (`references/measurement.md`), then size the cell |

The last row is a process error, not a geometry error. It is the most expensive one: a custom cell and a mold built around an unmeasured current. Real products often draw 3–5× the bottom-up datasheet budget. One worked case dropped from a claimed ~70 mAh to a realistic 55–65 mAh once seals, swelling and tolerance were applied. The 24 h target then needed an average current lower than anyone had measured.

## 2. Cell types

| Type | Envelope energy density `[estimate]` | Good for | Watch out |
|---|---|---|---|
| LiPo pouch, catalog, < 1.5 cm³ | 180–320 Wh/L | prototypes, first 100 units | fixed sizes; seals are a large share |
| LiPo pouch, catalog, 1.5–15 cm³ | 300–430 Wh/L | most wearables and handhelds | swelling allowance |
| High-voltage pouch (4.35–4.45 V) | +8–12 % over 4.2 V | squeezing capacity | the charger must support the voltage; cycle life is shorter |
| Custom stacked pouch | 350–500 Wh/L | final product at ≥ 1–2k units | MOQ, tooling, UN38.3 per design |
| Rechargeable Li-ion coin/button | 250–450 Wh/L | round products, hearables | low peak current; check the pulse rating |
| Primary coin (e.g. CR2032) | high energy, not rechargeable | trackers with a multi-year life | high internal resistance, so a radio peak needs a buffer capacitor |
| Thin-film / solid-state | very low (µAh–few mAh) | sensors, smart cards | cost |

Replace each range with a datasheet or a quote as soon as a candidate cell exists. The battery-fit script keeps the more conservative of two estimates, envelope density and active-stack density inside the seals.

## 3. Pouch anatomy and geometry rules

- **Tab side (top seal):** 2–4 mm, holding the tab weld, the seal and usually the protection board (PCM) folded over. Allow 2–4 mm more if the PCM sits on this side. Tabs are about 2–4 mm wide: aluminum for (+), nickel for (−).
- **Side seals:** 0.5–1.5 mm when folded up. Folded seals add to the thickness at the edges.
- **Bottom seal:** 0.5–1.5 mm.
- **Corners:** radius 0.5–2 mm. Sharp inside corners on a stepped cell need a larger radius.
- **Thickness:** specified as a maximum, with a tolerance of about ±0.1–0.2 mm.
- **Swelling:** keep 5–10 % of the thickness free. Never compress the cell between hard walls.
- **Support:** a flat, smooth backing over the whole face. No sharp edges, screw bosses or components pressing into the pouch. Keep away from heat sources such as regulators, LEDs and charging coils.
- **Fixing:** a double-sided adhesive or a foam pad. Never a screw or a clip through the cell.
- **Label and insulation:** about 0.05–0.1 mm, included in the max thickness.
- **Naming of catalog cells:** usually thickness (×0.1 mm), then width, then length. `401012` means 4.0 × 10 × 12 mm and `302030` means 3.0 × 20 × 30 mm. Vendors swap width and length, so always read the drawing.

## 4. Shapes, in order of preference

1. **Catalog rectangle.** Available now, cheap, samples in days.
2. **Custom rectangle.** Any W × L × T. Cheapest custom option.
3. **Stepped or L-shaped.** Two stacked or adjacent rectangles. Custom tooling, more NRE.
4. **Notched or polygonal with straight edges.** Higher NRE and yield risk.
5. **Curved (round, D-shaped).** Some vendors make them. You lose capacity along every curve, and they cost the most.

If the enclosure is round or organic, draw the largest rectangle that fits, check the capacity with `scripts/battery_fit.py`, and only then consider a step.

## 5. Sizing method

```
delivered mAh = average current (mA) × target runtime (h)
rated mAh     = delivered / (usable fraction × end-of-life fraction)
              e.g. usable 0.85 (cut-off above 3.0 V, temperature, ageing margin) × EOL 0.80 (capacity after the rated cycles)
```

Example: 2.0 mA × 24 h = 48 mAh delivered, so the cell must be rated 48 / (0.85 × 0.80) ≈ 71 mAh.

Do this for the optimistic, baseline, pessimistic and empirical cases (`scripts/power_budget.py`). Plan the product on the pessimistic or empirical case until a measurement exists.

## 6. Off-the-shelf first

- Search catalog cells close to the pocket from established vendors and distributors: the cell maker's catalog, Adafruit or SparkFun for prototype-grade cells, the major distributors.
- A catalog cell 10–20 % smaller than the pocket is usually a better EVT choice than a custom cell. It is available now, has a datasheet, and often already has UN38.3 test reports.
- Use custom cells for DVT and production, once the current is measured and the mechanical stack is stable.

## 7. Custom cell economics `[estimate unless quoted]`

- **MOQ:** about 1,000–2,000+ cells. One US cell distributor publishes 2,000 pieces plus a tooling charge for a custom spec.
- **Tooling/NRE:** low thousands of USD for a pouch die and fixtures. More for stepped shapes.
- **Samples:** 3–6 weeks. Production: 6–10 weeks.
- **Testing:** every new cell design needs its own UN38.3 test report before it can ship by air, and usually IEC 62133-2. Ask the vendor who pays. `compliance-planner` owns this.

## 8. What to send a cell vendor (RFQ)

- an outline drawing with the max dimensions, the tab position and the tab length or connector;
- nominal and charge voltage (4.2 / 4.35 / 4.4 V);
- minimum and typical capacity at 0.2C;
- max continuous and pulse discharge current (from the peak chain check);
- charge current and cycle life to 80 %;
- operating and charging temperature range;
- protection board spec: over-voltage, under-voltage, over-current, its quiescent current, and an NTC if needed;
- documents: datasheet, UN38.3 test summary, IEC 62133-2, MSDS;
- MOQ, tooling cost, sample lead time, and price at 100, 1k and 10k.

Ask two or three established vendors. Treat a vendor that will not provide UN38.3 or IEC 62133 documents as disqualified.
