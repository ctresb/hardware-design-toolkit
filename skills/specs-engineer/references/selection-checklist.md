# Part selection checklist

Run every candidate part through this list. A part that fails a **blocking** item cannot be primary. It can stay as an alternative, with the failure noted.

Record the answers in the BOM row (`key_specs`, `notes`) and in the part's dossier (`hw/parts/<MPN>.md`, written by `electronics-researcher`).

## 1. Existence and identity (blocking)

- [ ] The datasheet was opened and read in this session. A part known only from memory is an `assumption`.
- [ ] The **full orderable MPN** is known, including package, temperature grade, bin and packaging suffix (tape and reel, reel size). Families and truncated numbers are not MPNs.
- [ ] Bins and variants are understood. LED color bins, oscillator tolerance and memory voltage variants change the part. A distributor's "suggested equivalent" can be a different bin, for example a different color temperature.
- [ ] The variant does not change the interface. Some variants change the I2C address or the default mode.

## 2. Lifecycle and supply (blocking)

- [ ] Lifecycle is checked on the **manufacturer's** page first, then at one or two distributors.
- [ ] Not "early sampling", "preview", "engineering sample", NRND, last-time-buy, EOL or obsolete. If it is, the user accepted it as a logged risk and a fallback is chosen.
- [ ] Not special-order only. Datasheet ordering tables sometimes mark a suffix "on special order".
- [ ] Authorized stock exists, or a dated restock exists. Broker-only stock does not count.
- [ ] Lead time is recorded. If it is longer than the time to EVT, buy now or choose another part.
- [ ] A second source exists, or the single source is accepted in `hw/decisions.md`.

## 3. Mechanical fit (blocking)

- [ ] `size_max_mm` comes from the **maximum** dimensions in the package drawing, not the typical ones.
- [ ] Height fits the stack-up zone it sits in, with the enclosure clearance (`enclosure-engineer`).
- [ ] The footprint matches the package. Many crystals, inductors and LEDs come in near-identical sizes, for example 1.6 × 1.2 mm against 1.2 × 1.0 mm.
- [ ] The port or light direction is right: bottom-port against top-port mics, top-view against side-view LEDs, and the antenna keep-out.
- [ ] The part can be assembled by the chosen fab. Check BGA/CSP pitch against the fab's published minimum (it is often stricter on flex), the minimum component size (0201, 01005), double-sided assembly, X-ray, and flex stiffener support.

## 4. Electrical fit (blocking)

- [ ] The supply range contains the rail's min–max, including ripple and the battery's full range when the part sits on VBAT or VSYS.
- [ ] I/O levels match the bus voltage, or a level shifter is in the BOM.
- [ ] The bus address is unique on its bus, for the exact variant.
- [ ] Peak current is known, and the rail and power path can supply it at the same time as the other peaks.
- [ ] The average current in each product mode is known: active, idle, sleep, ship. Typicals are multiplied by 2 until measured.
- [ ] The interfaces exist on the SoC, and the pin budget has room. PDM, I2S, QSPI, ADC and wake pins are limited.
- [ ] Required external parts are in the BOM: crystals, inductors, bulk capacitors, pull-ups, matching network, ESD.
- [ ] Inductors and capacitors meet the datasheet's limits on DCR, saturation current, DC bias and height together. A tiny inductor with the required inductance can have too high a DCR. Check that a real part meets all of them.

## 5. Software

- [ ] An SDK or driver exists for the target RTOS or framework, or the effort to write one is estimated.
- [ ] Reference designs or evaluation kits are available for bring-up.
- [ ] Firmware features that the requirement needs actually exist, for example acoustic activity detection, low-power wake, or the codec.

## 6. Environment and compliance

- [ ] The temperature range covers the use case and the charging case.
- [ ] The part comes as a pre-certified module where certification cost matters, or the radio design plan accepts intentional-radiator testing.
- [ ] RoHS and REACH compliant. PFAS-free if the target market restricts PFAS (some membranes and coatings are not).
- [ ] Skin contact and biocompatibility apply to exposed parts such as contacts and membranes.

## 7. Cost

- [ ] Price at 1, 100 and 1k from a dated distributor page, or tagged `estimate` with its basis.
- [ ] The part's share of the BOM cost is known. Flag any single part above about 25 % of the silicon cost.
- [ ] MOQ and reel size are compatible with the build quantities.

## Quick reject signals

- Only one obscure distributor lists it.
- The datasheet is a one-page brief, with no package drawing.
- The product page has no ordering table.
- The part needs a process the fab does not publish, for example a 0.35 mm pitch on flex.
- The part solves one function with a chip built for ten.
