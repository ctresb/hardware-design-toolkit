# Reading a datasheet

Read the PDF, not a summary page. Give the page or section for every value you copy.

| What | Where it usually is | Why it matters |
|---|---|---|
| Revision and date | cover page or last page (revision history) | an older revision can have different limits or package options |
| Ordering information / part-number decoder | last pages, "Ordering information", "Package option addendum" | full orderable MPN, packaging suffix, temperature grade, special-order suffixes |
| Package drawing | "Mechanical data", "Package outline", appendix | **maximum** L, W, H for stack-up and pockets; pad pitch; exposed pad |
| Recommended land pattern / stencil | after the package drawing, or an app note | footprint; paste reduction for exposed pads and fine pitch |
| Absolute maximum ratings | early electrical section | limits never to exceed, not operating points |
| Recommended operating conditions | right after absolute max | supply range that must contain the rail; temperature range |
| Electrical characteristics | main tables | typical and max current per mode (active, idle, sleep, shutdown) |
| Peak or inrush current | power section, radio TX tables, charger section | battery, PMIC and regulator sizing |
| Interface section | "Serial interface", "I²C", "SPI" | I²C address and how to set it, bus speed, logic levels |
| Pin table | "Pin configuration and functions" | pin compatibility; which pins need pull-ups or decoupling |
| Typical application circuit | near the end | required passives and their values, layout notes |
| Bin and grade tables | LEDs, crystals, sensors, batteries | color temperature, flux, CRI, load capacitance, tolerance, grade |
| Errata | separate document on the product page | silicon bugs that change the firmware or circuit |
| Moisture sensitivity level (MSL) and reflow profile | handling section | assembly limits, especially for MEMS mics and LEDs |

## Per category

- **Wireless SoCs and modules:**
  - TX and RX current at the TX power you will use;
  - sleep current with RAM retention;
  - antenna matching network;
  - crystal requirements (frequency, load capacitance, ESR);
  - which packages are in mass production;
  - existing certifications (modular approval IDs).
- **PMICs and chargers:**
  - charge current range;
  - termination voltage options (4.20 / 4.35 / 4.40 V);
  - the maximum discharge or system current;
  - ship and hibernate currents;
  - fuel-gauge support.
- **Memory:**
  - supply range (1.8 V vs 3 V parts share package names);
  - page and block size, ECC, endurance;
  - standby and deep power-down current;
  - erase and program peak current.
- **MEMS microphones:**
  - port location (top or bottom);
  - acoustic overload point and SNR;
  - current per mode;
  - the sealing and gasket guidance in the app note.
- **LEDs:**
  - maximum height;
  - forward voltage per color at your current;
  - bin codes for color temperature, flux and CRI;
  - whether the white has a CRI spec at all.
- **Connectors:**
  - the full suffix (stacking height, plating, reel);
  - mated height;
  - mating cycles;
  - retention force;
  - whether the drawing is for the receptacle, the plug or the pair.
- **Springs and contacts:**
  - free height, working height, minimum height or hard stop;
  - force at working height;
  - current rating;
  - plating.
- **Passives:**
  - the real package height (0402 MLCCs at high capacitance can be taller);
  - DC-bias derating for MLCCs;
  - DCR and saturation current for inductors at the height you need.

## Rules

- Copy the number, its unit, the condition (temperature, voltage, mode) and the page.
- If the datasheet gives only a typical value, say "typ only, no max".
- If the product page and the datasheet disagree, the datasheet wins. Note the conflict.
