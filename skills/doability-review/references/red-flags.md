# Red flags

These are classic project killers. Each one has a symptom, why it fails and what to do instead. When a project shows one of them, it gets a finding of at least `major` severity.

## Power and battery

| Red flag | Why it fails | Do instead |
|---|---|---|
| Wi-Fi on a coin cell or a tiny LiPo | Wi-Fi TX peaks of about 250–400 mA exceed the cell's C-rate and the discharge limit of many small PMICs. Average current kills runtime | Bluetooth LE to a phone; batch uploads through the phone |
| Continuous audio or video streaming from a tiny cell | The radio and the codec run all the time. Shipped wearables average about 10–15 mA while doing this | Record locally, detect voice or activity in hardware, sync in bursts |
| Runtime from a datasheet-only budget | Shipped products draw about 3–5× the bottom-up figure (leakage, firmware, radio retries, peripherals left on) | Apply a reality factor until it is measured; measure on a dev kit first |
| mAh claim above what Wh/L allows | Small pouch cells lose a large share of their volume to seals, tabs and the protection board | Capacity = volume × cited Wh/L for that size class; confirm with a vendor quote |
| Free-form battery that fills the leftover space | Cells are made with straight sides and a few radii. Free-form shapes cost tooling and lose capacity to seals | A rectangle, or a simple shape from the vendor's rules, with swelling allowance |
| Custom cell ordered before current is measured | The cell size is locked before the need is known. MOQ is often about 2k plus tooling | Dev-kit measurement gate before the cell RFQ |
| No end-of-life margin | Capacity drops to about 80%; cold and cutoff voltage cut more | Size for end of life, not for a new cell |

## Parts

| Red flag | Why it fails | Do instead |
|---|---|---|
| A "sampling" or "new product" package with zero authorized stock | It cannot be bought in volume; dates slip | Ask the vendor for samples; keep the mass-production package as plan B |
| NRND / EOL / special-order suffix | No long-term supply; minimum orders apply | Use an active alternative; confirm with the manufacturer |
| Broker-only stock | Counterfeits, no traceability | Use authorized distributors only |
| One part is most of the BOM cost and in restricted supply | Price and schedule depend on one vendor | Smaller density, a second source, or a different architecture (for example less storage, better compression) |
| Nominal dimensions in the stack-up | Max dimensions are larger. Pockets and gaps close | Use datasheet maximums |
| A part that "should exist" at the needed size and value (for example a 4.7 µH inductor at 0402 with low DCR) | The physics of the part does not allow it | Search real catalogs; relax the size or change the regulator topology |
| A truncated part number from a design doc | The orderable MPN, bin or suffix is ambiguous | Use the full MPN from the ordering table |

## PCB and assembly

| Red flag | Why it fails | Do instead |
|---|---|---|
| 0.35 mm pitch BGA/CSP on flex at a fab whose minimum is 0.4 mm | It is outside the published capability; yield and acceptance are not guaranteed | Get written confirmation with a stiffener, choose a larger package, or move the part to the rigid board |
| An unrouted board treated as final | Routing changes placement, layer count and size | Call the design pre-EVT; route before freezing the enclosure |
| Black solder mask with tight pad spacing | Black mask often needs a wider minimum web | Check the fab's mask rules; change the color or the spacing |
| A board smaller than the assembler's minimum, not panelized | It is rejected or charged as a custom fixture | Panelize to the minimum size |
| No test points | Bring-up and production test become impossible | One test point per rail and per programming pin |

## Mechanical and enclosure

| Red flag | Why it fails | Do instead |
|---|---|---|
| An IP67/IP68 claim with open ports | Each opening needs a membrane or a gasket, and a test | Fewer openings, molded contacts, acoustic membranes; test the claim |
| Optical-clear parts with weld lines in view | Visible flow lines; polishing cost | Gate placement review with the molder; design the flow |
| Lanyard tunnel or curved hole molded in one piece | Needs a curved core or side actions, which are expensive and fragile | Split the tunnel at the parting line, or use an insert |
| Zero-clearance nominal stack-up | Tolerances make the worst case collide | Tolerance study; at least about 0.1–0.2 mm where several parts stack |
| A glued, sealed device in a market with battery-removability rules | Rules can require user-replaceable batteries | Check the exemptions (for example for waterproof devices) and get a legal opinion before freezing the tool |
| Hidden collisions in the 3D model, whitelisted | The real parts will not fit | Fix at the source; whitelist only a documented simplification of a supplier's model |

## Compliance and market

| Red flag | Why it fails | Do instead |
|---|---|---|
| "We will sell 100 founder units before certification" | Selling radio devices without certification is illegal in most markets | Put certification in the critical path; budget it |
| Bluetooth logo or name without SIG qualification | A trademark and qualification issue | Budget the SIG fee |
| No UN38.3 report for the cell | The device cannot be shipped by air | Require the report from the cell vendor |
| PFAS-based membranes for markets that are restricting PFAS | Future supply and compliance risk | Qualify a PFAS-free alternative |
| Prototype imports ignored | High import taxes and delays on courier shipments in some countries | Budget the taxes; use a customs broker |

## Process

| Red flag | Why it fails | Do instead |
|---|---|---|
| Fixes that undo each other | Geometry is rebuilt in a different order each time | Fix the pipeline order; freeze a validated golden state |
| "Competitor X does more in a smaller space" without checking X | X often has a bigger battery, worse runtime, or a different feature set | Check the teardown and the implied average current |
| Unknown vendors | No track record; risk of the vendor disappearing | Use established fabs, distributors and manufacturers |
