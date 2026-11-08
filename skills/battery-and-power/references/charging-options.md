# Charging options

Choose the charging method early. It sets the number of openings, the dock, the sealing and part of the certification. Every opening is a sealing, cost and certification problem, so prefer methods that add none.

## Trade-offs

| Method | Openings in the enclosure | Speed | Space | Sealing | Notes |
|---|---|---|---|---|---|
| **Contacts + magnets** (flat pads on the device, pogo pins on the dock) | none: the contacts are molded in | full rate (0.5–1C) | 2 pads + 2–4 magnets | excellent: the contacts are inserts sealed by the molding | Needs a dock. Plate the contacts with hard gold over nickel (sweat corrodes). Add reverse-polarity and ESD protection, and limit the current if the pads can short against metal |
| **USB-C receptacle** | 1 port | full rate | receptacle about 3 mm tall (mid-mount less), plus the PCB edge | needs a waterproof receptacle or a gasket | Universal, no dock. The port dominates small products and is the first thing to corrode |
| **Qi / inductive** | none | slower; small coils are inefficient and get warm `[estimate]` | coil + ferrite, about 0.3–0.8 mm thick over a large area | excellent | The heat sits next to the battery. Small coils couple poorly. The WPC logo needs certification |
| **NFC wireless charging (WLC)** | none | low power, a few hundred mW | small antenna | excellent | Fits very small devices. Check that the phone or charger side supports it |
| **Another ecosystem's charger** (e.g. a smartwatch puck) | none | — | — | — | **Not available.** These chargers are proprietary. Licensing programs cover accessories *for* that ecosystem, not third-party devices charging *from* its chargers. Do not plan on it |
| **Replaceable primary cell** | battery door | none | holder | the door needs a gasket | Only for multi-year, low-current products |

## Charge rules

- **Charge current:** 0.5C is typical for small pouch cells and 1C is the usual maximum. Read the cell datasheet. Charge time ≈ capacity / current × 1.2 + the constant-voltage tail; about 1.5–2.5 h at 0.5C.
- **Charge window:** usually 0–45 °C. Use the charger's NTC input and a JEITA profile if the product is charged warm (on the body, in the sun).
- **Termination:** a constant-current/constant-voltage charger with termination at 5–10 % of the CC current. Never trickle-charge Li-ion indefinitely.
- **Charge voltage:** 4.2 V cells need 4.2 V; high-voltage cells need a charger set to 4.35 or 4.4 V. A wrong setting either wastes capacity or damages the cell.
- **Power path:** the system runs from the input while charging, so a flat battery still boots.
- **Ship mode:** the PMIC or protection board disconnects the battery for storage and shipping. Its current, in nA to low µA, sets the shelf life. Shelf life (h) = remaining capacity (mAh) / (ship-mode current + cell self-discharge).
- **Fuel gauge:** use voltage plus a model (coulomb counting or a model-based gauge in the PMIC) for anything the user sees as a percentage. Voltage alone is unreliable during radio peaks.

## Peak current chain

A radio, speaker, haptic motor, LED or flash program pulse draws its peak through every element in the path. Check the worst simultaneous peak against each limit:

1. the cell's max continuous and pulse discharge (C-rate × capacity);
2. the protection board's over-current trip, including its delay;
3. the PMIC or charger's system-load limit, which can be lower than the battery could deliver;
4. each regulator's max output current, from `max_ma` in `hw/power/rails.json`;
5. the voltage drop: cell internal resistance (high in small, cold or old cells) × peak current must not pull VSYS below the brown-out threshold of any IC.

A radio with peaks of hundreds of mA (for example Wi-Fi transmission) can exceed a small PMIC's system-load limit on its own. That is a reason to choose a lower-power radio, not to add a bigger capacitor and hope.
