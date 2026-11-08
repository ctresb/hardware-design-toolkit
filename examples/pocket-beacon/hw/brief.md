# Product brief: Pocket Beacon

- **Version:** 1 · **Date:** 2026-11-08 · **Status:** approved
- **Approved by:** toolkit PoC (product owner role) on 2026-11-08

Pocket Beacon is the toolkit's proof-of-concept product. It is fictional. The interview answers were given by the toolkit acting as product owner, and each answer is logged in `hw/decisions.md`.

## 1. Idea

Pocket Beacon is a small item finder that lives on a keyring or inside a bag. When the user cannot find their keys, they tap "Ring" in the phone app, and the beacon plays a loud tone and blinks until it is found.

## 2. Users and use

- **Who:** adults who misplace keys, bags or small cases. Secondary: the same user leaving a bag behind (out-of-range alert in the app).
- **Moment of use:** the user cannot find the keys in the house (the phone rings the beacon), or the user cannot find the phone (a double press on the beacon rings the phone).
- **Carried or mounted:** on a keyring through a slot, or loose in a bag. Pressed against keys, coins and the inside of pockets.
- **Session pattern:** always on. The beacon advertises over BLE all the time. The user rings it 2 to 10 times per month, for 5 s to 30 s each time.
- **Phone or app:** required for ringing and setup. iOS and Android. Standard BLE GATT, with no network membership in v1 (D-003).

## 3. Environment

Applies from `references/use-environments.md`: worn or carried on a keyring, outdoor exposure, contact with hands.

| Factor | Expected | Requirement it implies |
|---|---|---|
| Water and sweat | rain, a drop into a puddle or a sink, sweat from hands | IP67 (1 m, 30 min), sealed lid with O-ring, sealed sound port, no open button (S-09) |
| Temperature (use / storage / charging) | −10 °C to +45 °C use, −20 °C to +60 °C storage (car), no charging | parts rated −40 °C to +85 °C; coin-cell capacity drops at −10 °C, so the alarm must still work at the end-of-life voltage (S-06) |
| Drop and impact | drops on concrete with keys, 1.5 m, many times | 1.5 m drop on concrete, 6 faces + 4 corners; no part may detach; the cell stays in place (S-10) |
| UV and sunlight | dashboard, outdoors | UV-stabilized resin; the translucent variant must not yellow visibly in 1 year (S-13) |
| Skin contact | short contact with hands | materials free of skin sensitizers in the touched surfaces; no nickel on the outside |
| Other (dust, chemicals, children, pets) | pockets with lint, keys scratching it; coin cell is a child hazard | dust-tight (IP6x); scratch-resistant surface texture; **child-resistant battery compartment** (a coin cell is a swallowing hazard: the lid needs a tool or two simultaneous actions, and the package carries a warning) (S-14) |

## 4. Body

- **Size target:** ≤ 32 × 32 × 8.5 mm (should) · hard limit ≤ 32 × 32 × 10.0 mm after the stack-up trade-off (D-007) · **Size is priority:** 2
- **Weight target:** ≤ 10 g with the cell (a CR2032 alone is about 3 g)
- **Shape:** a rounded-square pebble with soft, domed faces and a keyring slot through one corner. Original form, not modeled on any existing product (D-004).
- **Interaction:**
  - one button under a sealed, translucent elastomer membrane on the front; press to silence, double press to ring the phone, long press to pair;
  - one status LED that shines through the same membrane (D-005);
  - a loud tone from a piezo sounder behind a sealed sound port.
- **Look and finish:** fine matte texture on the shell, polished membrane ring. Markings on the lid: model, regulatory marks, cell type and polarity, "+ CR2032".
- **Variants in the first batch:** graphite (opaque dark grey), chalk white (opaque), smoke (translucent dark grey). Same mold, three resins (D-006).

## 5. Function and power

- **Core functions:** BLE advertising and connection to the phone app, ring on command, button input, status light, battery-level reporting to the app.
- **Sensors:** none in v1. An accelerometer for "moved" alerts was considered and left out (D-008).
- **Connectivity:** Bluetooth LE 5.x, 10 m indoor through a bag. The phone connects to the beacon.
- **Offline behavior and storage:** none required. The beacon keeps its pairing keys in internal flash.
- **Battery life by mode:**

| Mode | Duration target | Notes |
|---|---|---|
| Active (ringing) | 12 s per ring, ≤ 10 rings per month | included in the 12-month life |
| Connected idle | not used; the beacon advertises and the phone connects on demand | |
| Standby (advertising) | ≥ 12 months on one CR2032 (must), target 18 months | at 20 °C, with a typical user pattern |
| Shipping / storage | ≥ 2 years shelf with the cell installed, in ship mode, losing ≤ 10 % of capacity | ship mode until the first button press |

- **Charging:** none. The user replaces a standard CR2032 coin cell (D-002).
- **Ingress target:** IP67.

## 6. Business

- **Markets (first year):** US, EU, UK, Brazil.
- **Quantities and dates:**

| Milestone | Quantity | Target date |
|---|---|---|
| First working prototype | 10 | 2027-Q1 |
| First batch (launch batch) | 100 | 2027-Q3 |
| Production 1k | 1,000 | 2028-Q1 |
| Production 10k | 10,000 | 2028-Q3 |

- **Unit cost target:** ≤ USD 12 at 1k (recurring, before NRE and duties) · ≤ USD 8 at 10k · **Retail price idea:** USD 29
- **NRE budget:** USD 40,000 for tooling, certification and prototypes (planning figure, D-009).

## 7. References

| Reference | What the user likes about it | Claim to verify later |
|---|---|---|
| Commercial coin-cell item finders | year-long battery life on a CR2032, loud ring | that a CR2032 can deliver the ring current at the end of its life and at −10 °C |
| Key fobs with replaceable cells | user-replaceable cell, rugged | that a twist lid can be IP67 and child-resistant together |

Reference files: see `hw/refs/README.md`.

## 8. Priorities

1. Battery life (≥ 12 months on a user-replaceable CR2032)
2. Size (pocket and keyring friendly)
3. Unit cost (≤ USD 12 at 1k)

## 9. Requirements seed

| # | Requirement | Target | Limit | Priority | Why | Source |
|---|---|---|---|---|---|---|
| S-01 | Battery life on one CR2032, standby advertising + typical rings | 18 months | ≥ 12 months at 20 °C | must | top priority | user |
| S-02 | Envelope | 32 × 32 × 8.5 mm | ≤ 32 × 32 × 10.0 mm | must (limit) / should (target) | keyring and pocket; D-007 | user + trade-off |
| S-03 | Mass with cell | 9 g | ≤ 10 g | should | keyring comfort | default |
| S-04 | Ring loudness | ≥ 75 dB(A) at 25 cm | ≥ 65 dB(A) at 25 cm on an end-of-life cell (2.4 V under load) | must | findable in a sofa or a bag; above the 60 phon used by finder-network specifications | user + default |
| S-05 | BLE range | 10 m indoor through a bag | ≥ 5 m | must | find in the house | default |
| S-06 | Operating temperature | −10 °C to +45 °C | ring still works at −10 °C on a cell at 50 % | must | outdoors, cars | environment |
| S-07 | Cell | standard CR2032, user-replaceable without tools from the user's side, child-resistant | — | must | no charging; replace in seconds | user |
| S-08 | Status light | visible through the membrane in office light (500 lx) | — | should | pairing and battery feedback | user |
| S-09 | Ingress | IP67 | IPX7 minimum | must | rain, puddles | environment |
| S-10 | Drop | 1.5 m on concrete, 26 drops (6 faces, 12 edges, 8 corners) | no functional loss, cell retained | must | keyrings get dropped | environment |
| S-11 | Unit cost | ≤ USD 12 at 1k | ≤ USD 15 at 1k | should | retail USD 29 | user |
| S-12 | Markets | US, EU, UK, BR | — | must | first year | user |
| S-13 | Translucent variant UV stability | no visible yellowing after 1 year outdoors | — | should | smoke variant | default |
| S-14 | Coin-cell child safety | compartment needs two simultaneous actions or a tool; warning on pack | — | must | swallowing hazard; US and EU coin-battery product rules | environment |
| S-15 | Shelf life in ship mode | ≥ 2 years with ≤ 10 % capacity loss | — | should | retail stock | default |

## 10. Trade-offs explained

| Wish | Physical cost | Options offered | Chosen | Decision |
|---|---|---|---|---|
| Rechargeable vs coin cell | A rechargeable needs contacts or a coil, a charger IC and a pouch cell. That costs about 2 mm of height, a dock, and battery shipping rules | coin cell (chosen); rechargeable pouch + contacts | CR2032, user-replaceable | D-002 |
| 8.5 mm thickness with an off-the-shelf cell holder | The holder, the cell, the board, a sounder and two walls stack to about 9.5–9.9 mm | accept ≤ 10.0 mm with a standard holder (chosen for v1); cell retained by the lid with custom contacts (about 8.5 mm, extra tooling); CR2025 (−0.7 mm, −27 % capacity) | ≤ 10.0 mm in v1; custom contacts kept as a v2 option | D-007 |
| Loud ring on a coin cell | A loud ring draws 6–15 mA for 12 s. A CR2032 sags under this load, more so when cold or near the end of its life | piezo sounder with a charge-pump driver; firmware drops to a lower drive mode when the cell sags | piezo + charge-pump driver, adaptive drive | D-010 |
| White status LED | A white LED needs about 2.7–3.2 V. A CR2032 under load falls below that, so the light would fail first as the cell ages | white LED with a boost; a single low-voltage colour LED | one amber LED (≈ 2.0 V forward voltage) | D-005 |
| Joining a phone-maker finder network | Network programs require their own certification, firmware stacks and contracts | standard BLE only (chosen); join later | standard BLE in v1 | D-003 |

## 11. Defaults taken

| Topic | Default | Why | Decision |
|---|---|---|---|
| BLE version | Bluetooth LE 5.x, 1M PHY, 0 dBm default TX power | enough range; lowest peak current | D-011 |
| Advertising interval | 1.0 s to 2.0 s, adaptive | balances phone discovery and battery | D-011 |
| Firmware update | over the air from the app | no port on the device | D-011 |
| Ring pattern | 12 s per ring, stop on button press | from finder specifications and user habit | D-010 |

## 12. Open questions

- [ ] Final cell retention design (holder vs lid contacts) for v2 — needed by enclosure-engineer v2
- [ ] Child-resistant lid action (two-step twist with a push, or a coin slot) — needed by enclosure-engineer
- [ ] Out-of-range alert in the app (firmware and app scope, not hardware) — needed by product owner before launch
