# Doability checklist

Go through every item. Each item has two parts:

- **Verify:** how to check it.
- **Evidence:** what counts as proof. Anything weaker is `[estimate]` or `[assumption]`.

Mark each item `ok`, `finding F-xxx` or `n/a` in your working notes. Every finding gets an `owner`, an exact `fix` and `auto_fixable` (see SKILL.md). Anything that can only be measured on the built prototype goes to §10, not to the findings.

## 1. Parts

Use one row per active part, and one row per passive or electromechanical part with special needs. Columns:

`ref | MPN (full, orderable) | exists | manufacturer lifecycle | distributor lifecycle | stock + date | lead time | price 1 / 1k | package max dims vs footprint | sources | red flags`

| Item | Verify | Evidence |
|---|---|---|
| The MPN exists and is orderable | Search the full MPN, including the packaging suffix, at two authorized distributors and on the manufacturer's page | Distributor product page and manufacturer page, dated |
| The suffix is the standard one | Read the ordering-information table in the datasheet. Some suffixes are "special order only" | Datasheet section number |
| Lifecycle | The manufacturer's page first ("mass production", "sampling", "NRND", "EOL"), then distributors | Manufacturer URL + date. A distributor label alone is a second source |
| Authorized stock | Use authorized distributors only. Broker-only stock is a red flag | Stock count + date |
| Lead time | Factory lead time from the distributor; shortage notes ("restricted supply", "no backorders") | Distributor page + date |
| Single source | Is there a pin-compatible or footprint-compatible alternative from another manufacturer? | Alternative MPN with its datasheet |
| Price share | Each part's share of the BOM at 1k. Anything above 25% is the main cost lever | BOM roll-up |
| Dimensions | Datasheet **maximum** L×W×H against the footprint, the pocket and the stack-up | Datasheet mechanical drawing |
| Bin / variant | LED color temperature and CRI bins, crystal CL, MLCC voltage and dielectric. Check that the bin code means what the design assumes | Datasheet bin table |
| 3D model | The supplier's STEP is used, or the simplification is documented | File in `hw/pcb/` or `hw/mech/` |
| Purchase plan for long-lead parts | Parts with more than 16 weeks lead time are bought now for EVT/DVT | Roadmap entry |

## 2. Electrical

| Item | Verify | Evidence |
|---|---|---|
| Supply range per IC | For each IC, check that its VCC/VDD range (datasheet, recommended operating conditions) contains the voltage of the net it connects to in the **schematic** | Datasheet table + net name |
| IO voltage domains | Every digital connection between ICs: VOH/VIL compatible, or level shifting present. Watch for 1.8 V parts on 3.0 V buses | Datasheet IO tables |
| Rails forced by parts | List the parts that force a rail (for example a 1.8 V-only flash or mic) and check that the PMIC provides it | Schematic + PMIC datasheet |
| Peak current chain | For the worst simultaneous load (radio TX + LED + speaker + flash program), sum the peak and compare with: cell max discharge (C-rate), protection IC overcurrent threshold, PMIC discharge limit, each regulator's maximum, and the connector or contact rating | Each limit from its datasheet |
| Inrush and brown-out | Bulk capacitance on hot-plug paths. BOR threshold vs the minimum rail during peaks at end-of-life cell voltage and cold temperature | Calculation with the cell's internal resistance |
| Charging | Charge current ≤ the cell's recommended rate (often 0.5–1 C). Charge time follows. Termination voltage matches the cell chemistry (4.2 / 4.35 / 4.4 V) | Cell datasheet + PMIC setting |
| Standby / ship mode | Ship-mode and sleep currents of every part summed. Shelf life from that drain | Datasheet table values |
| ESD and exposed contacts | Charging contacts, touch electrodes and connectors have TVS/ESD protection rated to IEC 61000-4-2 levels | Part datasheet + schematic |
| Reverse and short protection on contacts | Exposed charge pins can short on a metal surface or be reversed | Schematic |
| I2C/SPI | Address conflicts on each I2C bus. Pull-up values vs bus capacitance. Chip-select count | Address table from datasheets |
| Pin budget | MCU GPIOs needed vs available in the **chosen package** (smaller packages have fewer GPIOs). Special pins: ADC, PDM/I2S, NFC, analog | Pinout table |
| Clock | Crystal frequency, CL, ESR and tolerance accepted by the SoC vendor's reference design. The crystal's footprint matches the chosen part | SoC vendor document + crystal datasheet |
| Antenna | Keep-out, ground clearance and feed per the antenna datasheet. Distance to battery, metal, hand and body. Matching network present | Antenna app note |
| Microphone acoustic path | Port location (top vs bottom port) matches the board and enclosure design. Port hole size, gasket, and membrane loss (dB) | Mic datasheet + membrane datasheet |
| Speaker/buzzer loudness | Required SPL (for example a finder protocol's loudness rule) vs a driver of that size | Protocol spec + transducer datasheet |
| Thermal | Dissipation at peak (charging + radio). Skin temperature limits for wearables | Calculation; later a measurement |
| Firmware support | SDK/driver availability for each IC on the chosen RTOS | Repository or vendor SDK page |

## 3. Power and battery

| Item | Verify | Evidence |
|---|---|---|
| Budget method | Bottom-up budget per mode with a duty cycle, then a reality factor of 3–5× until measured | `hw/power/` + calibration against shipped products |
| Measurement plan | Dev-kit measurement with a power profiler **before** the custom cell or mold is ordered | Roadmap gate |
| Capacity sanity | Claimed mAh vs volume × cited Wh/L for that cell type and size class. Small pouch cells have a much lower density than phone cells, because seals and tabs dominate | Vendor datasheets of similar cells |
| Cell geometry | Straight edges, seal border width, tab position, corner radii the vendor can make, and swelling allowance in the pocket (often 5–10% of thickness over life) | Vendor design rules or a quote |
| Usable capacity | Cutoff voltage set by the PMIC or regulator, end-of-life capacity (often 80%), cold temperature | Cell datasheet |
| Runtime claim | Runtime = usable mAh / measured average mA. State the new-cell and end-of-life values | Calculation from measured or tagged inputs |
| Custom cell terms | MOQ, tooling (NRE), sample lead time, UN38.3 test cost and time | Vendor quote or a published policy |
| Off-the-shelf fallback | A catalog cell that fits a prototype enclosure, for EVT | Catalog datasheet |

## 4. PCB

| Item | Verify | Evidence |
|---|---|---|
| Fab capability | Compare the design's minimum trace/space, drill, annular ring, via types (blind/buried/microvia), layer count, thickness, impedance control, finish and **solder mask web** with the chosen fab's published page. Black mask often needs a wider web | Fab capability URL + date |
| Fine pitch | The minimum BGA/CSP pitch the fab accepts, separately for **flex**. Smaller pitch than the fab's published minimum is a finding | Fab assembly capability page |
| Flex | Stiffeners under components, bend radius ≥ the rule for its thickness, no vias in bend zones, coverlay openings | Fab flex rules |
| Assembly | 0201 support, double-sided assembly, X-ray for QFN/BGA/LGA, minimum assembly panel size (small boards must be panelized), fixture costs | Assembler capability page |
| Status | Routed? DRC clean? ERC clean? Schematic parity? A placed, unrouted board is **pre-EVT** | `kicad-cli` reports |
| Testability | Test points for every rail and programming interface. Pogo-pin fixture possible | Board files |
| DFM | Fiducials, tooling holes or a panel frame, component-to-edge distance, tall parts near the edge | Board files + fab DFM report |

## 5. Mechanical

| Item | Verify | Evidence |
|---|---|---|
| Assembly validator | No interpenetration and no broken mesh in the frozen assembly. Each whitelisted contact is a documented simplification | `hw/validation/` report |
| Tolerance stack | For each gap under ~0.3 mm, list the contributing parts with their tolerances. Compute the worst case and RSS; flag a negative worst case | `hw/mech/` tolerance table |
| Wall thickness | Within the material's moldable range (often 0.8–2.5 mm for PC/ABS). Uniform walls, ribs ≤ 60% of the wall | DFM notes; molder's guideline |
| Draft | Draft on every wall in the pull direction (≥ 0.5–1°, more for textures) | CAD check |
| Undercuts | Each undercut (lanyard tunnel, snap, side port) needs a side action or a lifter, which adds tool cost. A curved core is expensive | DFM notes; quote |
| Optical clear parts | Gate location and weld lines away from visible areas; polish grade; stress birefringence | Molder review |
| Sealing / IP | Every opening listed with its seal (membrane, gasket, adhesive). The IP claim is tested, not assumed | Seal datasheets; test plan |
| Touch or light through plastic | Wall thickness over the electrode or LED within the sensor's or the light's limit | Sensor app note; LED window spec |
| Battery pocket | Swelling allowance, no sharp edges, adhesive or foam, no pressure on the cell | Stack-up |
| Contacts and springs | Spring working height within the part's range at worst-case tolerance | Spring datasheet + stack-up |
| Drop | Board retention, connector retention, battery restraint. Plan a 1.0–1.5 m drop test | Test plan |
| Joining | Adhesive, ultrasonic welding or screws: strength, rework, IP | Process notes |
| Serviceability laws | Battery removability or replaceability rules in the target markets, against a glued enclosure | Regulation text + date |

## 6. Compliance and market

| Item | Verify | Evidence |
|---|---|---|
| Radio | Certification per market (FCC, ISED, CE/RED, UKCA, and local agencies such as Anatel, MIC/TELEC, KC, SRRC). Selling, and sometimes even giving away units, before certification is illegal | Agency rules |
| Modular vs discrete radio | A pre-certified module simplifies certification. A chip-down design needs full RF testing | Module grant |
| Bluetooth / Wi-Fi / other SIGs | Qualification and membership fees for the logo and the name | SIG fee page + date |
| Safety | IEC 62368-1 (product); IEC 62133-2 (cell/pack); UL 2054/1642 where relevant | Standard list |
| Battery shipping | UN38.3 test summary for the cell or pack; air shipping limits | Vendor test report |
| Cybersecurity / privacy | Radio cybersecurity rules (for example EN 18031 under the EU RED delegated act), data protection for microphones and cameras | Regulation + date |
| Materials | RoHS, REACH, PFAS restrictions (some membranes are PTFE-based), conflict minerals | Supplier declarations |
| Import | Duties and taxes for prototypes and for production, in the destination country | Customs authority page |

## 7. Cost and schedule

| Item | Verify | Evidence |
|---|---|---|
| Unit cost tiers | 1 / 10 / 100 / 1k / 10k. Recurring cost separate from NRE | `hw/cost/` model with tags |
| Target margin | Unit cost vs the target retail price (hardware usually needs a 3–5× retail multiple over landed cost) | Brief + cost model |
| NRE list | Molds, cell tooling, fixtures, certifications, SIG fees, test labs | Quotes or tagged estimates |
| Critical path | The longest chain of dependent steps, for example: measure current → custom cell → UN38.3 → certification → sale | Roadmap |
| Long-lead parts | Parts with 16–26 week lead times in the critical path | Distributor lead times |

## 8. Claims vs reality

| Item | Verify | Evidence |
|---|---|---|
| Competitor comparison | For each product the design is compared with, check its real battery capacity, runtime, size and features. Compute the implied average current | Teardown, official spec page or FCC internal photos |
| Size claims | The smallest real product with the same feature set | Spec pages |
| "Final" claims | What is frozen: industrial design, schematic, layout, tooling? | Files and their status |

## 9. Build package (the READY TO BUILD gate)

Each item maps to a key in `build_package` in `findings.json`. Set it to true only after you have opened the files and checked them yourself.

| Key | Verify | Evidence |
|---|---|---|
| `routed_board` | Every net is routed on every board; there is no ratsnest left. Planes are poured | `kicad-cli pcb drc` reports 0 unconnected items |
| `drc_erc_zero` | DRC and ERC have 0 violations, with schematic parity, using the **chosen fab's** rules (not the defaults) | The `drc.rpt` / `erc.rpt` files and the DRC rule file |
| `fab_files` | Gerbers, drill, pick-and-place (CPL), BOM in the assembler's format, assembly drawing, stack-up and impedance notes. Panelized if the assembler needs it | Files in `hw/pcb/fab/`; a successful upload preview at the fab if possible |
| `bom_in_stock` | Every line is in stock at the chosen assembler's parts library, or at an authorized distributor, for the build quantity plus attrition. Otherwise it is bought and consigned | Stock snapshot with the date, per line |
| `enclosure_step` | STEP of every enclosure part, with the wall thickness and draft checked, and the material and finish noted | Files in `hw/mech/` |
| `assembly_validated` | Assembly validator: 0 interpenetrations and 0 broken meshes. A tolerance study exists for every gap under ~0.3 mm | `hw/validation/` report; tolerance table |
| `test_plan` | Bring-up order (rails first, then clocks, programming, each peripheral), test points, a firmware smoke test, and the §10 list | `hw/roadmap.md` or `hw/pcb/test-plan.md` |

## 10. Verify on the prototype

These are measurements that only the built prototype can answer. They do not block READY TO BUILD (prototype), but every one must be written in full in `prototype_checks`:

- `id`
- `what`
- `method`
- `instrument`
- `pass_criteria`, a number with its unit

A finding that only a prototype can close points to its check with `prototype_check`.

Typical checks:

| What | Method | Instrument | Pass criteria (example; derive the real numbers from the requirements) |
|---|---|---|---|
| Average current per mode | Run each mode for ≥ 10 min on release firmware | Power profiler (≥ 100 kHz sampling) | ≤ the current that gives the required runtime at end-of-life capacity |
| Peak current and rail droop | Worst-case simultaneous load at the lowest cell voltage | Oscilloscope on the rails + current probe | Rail stays above the BOR threshold + margin |
| Sleep / ship current | Ship mode, then sleep with wake sources on | Power profiler or µA meter | ≤ the budget figure |
| Charging | Full charge from cutoff, at room and minimum temperature | Charger log + thermocouple | Time ≤ target; cell ≤ its maximum temperature; correct termination voltage |
| RF | Conducted output power and sensitivity, or range in the real enclosure on a body | Spectrum analyzer / RF tester, or a range test | ≥ the link budget target |
| Antenna tuning | Return loss in the enclosure, with a hand or body phantom | VNA | S11 ≤ −10 dB across the band |
| Audio | Frequency response and SNR through the enclosure and membrane | Reference mic + sound source in a quiet room | ≥ the requirement |
| Touch / buttons | False-trigger and miss rate on a table, in a pocket, with a wet finger | Scripted test, N trials | ≤ the target error rate |
| Thermal | Skin temperature at peak load and while charging | Thermocouple / IR camera | ≤ the skin contact limit |
| Drop | 1.0–1.5 m onto a hard surface, on several faces | Drop rig | Functional, no internal parts loose |
| Sealing | IP test to the claimed rating | IP test rig or lab | Passes the rating |
| ESD | IEC 61000-4-2 contact and air discharge on exposed parts | ESD gun | No reset or damage at the target level |
| Fit | Assembly of N units; gaps measured | Calipers, feeler gauges | Within the tolerance study |
