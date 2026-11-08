# Layout rules for small connected devices

The datasheet and reference design of each part win over anything here. These rules are the checklist to apply when the datasheet is silent. Lines marked `[practice]` are common engineering practice, not a cited figure.

## Stack-up

- **4 layers is the default for a small radio board:**
  - outer layers: signals and parts;
  - In1: a solid GND under the RF and the SoC;
  - In2: power, or GND plus routing.
  `[practice]`
- **Thin boards (0.6–0.8 mm)** save height but flex more. Keep heavy parts, connectors and springs near the support points of the enclosure.
- **Copper on thin 4-layer boards** is usually 1 oz outside and 0.5 oz inside. Take the dielectric thicknesses from the fab's stack-up table. You need them to compute the 50 Ω width.

## Antenna and RF

- **Follow the antenna maker's layout drawing exactly:** ground clearance area, feed position, and distance to the board edge. A chip antenna's clearance area has no copper on any layer. In the spec, it is a keepout with `"copper": true, "parts": false`.
- **The antenna goes at an edge or corner of the board, away from:**
  - the battery and any metal (springs, steel stiffeners, shields, magnets);
  - the user's hand and body where possible.
  The enclosure counts too: no metal paint, plating or metal inserts over the antenna. `[practice]`
- **Keep the matching network** (π or T, with DNP positions) between the SoC pin and the antenna feed. Tune it on the final enclosure with a VNA. Values from the reference design are a starting point only.
- **RF trace:** 50 Ω coplanar waveguide with ground, short, no stubs, ground vias along both sides every ~λ/20. `[practice]`

## SoC support circuits

- **Crystal:** within 2–3 mm of the XC pins, with load caps next to it and a ground guard around it. No signals under it on the next layer. Calculate the load caps from the crystal's CL and the stray capacitance.
- **DC/DC:** the inductor at the switch pin, then output cap → ground → input cap in the smallest loop. Use the inductor the reference design names, or one with the same inductance, saturation current, DCR and **height**. Low-profile inductors often miss the DCR target.
- **Decoupling:** one cap per supply pin at the pin. The smallest value is closest. A via to the plane goes directly at the cap pad.
- **Exposed pad:** connect it to GND with a via array, either tented or filled for via-in-pad.

## Power entry and exposed contacts

- **ESD protection** goes at every exposed contact: charging pads, pogo pins, USB, buttons with metal caps, touch electrodes if the controller asks for it. Place it at the contact, before the trace goes anywhere else.
- **Reverse-polarity and overvoltage protection** belong on dock contacts. A magnetic dock can touch the wrong way, and so can a coin.
- **Charge current:** the charger's programming resistor sets it. Keep it at or below the cell's rated charge current (often 0.5–1 C for small cells). Confirm with `battery-and-power`.

## Sound ports and microphones

- **Bottom-port MEMS mics** listen through a hole in the board under the part. The datasheet gives the diameter (typically 0.5–1 mm, unplated or as the datasheet specifies). Seal the path from that hole to the enclosure port with a gasket or adhesive ring, and keep the ground ring of the land pattern intact.
- **Top-port mics** need the port in the enclosure directly above them, with a gasket between the mic and the shell.
- **Waterproofing:** the acoustic membrane in the enclosure port. The seal, membrane and adhesive openings all stack tolerances. Check them with `enclosure-engineer`.
- **Keep away from mics:** switching regulators, the speaker or buzzer, vibration motors and the antenna feed. `[practice]`

## Touch, LEDs and sensors under the shell

- **Capacitive touch electrodes:** solid copper under the touch area, no ground pour directly under it on the next layer (use hatched ground or none, per the controller's app note), and the sensor IC close to the electrode. A flex bonded to the shell gives the most even sensitivity.
- **LEDs under windows or light pipes:** fix their position from the enclosure. Use the datasheet's maximum height for the gap to the shell, and check the LED's viewing angle against the window size.
- **Accelerometers:** away from board edges and connectors (stress), and not under a spring contact.

## Test, programming and manufacturing

- **Test points** for SWD/JTAG, reset, every rail, battery and charge status go on the side a pogo fixture can reach. Space them ≥ 1.27 mm and use ≥ 0.8–1.0 mm pads. `[practice]`
- **Fiducials:** 3 on the panel rails for small boards, or 2–3 on the board itself when it is large enough.
- **Text on the board:** board name, revision and date code, in copper or on a fab layer if silkscreen does not fit.

## Flex boards

- **Shape:** no sharp inner corners. Use `union` with a fillet ≥ 0.5 mm. Add a tear-stop (a copper or coverlay ring) at slit ends. `[practice]`
- **Bends:** no vias, pads or parts in bend areas. Traces in bend areas run perpendicular to the bend, staggered between layers, and hatched ground only. Bend radius ≥ the fab's minimum (JLCPCB: 10× thickness).
- **Stiffeners:** one under every group of parts. Steel under fine-pitch parts and connectors, PI or FR4 elsewhere. Remember that steel is slightly magnetic and blocks RF.
- **Connector tails:** stiffener to the connector's specified thickness, and a mating force path that does not peel the flex.

## Mechanical interface

- **Every enclosure feature over the board is a keepout on its side:** magnets, battery, ribs, screw bosses, springs and ports.
- **Use the parts' maximum heights** for the gap to the enclosure.
- **The 3D model needs real vendor models** of connectors, springs, batteries and shields. A box gives the validator a wrong answer.
- **Outline tolerance:** the fab cuts to ± 0.1–0.2 mm. Design the board-to-wall gap at ≥ 0.3 mm. `[estimate: fab tolerance plus enclosure tolerance]`
