# Design levers that change certification cost

These are design decisions that remove tests, cut cost or shorten the schedule. Make them before the PCB is routed and the enclosure is tooled. All costs are `[estimate]`.

## 1. Pre-certified module or chip-down radio

| | Pre-certified module | Chip-down radio |
|---|---|---|
| Size | Larger: the module footprint plus a keep-out | Smallest: the SoC plus a matching network and antenna |
| Unit cost | Higher, by a few dollars per unit | Lower |
| FCC/ISED | Host SDoC plus "Contains FCC ID". Saves a 15C grant, about USD 4–10k | Full 15C grant and RF tests |
| CE/RED | Smaller radio test scope; the declaration is still yours | Full EN 300 328 set |
| Brazil/Japan/Korea | Smaller scope if the module holds that market's certificate; the end product still needs its own certificate in Brazil | Full scope |
| Antenna freedom | Limited to the module grant's conditions | Any antenna, but you own the tuning and the tests |

Rules of thumb `[estimate]`:

- Under about 5k units a year, or with a team that has never passed radio certification, the module usually wins.
- Very small wearables often go chip-down because the module does not fit. If you do, budget for a VNA antenna tuning inside the real enclosure, on a body phantom.
- A body-worn product can need its own RF-exposure evaluation even when it uses a modular-approved radio.

## 2. TX power cap

BLE at 0–4 dBm usually stays under the low-power exposure thresholds of the FCC, ISED, EN 62479 and Brazil. Above that, a body-worn device can need SAR tests, which cost several thousand USD per market. To use this lever:

- set the cap in firmware;
- write it in the test report;
- check the link budget, because range drops by roughly half for every 6 dB.

## 3. Openings and sealing

Every port is a test, a risk and a cost. Charging contacts, microphone ports, buttons and seams each need:

- an ESD test (IEC 61000-4-2, discharges to every accessible metal part and seam);
- an ingress path in the IP test.

To reduce them:

- molded contacts instead of a receptacle;
- an acoustic membrane on each port instead of an open hole;
- a sealed seam with adhesive or welding.

Check the EU Battery Regulation article 11 before you choose welding or glue (section 4).

## 4. Battery removability (EU from 2027-02-18)

A non-removable battery needs an exception argument, or the product needs a battery door or screws. Decide before tooling. Retooling a mold costs far more than a legal opinion. A battery door with a gasket can keep IP67, but it adds height, cost and a sealing test.

## 5. Mains adapter

Do not put a mains adapter in the box. Ship only a USB cable. This avoids adapter certification in several markets (for example Brazil, Japan PSE and China CCC) and makes shipping simpler.

## 6. Lithium cells: standard or custom

- **Catalogue cells** often already have UN 38.3 and IEC 62133-2 reports.
- **Custom cells** need new reports: 4–8 weeks and up to several thousand USD, unless the vendor includes them in the NRE.
- **Prototypes:** use a catalogue cell that already has a UN 38.3 report.
- **Custom-cell contract:** require the UN 38.3 report, the test summary and the MSDS as deliverables.

## 7. Cybersecurity from day one

EU RED 3.3, the EU CRA and the UK PSTI share these core requirements:

- no default passwords;
- signed, authenticated firmware updates;
- encrypted personal data at rest and in transit;
- a vulnerability-disclosure contact;
- a declared support period;
- an SBOM.

Building them into the firmware architecture costs little. Retrofitting them before launch costs a lot.

## 8. Recording, camera and location products

- Drive the recording indicator from hardware, so firmware cannot record with it off.
- State the data flows in the privacy policy.
- Encrypt the stored data.
- Trackers: implement the anti-stalking specifications (for example the IETF DULT draft) from the first firmware.

## 9. Pre-scan before formal tests

Book a pre-compliance session (1–2 days in a chamber, about USD 1–4k) on EVT or early DVT units. A failure in the formal tests costs a board revision, new samples and a retest slot, often 4–8 weeks.
