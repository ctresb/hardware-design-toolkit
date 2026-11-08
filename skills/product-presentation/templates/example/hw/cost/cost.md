# Cost model — Fixture Tag (fictional example)

Prices as of 2026-11-08. Ranges are low–high. Every line keeps its evidence tag in `model.json`.

## Cost per unit by order size

| Item (per unit, USD) | 1 | 10 | 100 | 1,000 | 10,000 |
|---|---:|---:|---:|---:|---:|
| electronics (BOM) | $29.7 | $9.37 | $5.84 | $4.22 | $3.50 |
| PCBA (variable) | $1.79 | $1.79 | $0.64 | $0.37 | $0.20 |
| bare boards | $5.00–12.0 | $2.00–6.00 | $0.50–1.50 | $0.08–0.20 | $0.05–0.12 |
| enclosure | $40.0–150 | $25.0–70.0 | $12.0–30.0 | $0.90–1.80 | $0.45–0.90 |
| packaging | $2.00–6.00 | $2.00–6.00 | $2.00–6.00 | $0.40–1.20 | $0.25–0.60 |
| yield loss | $4.13–35.2 | $2.11–16.4 | $0.71–4.26 | $0.14–0.41 | $0.05–0.13 |
| assembly & test | — | — | $2.00–5.00 | $0.80–2.00 | $0.40–1.00 |
| per-order fees, spread over the order | $123–183 | $12.3–18.3 | $1.08 | $0.23 | $0.02 |
| **Recurring (FOB, before duties)** | **$206–418** | **$54.6–128** | **$24.8–54.3** | **$7.14–10.4** | **$4.92–6.47** |
| One-time costs (NRE) in this plan | $50.0–300 | $450–3.8k | $16.8k–28.3k | $32.5k–70.3k | $43.5k–96.3k |
| NRE spread per unit | $50.0–300 | $45.0–380 | $168–283 | $32.5–70.3 | $4.35–9.63 |
| **Total per unit (recurring + NRE)** | **$256–718** | **$99.6–508** | **$192–337** | **$39.6–80.7** | **$9.27–16.1** |
| Landed in US (formal entry) | $276–896 | $120–598 | $193–358 | $39.9–85.2 | $9.57–19.3 |
| Landed in EU (formal import) | $321–896 | $135–598 | $198–358 | $41.4–85.2 | $10.6–19.3 |
| Share of recurring cost resting on verified figures | 27% | 11% | 4% | 7% | 4% |

How to read it: recurring cost is what one more unit costs at that order size. NRE is paid once (tooling, fixtures, certifications) and is shown spread over the order. Landed cost applies the destination's duty and tax multiplier to the recurring cost and adds freight.

## One-time costs (NRE)

| Item | Group | From order size | Cost | Evidence |
|---|---|---:|---:|---|
| Test and programming fixture (DIY) | fixtures | 1 | $50.0–300 | estimate |
| Urethane casting molds | tooling | 10 | $400–3.5k | estimate |
| Bluetooth SIG qualification (Contributing Adopter small, first product) | certification | 100 | $11.5k | verified |
| FCC Part 15 (15.247 + 15B) via TCB, chip-down | certification | 100 | $4k–10k | estimate |
| IP67 test (IEC 60529) | certification | 100 | $800–3k | estimate |
| Test and programming fixture (EMS-built) | fixtures | 1,000 | $2k–10k | estimate |
| Rapid aluminum tools (shell + lid) | tooling | 1,000 | $4k–9k | estimate |
| Retail box artwork and cutting die | packaging | 1,000 | $200–800 | estimate |
| CE/RED incl. EN 18031 | certification | 1,000 | $9k–22k | estimate |
| UKCA radio declaration support | certification | 1,000 | $1k–4k | estimate |
| Hardened steel tools, 2 cavities | tooling | 10,000 | $15k–35k | estimate |

## What drives the cost

**1 unit:** Enclosure set (shell, twist lid, O-ring, LED window) $40.0–150 (30%, estimate); PCBA setup, stencil, loading, fixtures, handling (per order) $83.5 (27%, verified); Bare PCB prototype lot (5–10 panels) (per order) $40.0–100 (22%, estimate); C1 EXAMPLE-CAP-220U-POLY $11.6 (4%, estimate)

**1,000 units:** Final assembly, programming, functional test $0.80–2.00 (16%, estimate); Enclosure set (shell, twist lid, O-ring, LED window) $0.90–1.80 (15%, estimate); U1 EXAMPLE-BLE-SOC-WLCSP $1.19 (14%, estimate); Retail packaging with pull tab $0.40–1.20 (9%, estimate)

**10,000 units:** U1 EXAMPLE-BLE-SOC-WLCSP $1.03 (18%, estimate); Final assembly, programming, functional test $0.40–1.00 (12%, estimate); Enclosure set (shell, twist lid, O-ring, LED window) $0.45–0.90 (12%, estimate); LS1 EXAMPLE-BUZZ-0903-SMT $0.59 (10%, estimate)

