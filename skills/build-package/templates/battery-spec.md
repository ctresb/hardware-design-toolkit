# Battery · <product> rev <rev>

## Option used in this release

<!-- Keep ONE of the two sections and delete the other. -->

### Catalog cell

| Field | Value | Source |
|---|---|---|
| Cell | <manufacturer> `<MPN>` | <dossier hw/parts/…> |
| Chemistry / nominal V | <e.g. Li-MnO2 3.0 V> | |
| Rated capacity | <mAh at load> | |
| Holder / contacts | <manufacturer> `<MPN>` | |
| Shipping | <UN number, packing instruction, "ships with equipment" or separately> | |

### Custom cell (specification for the cell vendor)

| Field | Value with tolerance |
|---|---|
| Outline | drawing `battery.svg`, straight edges, corner radius <mm> |
| Length × width × thickness | <mm ± mm>, thickness at <state of charge> |
| Sealed border / tab side | <mm> / <side> |
| Capacity | min <mAh> at 0.2 C, 25 °C |
| Chemistry / charge voltage | <LCO 4.2 V / 4.35 V> |
| Max continuous / peak discharge | <mA> / <mA for ms> |
| Protection (PCM) | over-charge <V>, over-discharge <V>, over-current <mA>, PCM size <mm> |
| Tabs / connector | <tab material, length, or flex + connector MPN> |
| Swelling allowance in the product | <mm> over <cycles> |
| Cycle life | ≥ <cycles> to 80 % |
| Certifications | UN 38.3 test summary, IEC 62133-2, MSDS |
| Samples / MOQ / tooling | <qty> / <qty> / <USD> [quote ref] |
