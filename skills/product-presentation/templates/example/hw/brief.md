# Product brief: Fixture Tag

- **Version:** 1 · **Date:** 2026-11-08 · **Status:** approved
- **Approved by:** user on 2026-11-08

> Fictional example project. Every part number, price and date in this folder is illustrative and tagged as an estimate or an assumption. Do not use these numbers for a real product.

## 1. Idea

A coin-sized tag that lives on your keys and rings when you ask your phone where they are. It lasts a year on a coin cell, so you never think about charging it.

## 2. Users and use

- **Who:** anyone who loses keys, bags or a bike; secondary: parents tagging a school bag
- **Moment of use:** the two minutes before leaving home, when the keys are not where they should be
- **Carried or mounted:** on a key ring, through a 3 mm ring hole
- **Session pattern:** idle all day; 1–3 "ring" events per week of 10–20 s each
- **Phone or app:** required for setup and ringing; iOS and Android

## 3. Environment

| Factor | Expected | Requirement it implies |
|---|---|---|
| Water and sweat | rain, a spilled drink, pocket humidity | IP54 at least; IP67 target |
| Temperature (use / storage / charging) | −10…45 °C use, −20…60 °C storage, no charging | coin-cell chemistry rated −20…60 °C |
| Drop and impact | dropped with keys onto concrete, 1.5 m, often | no loose parts; battery retained |
| UV and sunlight | car dashboard | UV-stable plastic, no clear parts |
| Skin contact | brief | no sharp edges |
| Other (dust, chemicals, children, pets) | children | coin cell must not be reachable without a tool |

## 4. Body

- **Size target:** 28 × 28 × 6.5 mm · **Size is priority:** 1
- **Weight target:** 7 g including the cell
- **Shape:** rounded square, 6 mm corner radius, ring hole in one corner
- **Interaction:** one press to ring the phone back; one white LED behind a thin window; a sound port for the speaker
- **Look and finish:** matte PC/ABS, three colors (graphite, sand, signal orange)
- **Variants in the first batch:** graphite only

## 5. Function and power

- **Core functions:** ring on request, find the phone, last-seen location via the phone
- **Sensors:** accelerometer for "moved" wake-up
- **Connectivity:** Bluetooth LE to one phone, 10–30 m
- **Offline behavior and storage:** none needed
- **Battery life by mode:**

| Mode | Duration target | Notes |
|---|---|---|
| Active | 20 s ring, 3 per week | speaker at ≥ 80 dB(A) at 10 cm |
| Connected idle | 12 months | advertising every 2 s |
| Standby | 3 years shelf | shipped with a pull tab |
| Shipping / storage | 3 years | cell isolated by the tab |

- **Charging:** none; user-replaceable CR2032
- **Ingress target:** IP67

## 6. Business

- **Markets (first year):** US, EU, UK
- **Quantities and dates:**

| Milestone | Quantity | Target date |
|---|---|---|
| First working prototype | 5 | 2027-02 |
| First batch | 100 | 2027-06 |
| Production 1k | 1,000 | 2027-10 |
| Production 10k | 10,000 | 2028-03 |

- **Unit cost target:** USD 8 at 1k, USD 5 at 10k · **Retail price idea:** USD 29
- **NRE budget:** USD 40,000

## 8. Priorities

1. Size
2. Battery life
3. Unit cost

## 12. Open questions

- [ ] Does the phone OS finder network matter for launch? — needed by specs
