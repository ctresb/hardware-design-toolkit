# Enclosure materials

The properties below are qualitative guidance. For a decision, read the datasheet of the exact grade and confirm availability with the molder. Resin suppliers publish datasheets per grade, for example Covestro, SABIC, Trinseo, Mitsubishi Chemical, Evonik and Lubrizol.

## Rigid plastics

| Material | Strengths | Weaknesses | Typical use |
|---|---|---|---|
| **PC** (polycarbonate) | tough, impact resistant, clear grades, good for thin walls, takes laser marking | scratches easily (often hard-coated), stress cracking with some chemicals (sunscreen, alcohol), must be dried before molding | clear or tinted housings, lenses, wearables |
| **PC/ABS** | tough, good surface finish, easier to mold than PC, paintable | opaque | phone accessories, opaque housings |
| **ABS** | cheap, easy to mold, good finish | lower impact and heat resistance, poor UV resistance | consumer housings, prototypes |
| **PMMA** (acrylic) | best clarity, scratch resistant, UV stable | brittle on impact, notch sensitive | windows, light guides, display covers |
| **PA** (nylon), glass-filled grades | strong, wear resistant | absorbs moisture (dimensions change), glass fibers show on the surface | internal frames, clips |
| **PBT** | dimensionally stable, chemical resistant | opaque | connectors, internal parts |
| **Copolyester** (e.g. Tritan-type grades) | clear, chemical resistant, tough | lower heat resistance than PC | clear consumer parts in contact with cosmetics |

## Clear parts

- Choose an **optical grade** of PC or PMMA. Standard grades have a yellow tint and haze.
- A clear part shows every internal feature and every defect: weld lines, sink, splay, flow lines, dust. See `dfm-injection-molding.md`.
- A hard coat makes clear PC usable in daily wear. Without it, a clear wearable looks scratched within weeks. A real product has some light scratches anyway. Show them in renders, and do not promise "scratch-proof".
- Render clear plastic with a plastic IOR (PC ~1.58, PMMA ~1.49), a slight volume absorption and surface wear. It must not look like glass. The `product-render` skill owns the shaders.

## Soft materials

| Material | Use | Note |
|---|---|---|
| **TPU** | overmolds, straps, bumpers | good abrasion resistance; check skin-contact grade |
| **TPE / TPV** | soft-touch overmolds, seals | bond to the substrate depends on the pair; ask the resin supplier |
| **LSR** (liquid silicone rubber) | gaskets, straps, button membranes | best skin feel and temperature range; its own tooling process |
| **Foam** (PU, PE, PORON-type) | battery cushion, gap fill, acoustic seal | compression set matters; check the datasheet |

## Metals

| Material | Use | Note |
|---|---|---|
| **Aluminum 6061 / 6063, CNC or extruded** | premium housings, heat spreading | anodize for color and wear; blocks radio, so plan antenna windows |
| **Stainless steel 304 / 316L** | charging contacts, inserts, small housings | 316L for skin contact and sweat; plate contacts with hard gold over nickel |
| **Zinc die-cast** | heavy, decorative parts | plate or paint; nickel allergy risk if nickel-plated and in skin contact |
| **NdFeB magnets** | alignment and attachment | nickel-plated as standard; corrode if the plating is damaged; lose strength at high temperature (grade-dependent) |

## Skin contact and wearables

- Ask suppliers for skin-contact and biocompatibility statements, for example ISO 10993 cytotoxicity, sensitization and irritation tests, for the material in its final finish.
- **Nickel release:** in the EU, items in prolonged skin contact are restricted under REACH Annex XVII, and EN 1811 is the test. Avoid exposed nickel plating on parts that touch the skin.
- **Sweat** is salty and slightly acidic. It attacks contacts, adhesives and some coatings. Plan artificial-sweat and salt-fog tests for charging contacts and seams.
- **Chemicals that crack PC under stress:** sunscreen, insect repellent, alcohol wipes and some hand creams. A wearable PC part needs a chemical-resistance check, or a copolyester or PC-blend grade.

## Radio and sensors

- Metal walls block radio. Plastic is transparent to it, but some fillers, metallic paints and vacuum-metallized finishes are not. Keep the antenna keep-out free of metal and conductive coatings.
- Capacitive touch works through plastic up to a few millimetres, depending on the sensor. A thinner wall over the electrode improves sensitivity. Keep the wall over the electrode uniform.
- LEDs shining through a translucent wall need a minimum wall area and thickness for even light. A thin window of 0.4–0.5 mm over the LED is common. Clear parts need a diffuser texture or an internal light guide to avoid a hot spot.

## Color and finish options per variant

When the product has color variants (for example clear, black and white), list the variants in `hw/mech/dfm.md`. For each one, give the resin and color masterbatch, the finish (SPI grade or texture), the coating and the marking method (laser, pad print, in-mold). Each variant can change the molding (clear parts are stricter), the cost and the lead time.
