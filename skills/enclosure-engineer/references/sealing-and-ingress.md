# Sealing and ingress protection

## Principle: every opening is a cost

Each hole, seam and moving part has to be sealed, tested and certified. It also changes the tooling. Before you design a seal, ask whether the opening is needed at all.

| Need | Instead of an opening |
|---|---|
| Button | capacitive touch through the wall; a force sensor behind a thin wall |
| Charging port | molded-in charging contacts (pogo pins or a spring contact inside, flat pads outside); wireless charging if the power budget allows it |
| Speaker grille | a membrane-covered port, or a sealed micro-speaker port with a dust mesh |
| Microphone port | a small port with an acoustic membrane bonded over it |
| Screws | an adhesive seam, ultrasonic welding or snap + gasket |
| Light pipe hole | a thin, translucent wall region (the LED shines through the plastic) |

## Microphone and speaker ports

- Check the port location of the part. Many MEMS microphones are **bottom-port**: the sound hole is on the pad side. They need a hole through the PCB or flex, aligned with the package port and sealed to the enclosure port by a gasket or adhesive ring. Top-port parts take sound from above the package. This decides the whole acoustic path. Verify it in the datasheet before placement.
- An acoustic path has three parts: the enclosure port (diameter and length), the cavity in front of the microphone, and the seal around it. A leak in the seal creates a second path that changes the frequency response and adds noise.
- **Acoustic membranes** (ePTFE vents and similar) block water and dust and pass sound, with an insertion loss of a few dB that depends on the part and the frequency. Use the vendor's acoustic data at your port size. Major vendors: W. L. Gore, Donaldson (Tetratex), Nitto (TEMISH), SAATI (mesh and PFAS-free options).
- **PFAS:** ePTFE is a fluoropolymer. Regulation of PFAS in consumer products is tightening, especially in the EU. Ask each vendor for a PFAS-free alternative (polyester or polyamide meshes, non-fluorinated membranes) and check how it changes the IP rating and the acoustic loss.
- Some membrane vendors sell only directly, not through distributors. Ask early: samples and the minimum order can take weeks.

## Seams

| Method | Seal quality | Rework | Tool and process | Note |
|---|---|---|---|---|
| Pressure-sensitive adhesive (PSA) ring | good, if the bond line is continuous | hard | die-cut adhesive; no tool change | simplest for small products; can be done by hand in prototypes |
| Liquid adhesive or glue bead | good | hard | dispensing; fixture | needs cure time and process control |
| Ultrasonic welding | very good | none (permanent) | energy director in the design; welding horn and fixture | same resin family on both parts; check clear parts for marks |
| Laser welding | very good | none | one part transparent to the laser, the other absorbing | clean, expensive equipment |
| Gasket + snaps or screws | good | yes | gasket groove, compression 15–30% `[estimate: O-ring design guides]` | serviceable; thicker product |

A sealed, glued product cannot be opened to replace a battery. Check the battery rules of each target market with `compliance-planner` before you close the design. For example, EU rules on user-replaceable batteries apply to many portable products from 2027.

## Charging contacts

- Molded-in metal contacts (stainless steel with hard gold plating) give a flat, sealed outer surface. Seal and adhesion around the insert are the weak points, so specify the insert's surface preparation and the plastic grade.
- Spring contacts inside (SMD springs on the PCB) press against the inner side of the inserts. Fit each spring to its working height and check the tolerance stack (see `tolerances.md`). A spring outside its working range gives intermittent charging.
- Magnets for alignment add an attraction force and a keep-out for other parts. Keep components and their solder off the magnet positions.

## IP ratings (IEC 60529)

| Code | Meaning (summary) |
|---|---|
| IP5X | dust protected (limited ingress allowed) |
| IP6X | dust tight |
| IPX4 | splashing water from any direction |
| IPX5 / IPX6 | water jets (6.3 mm nozzle / 12.5 mm nozzle) |
| IPX7 | temporary immersion, 1 m for 30 min |
| IPX8 | continuous immersion beyond IPX7, conditions agreed by the manufacturer |

`[estimate: summary of IEC 60529; read the standard or a test lab's summary before you claim a rating]`

- Sweat resistance is not part of IEC 60529. Sweat is salty and acidic. It attacks contacts, adhesives and coatings. Test it separately, for example with artificial-sweat exposure and salt-fog tests on the charging contacts.
- A rating is earned by a test at a lab, on production-intent parts. A claim in marketing without a test report is a liability.
- Pressure equalization: a sealed product sees pressure changes in flights and with temperature. A vent membrane prevents seal and membrane damage. Acoustic membranes may already do this.

## Checklist for `hw/mech/dfm.md`

- [ ] Every opening listed, with its reason, or replaced by a sealed alternative.
- [ ] Microphone port type (top or bottom) verified in the datasheet. Acoustic path and seal drawn.
- [ ] Membrane part numbers, vendors, sales channel (distributor or direct), PFAS status.
- [ ] Seam method chosen. Rework and battery-replacement rules checked.
- [ ] Charging contacts: material, plating, insert method, spring working height and tolerance.
- [ ] Target IP rating, test lab and test plan. Sweat and salt-fog tests if worn on the body.
