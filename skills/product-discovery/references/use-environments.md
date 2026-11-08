# Use environments and what they imply

Pick every environment that applies and copy its implications into section 3 of the brief. These are planning targets. `doability-review` and `compliance-planner` confirm them against standards and data.

## Water, sweat and dust

| Environment | Ingress target | Implications |
|---|---|---|
| Desk, indoor | IP4X–IP54 | Openings acceptable; USB-C fine |
| Splash, rain on a bag | IPX4 | Drain paths; gasketed port or a sealed body |
| Worn on the body (sweat) | IP67 recommended | Sweat is saline and acidic (pH ~4.5–7), and it is worse than fresh water for contacts. Mitigations: gold-plated or stainless contacts, ePTFE acoustic membranes, adhesive-sealed seams, no exposed copper. Test with artificial sweat (ISO 3160-2 or EN 1811 for nickel). |
| Shower, rain, hand washing | IP67 | Membranes on every acoustic port, sealed button or capacitive touch, sealed charging contacts |
| Swimming, submersion | IP68 (depth and time defined by the maker) | Pressure on membranes; sealed vents; acoustic performance under water is lost |
| Saltwater, beach | IP68 + corrosion | 316L or titanium contacts, no aluminum without anodizing, rinse instructions |
| Dust, sand, workshop | IP5X–IP6X | Sealed seams; no exposed gaps around buttons |

Every opening in the enclosure is a sealing part, a cost and a test. Fewer openings are better: capacitive touch instead of buttons, molded contacts instead of ports, one acoustic port per mic with a membrane.

## Temperature

| Situation | Typical range | Implications |
|---|---|---|
| Indoor use | 0–40 °C | — |
| Worn on the body | skin ~33 °C; surface limit ~41–43 °C for prolonged contact | Limit charging and radio heat; check skin-contact surface temperature (IEC 62368-1 touch temperature limits) |
| Car interior, summer sun | up to 70–85 °C storage | Li-ion degrades and swells above ~60 °C. Store cells partially charged. Choose resins with a high heat deflection temperature. |
| Cold outdoor | down to −20 °C | Li-ion capacity drops strongly below 0 °C. Never charge below 0 °C (the charger must check it with an NTC). |
| Charging | 0–45 °C (typical cell spec) | The PMIC needs NTC monitoring with JEITA charging profiles |

## Mechanical

| Situation | Typical target | Implications |
|---|---|---|
| Handheld, pocket | 1.0–1.5 m drop on hardwood or concrete, several orientations | Board retention, connector latches or adhesive over connectors, no large unsupported glass. Battery restrained by foam or adhesive. |
| Worn on a cord or clip | 1.5 m drop + snag pull on the cord | Strain relief on the cord hole; the cord tunnel must survive the pull; breakaway for neck cords (safety) |
| Wrist | 1 m drop, frequent knocks | Scratch-resistant top surface; band attachment strength |
| Vehicle, machinery | Vibration (IEC 60068-2-6 / -64) | Locking connectors; no heavy parts on thin flex |

## Light and chemicals

- **UV / sunlight.** Clear polycarbonate yellows under UV without a UV-stabilized grade. Prefer UV-stabilized PC, PMMA or co-polyester for clear parts used outdoors.
- **Skin oils, sunscreen, cosmetics.** These attack some plastics (PC stress cracking, ABS). Check the chemical resistance of the resin. Avoid molded-in stress near the snaps.
- **Cleaning agents (alcohol, disinfectant).** Same check. Laser markings must survive wiping.

## Skin contact

- **Nickel release** must be below the EU REACH limit (0.5 µg/cm²/week, EN 1811) for prolonged skin contact. Nickel-plated magnets and contacts must not touch the skin, or they need a gold or other cover layer that is verified.
- **Preferred skin-contact materials.** 316L stainless, titanium, medical-grade silicone, PC/ABS with known biocompatibility data. Run ISO 10993-5/-10 tests for products with long skin contact if claims are made.
- **Sharp edges.** Radius all edges that the user touches (≥ 0.2–0.3 mm).

## People

| User | Implications |
|---|---|
| Children (< 14 years, or products attractive to children) | Toy safety (EN 71, ASTM F963) may apply. Small-parts rules. Battery compartments secured with a screw. No accessible button cells (Reese's Law in the US). Loudness limits. |
| Elderly | Large, high-contrast controls; simple charging; loud alerts |
| Neck-worn by anyone | Breakaway cord or clasp to avoid strangulation risk |
| Professional or industrial | Gloves (touch must work with gloves or use buttons), hazardous areas (ATEX/IECEx are out of scope for a first product) |

## Privacy and social context

- **Devices that record audio or video.** A visible recording indicator (LED) the user cannot disable is expected, and required in some jurisdictions. Check local consent laws for recording conversations.
- **Trackers.** Unwanted-tracking rules apply (Apple and Google DULT specification): sound output, a minimum loudness, and identifier rotation.
