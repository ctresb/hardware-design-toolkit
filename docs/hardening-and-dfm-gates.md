# Hardware Design Toolkit — Physics, Electrical, CAD & Security Hardening Gates

> **Target Revision Audited:** `ctresb/hardware-design-toolkit` @ `a7f2aa860bbf696152cead9d5dd34c566836f752` (`v0.1.0`)
> **Scope:** 17 skills, single-owner `hw/` workspace contract, Python verification oracles, KiCad 10 PCB synthesis, `build123d` B-rep CAD, and Blender `BVHTree` collision gates.

---

## 1. Executive Summary of the 12 Source-Code Findings & Fixes

| # | Category | File & Line (`a7f2aa860bbf`) | Trigger & Failure Mode | Risk (`L × I`) | Hardened Fix Implemented |
|---|---|---|---|---|---|
| **1** | **Supply-Chain Security** | `skills/toolchain-setup/scripts/install_linux.sh:238-279`, `install_macos.sh:115-183` | `awscliv2.zip` and `session-manager-plugin.deb`/`.rpm` are fetched over HTTP/HTTPS and executed under `sudo` without SHA-256 or GPG verification; 4 texture ZIPs (`ambientcg.com`) + HDRI (`dl.polyhaven.org`) extract without checksums; `pip install --upgrade` runs without `--require-hashes`. | `6 × 9 = 54` | Added `verify_sha256()` gate in `install_linux.sh` and documented pinned SHA-256 / `--require-hashes` supply-chain policy. |
| **2** | **Local File Disclosure (Headless Chrome)** | `skills/product-presentation/scripts/layout_check.py:171` | `measure_chrome()` opens `file://.../index.html` with `--allow-file-access-from-files` after injecting `LINT_JS`. Untrusted strings from scraped distributor/datasheet pages can read arbitrary local host files via `fetch('file:///...')`. | `5 × 8 = 40` | Replaced `file://` + `--allow-file-access-from-files` with `serve_directory_loopback(d)` (`http://127.0.0.1:<ephemeral>/`) and `--disable-background-networking`. |
| **3** | **Battery Physics ($R_{\text{int}}$ Pulse Droop)** | `skills/battery-and-power/scripts/power_budget.py:28-36, 135-147` | Battery is modeled as a constant ideal voltage source (`vbat = nominal_v`), ignoring internal resistance $R_{\text{int}}(T, \text{SOC})$ and Peukert/rate droop. A CR2032 coin cell ($R_{\text{int}} \approx 15\text{–}100\,\Omega$) under a $30\,\text{mA}$ BLE TX + piezo pulse drops $\Delta V = I_{\text{peak}} R_{\text{int}} = 0.45\text{–}1.2\,\text{V}$, tripping UVLO at 90% SOC. | `8 × 9 = 72` | Added `verify_battery_pulse_droop()` and `internal_resistance_ohm` / `r_int_ohm` support in `power_budget.py` to enforce $V_{\text{ocv}} - I_{\text{peak}} R_{\text{int}} \ge V_{\text{cutoff}} + 0.10\,\text{V}$. |
| **4** | **Electrical Cross-Domain `vio`, Dual-Rail Peak & LDO Dropout** | `check_rails.py:77-99`, `bom_check.py:156-188`, `bom_merge.py:135-182, 321-338` | (a) Shared `I2C`/`SPI`/`UART` buses never check `vio` / `io_range_v` compatibility across connected ICs (allowing a $3.3\,\text{V}$ sensor and $1.8\,\text{V}$ SoC on `I2C0` without level shifting); (b) `bom_check.py:165` attributes 100% of `peak_current_ma` only to `names[0]`; (c) `bom_merge.py:325` validates only `names[0]`; (d) LDO dropout headroom is unchecked. | `8 × 9 = 72` | Added `check_bus_vio_compatibility()`, `check_ldo_dropout()`, `vio_rail` checking in `check_rails.py`, `io_range_v` validation in `bom_merge.py`, and multi-rail peak attribution in `bom_check.py`. |
| **5** | **3D BVH Collision Blindspots** | `skills/enclosure-engineer/scripts/validate_assembly.py:262, 281` | (a) `if L < 2 * tol: continue` skips all triangle edges $< 0.04\,\text{mm}$ on high-density filleted/threaded meshes; (b) `validate()` only tests edge-face intersections, reporting `0 interpenetrations` when a smaller closed solid is 100% contained inside another closed solid without crossing a surface. | `6 × 8 = 48` | Added midpoint parity check for short edges (`0 < L < 2 * tol`) and representative vertex `_parity_inside` check when closed AABBs overlap with `n == 0` edge hits. |
| **6** | **PCB Legalizer Geometry & Rotation** | `skills/pcb-engineer/scripts/pcbgen.py:125, 209` | (a) `poly_gap()` tests only vertex `0` (`outl.inside(B, *A[0])`), missing concave courtyard containment when vertex `0` lies outside `B`; (b) `npads(p) > 2` locks rotation for all 3+ pad parts (`SOT-23`, crystals); (c) `problems()` ignores component Z-height vs. enclosure ceiling. | `7 × 7 = 49` | Updated `poly_gap()` to test all vertices (`any(outl.inside(B, *pt) for pt in A)`), unlocked $90^\circ$ rotation unless `lock_rotation` is set, and added `max_z_mm` / `height_mm` checks. |
| **7** | **RF Impedance & IC Thermal Gates** | `skills/pcb-engineer/scripts/release_check.py:127-129` | `release_check.py` only checks if the netclass name string appears in `stackup.md`, with no closed-form $50\,\Omega$ CPWG/microstrip verification and no $\Delta T = P_{\text{diss}} R_{\theta\text{JA}}$ thermal check. | `6 × 8 = 48` | Added `cpwg_impedance_ohm(w_mm, s_mm, h_mm, er)` (complete elliptic integral via AGM) and `check_thermal_rise()` to `release_check.py`. |
| **8** | **Multi-Runtime Agent Portability** | `skills/*/SKILL.md` (30 occurrences) | Commands invoke `python3 "${CLAUDE_SKILL_DIR}/scripts/..."`. In Codex, Antigravity, Cursor, or OpenCode where `CLAUDE_SKILL_DIR` is unset, this expands to `/scripts/...` and fails. | `7 × 6 = 42` | Documented portable `${CLAUDE_SKILL_DIR:-skills/<skill-name>}` resolution in `AGENTS.md` and `docs/hardening-and-dfm-gates.md`. |
| **9** | **Python 3.9–3.11 `SyntaxError` Crash** | `skills/compliance-planner/scripts/compliance_matrix.py:167` | Uses PEP 701 nested double quotes inside a double-quoted f-string (`f"> {rules["disclaimer"]} ..."`), raising `SyntaxError: f-string: unmatched '['` on Python 3.9–3.11 despite documented Python 3.9+/3.10–3.13 support. | `9 × 8 = 72` | Replaced inner quotes with single quotes (`rules['disclaimer']`); verified on Python 3.9–3.13. |
| **10** | **Fresh-Clone `selftest.py` Crash** | `skills/build-package/scripts/selftest.py:31` | `build_fixture()` writes `hw / "drawings/blueprint.pdf"` without creating `hw / "drawings"`, raising `FileNotFoundError` on every clean Git clone because Git does not track empty directories. | `10 × 7 = 70` | Added `(hw / "drawings").mkdir(parents=True, exist_ok=True)` in `selftest.py`. |
| **11** | **CSV Formula Injection & Duplicate `#define`s** | `release_lib.py:55-60`, `assemble_release.py:244-250` | (a) `write_csv()` writes distributor/BOM cells without neutralizing leading `=`, `+`, `-`, `@` formula triggers (CWE-1236); (b) `pin_map()` emits duplicate `#define PIN_<NET>` macros when multiple MCU pins share a net. | `5 × 7 = 35` | Added `_sanitize_csv_cell()` in `release_lib.py` and disambiguated multi-pin nets as `PIN_<NET>_<PAD>` in `assemble_release.py`. |
| **12** | **KEEL 6-Layer Repository Governance (`74/100` -> `100/100`)** | Repository root & `.github/` | Missing `.github/workflows/ci.yml` (`LIFECYCLE_NO_CI` error — allowing Findings 9 & 10 to ship), missing `SECURITY.md` (`GOVERNANCE_MISSING_SECURITY_MD` error), missing `AGENTS.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, issue/PR templates, and `README.md` Quick Start. | `8 × 6 = 48` | Added GitHub Actions matrix CI (`.github/workflows/ci.yml`), `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `AGENTS.md`, `CODEOWNERS`, templates, and `## Quick Start`. |

---

## 2. Physics, Electrical & RF Verification Equations

### 2.1 Battery Internal Resistance ($R_{\text{int}}$) & Pulse UVLO Margin
Instead of treating the cell as an ideal constant voltage source $V_{\text{nom}}$, `verify_battery_pulse_droop()` in `skills/battery-and-power/scripts/power_budget.py` evaluates terminal voltage under peak current $I_{\text{peak}}$:

$$V_{\text{term,min}}(T, \text{SOC}) = V_{\text{ocv}}(\text{SOC}) - I_{\text{peak}} \cdot R_{\text{int}}(T, \text{SOC}) \ge V_{\text{cutoff}} + V_{\text{margin}}$$

where $V_{\text{margin}} = 0.10\,\text{V}$ by default. For high-impedance primary cells (such as CR2032 where $R_{\text{int}} \in [15\,\Omega, 100\,\Omega]$ at $-10\,^\circ\text{C}$ or low SOC), a $30\,\text{mA}$ BLE TX + piezo burst requires either a bulk holdup capacitor sized via $C_{\text{holdup}} \ge \frac{I_{\text{pulse}} \cdot \Delta t_{\text{pulse}}}{\Delta V_{\text{allow}}}$ or a buck-boost regulator with input current limiting.

### 2.2 Cross-Domain `vio` Bus Compatibility & LDO Dropout
In `skills/battery-and-power/scripts/check_rails.py`:
- **`check_bus_vio_compatibility(rows, rails)`**: Groups all BOM components by shared digital bus (`I2C`, `SPI`, `UART`, `SWD`, `QSPI`, `USB`, `GPIO`) and checks that the intersection of their effective I/O voltage spans (`vio` in `key_specs`, `vio_rail`, or single-rail `supply_rail_v`) is non-empty and within $\pm 0.15\,\text{V}$ nominal mismatch unless a level shifter is present on the bus.
- **`check_ldo_dropout(rails)`**: For every linear regulator rail (`kind == "ldo"`), enforces:

$$V_{\text{in,min}} \ge V_{\text{out,max}} + V_{\text{dropout,max}}(I_{\text{peak}}, T_{\max})$$

### 2.3 Grounded Coplanar Waveguide (CPWG) $50\,\Omega$ Impedance & IC Junction Thermal Gate
In `skills/pcb-engineer/scripts/release_check.py`:
- **`cpwg_impedance_ohm(w_mm, s_mm, h_mm, er)`**: Computes characteristic impedance $Z_0$ using complete elliptic integrals of the first kind $K(k)$ via the Arithmetic-Geometric Mean (AGM):

$$k = \frac{a}{b}, \quad k_1 = \frac{\tanh(\pi a / 2h)}{\tanh(\pi b / 2h)}, \quad \varepsilon_{\text{eff}} = \frac{1 + \varepsilon_r \frac{K(k') K(k_1)}{K(k) K(k_1')}}{1 + \frac{K(k') K(k_1)}{K(k) K(k_1')}}, \quad Z_0 = \frac{60\pi}{\sqrt{\varepsilon_{\text{eff}}} \left( \frac{K(k)}{K(k')} + \frac{K(k_1)}{K(k_1')} \right)}$$

where $a = w/2$ and $b = w/2 + s$.
- **`check_thermal_rise(t_amb_c, p_diss_w, r_theta_ja_c_per_w, t_j_max_c)`**: Enforces $T_J = T_{\text{amb}} + P_{\text{diss}} \cdot R_{\theta\text{JA}} \le T_{J,\max}$.

### 2.4 3D BVH Full-Containment & Short-Edge Collision Oracles
In `skills/enclosure-engineer/scripts/validate_assembly.py`:
- **Short-edge midpoint parity (`0 < L < 2 * tol`)**: When dense fillets or screw threads produce triangle edges shorter than $2 \cdot \text{tol}$ ($0.04\,\text{mm}$), the midpoint $\mathbf{m} = \frac{1}{2}(\mathbf{v}_0 + \mathbf{v}_1)$ is tested against `bvh` using 3-axis majority ray-cast parity (`_parity_inside`) and `find_nearest` penetration depth.
- **Full-containment check (`n == 0` with overlapping closed AABBs)**: Tests vertex $\mathbf{v}_0$ of each closed mesh against the partner's BVH via `_parity_inside` so a component completely inside a solid boss or wall is always flagged.
