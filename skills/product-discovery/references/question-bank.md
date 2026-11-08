# Question bank

Each question has the reason it matters and a typical default. Ask a question only when the default does not fit or the answer changes the design. Otherwise take the default and log it in `hw/decisions.md`.

## 1. Use

| Question | Why it matters | Typical default |
|---|---|---|
| What does it do, in one sentence? What is the moment the user reaches for it? | Defines the core function. Everything else is optional. | — (always ask if unclear) |
| Who uses it? Adults, children, professionals, elderly? | Children's products have extra safety rules (small parts, battery access, button cells). Elderly users need large controls. | Adults |
| How is it carried or mounted? Cord, clip, wrist, pocket, desk, wall, vehicle? | Sets shape, attachment, drop height and skin contact. | — (ask) |
| How often and how long is it used per day? | Turns battery life into an average current. | — (ask for wearables and battery devices) |
| Does it need a phone or app? Which platforms? | BLE pairing, background limits (iOS), MFi licensing, cloud cost. | BLE to a phone app; iOS and Android |
| Which products do you admire, and for what? | Calibrates taste and expectations. Claims like "X does more in less space" are checked later with data. | — |

## 2. Body

| Question | Why it matters | Typical default |
|---|---|---|
| Size target (L × W × H)? Is size the top priority? | Size bounds battery, board area and antenna. | Ask. Offer 2–3 sizes as previews. |
| Weight target? | Wearables over ~15 g on a cord or ~40 g on a wrist start to feel heavy. | ≤ 15 g for pendants and clips |
| Shape? Any sketch, logo or outline? | An outline becomes the board and enclosure contour. Store it as given. | Rounded rectangle or circle |
| How does the user interact? Button, touch, gesture, voice, LED, sound, haptics? | Each input or output adds a part, power, and often an opening. | One capacitive touch area + one RGB LED |
| Must it reject false triggers (e.g. touching a table)? | Accelerometer taps alone false-trigger. Capacitive touch senses a finger. Combine for robustness. | Capacitive touch, with accelerometer for wake and orientation |
| Does it need to make sound (find-my, alerts)? | Speakers need volume and an acoustic port. Tracking networks set minimum loudness. | No speaker unless find-my or alerts are required |
| Look and finish: colors, transparent variant, matte or gloss, texture? | Transparent parts need optical-grade resin, polished tools, and clean internal layout. Every variant is a separate material and validation. | One opaque color for the first batch |
| Markings: logo, regulatory text, engraving? | Back-side engraving and laser marking hold regulatory text. Plan their space early. | Laser marking on the back |

## 3. Life

| Question | Why it matters | Typical default |
|---|---|---|
| Battery life per mode, in hours: active, connected idle, standby, shipping? | Each mode has a different current. A single number hides the hard one. | Ask for active. Standby 7 days, shipping 6 months. |
| How does it charge? Contacts with a dock, USB-C, wireless? | USB-C needs a port and sealing. Wireless adds a coil and heat and is not faster. Contacts plus magnets seal well. | Magnetic dock with molded contacts |
| Full charge time target? | Small cells charge at about 0.5–1 C. Fast charging shortens cycle life. | ≤ 90 min |
| Connectivity: BLE, Wi-Fi, cellular, UWB, LoRa, none? | Wi-Fi and cellular peaks of 250–400 mA or more do not fit tiny cells. Certification differs per radio. | BLE only |
| What happens without the phone? How much data must be stored offline? | Sets the memory type and size (NOR vs NAND), and the sync protocol. | Store at least 1 day of the main data |
| Which sensors, and what for? | Each sensor costs area, current and firmware. Drop sensors without a purpose. | Only the sensors the core function needs |
| Ingress target: splash (IPX4), sweat, rain, shower, swimming (IP67/IP68)? | Drives openings, membranes, seals, gaskets and test cost. | IP54 for desk devices, IP67 for wearables |
| Does the user replace the battery? | EU Battery Regulation rules on removability apply from 2027 to many portable devices. A glued enclosure may conflict with them. | Not user-replaceable. Flag EU risk. |

## 4. Business

| Question | Why it matters | Typical default |
|---|---|---|
| In which markets will it be sold in the first year? | Decides radio and safety certifications, labels and importer duties. "Worldwide" is not an answer. | — (always ask) |
| How many units, by when? First prototype, first batch, 1k, 10k? | Decides the manufacturing process (3D print vs urethane cast vs aluminum vs steel mold), the MOQ of custom parts, and the cost curve. | 1 prototype → 100 → 1k |
| Unit cost target at 1k and 10k? Retail price idea? | Retail is often 3–5× the landed cost for consumer hardware. | — (ask, or derive from retail) |
| NRE budget for tooling, certification and prototypes? | Molds, custom cells and certification are often USD 20k–100k before the first sale. | — (ask) |
| Who assembles the first units? You at home, or a contract manufacturer? | Home assembly limits the process: adhesive instead of ultrasonic welding, no reflow of fine-pitch BGA. | Contract assembly for PCBA. Final assembly at home for the first ≤ 100 units. |
| Is there a deadline (launch, crowdfunding, event)? | Sets the critical path. Custom cells and certification take months. | — |

## 5. Follow-ups by product type

- **Audio capture.** Number of mics, near or far field, the language and the environment (noise, wind), always-on vs triggered recording, local storage hours, privacy indicator (LED).
- **Wearable on skin.** Skin-contact materials, allergies (nickel), sweat, temperature at skin (≤ 41–43 °C).
- **Outdoor.** UV, temperature range, rain, GPS need, mounting.
- **Desk or home.** Mains or battery, Wi-Fi availability, size freedom.
- **Children or pets.** Small parts, battery compartment screws, chew resistance, loudness limits.
- **Medical-adjacent** (heart rate, temperature, fall detection). Say "wellness, not medical" unless the user plans regulatory clearance. Medical claims change everything.
