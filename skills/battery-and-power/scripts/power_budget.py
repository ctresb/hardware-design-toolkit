#!/usr/bin/env python3
"""Power budget for a battery-powered device: average battery current per scenario, runtime, required cell.

Reads a JSON budget (see templates/power_budget.example.json), converts every part's rail current into
battery current through its regulator, weights the modes by duty cycle and reports four scenarios:

  optimistic   bottom-up datasheet figures x scenario factor (default 0.8)
  baseline     bottom-up datasheet figures x 1.0
  pessimistic  bottom-up x factor (default 2.0) for firmware overhead, leakage, wake-ups, retries
  empirical    average current of comparable shipped products (capacity x usable / runtime)

Real products often draw 3-5x a bottom-up datasheet budget. The empirical case keeps the budget honest
until a dev-kit measurement replaces it.

Rails: each entry in "rails" carries its voltage as {"nom": V, "tol": V} or {"min": V, "max": V},
its current limit "max_ma", and the regulator model ("type": direct|ldo|buck|boost, "efficiency",
"iq_ma", "off_modes"). --rails-out writes the shared rail table hw/power/rails.json, which holds only
voltage and max_ma: {"<RAIL>": {"nom": V, "tol": V, "max_ma": mA}} or {"<RAIL>": {"min": V, "max": V, "max_ma": mA}}.

Standard library only.
usage: power_budget.py budget.json [-o hw/power/budget.json] [--rails-out hw/power/rails.json]
"""
import argparse
import json
import sys


def battery_current(load_ma, rail_v, rail, vbat):
    """Battery-side current for a load on a rail (without the regulator's quiescent current)."""
    kind = rail.get("type", "direct")
    if kind in ("direct", "ldo"):
        return load_ma                       # an LDO passes the load current through (Iq is added per rail)
    if kind in ("buck", "boost", "switcher"):
        eff = float(rail.get("efficiency", 0.85))
        return load_ma * rail_v / (vbat * eff)
    raise ValueError(f"unknown rail type {kind!r} (use direct, ldo, buck, boost)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("budget", help="input budget JSON")
    ap.add_argument("-o", "--out", help="write results JSON here (e.g. hw/power/budget.json)")
    ap.add_argument("--capacity-mah", type=float, help="override rated cell capacity (mAh)")
    ap.add_argument("--rails-out", help="write the shared rail table (e.g. hw/power/rails.json)")
    a = ap.parse_args()

    cfg = json.load(open(a.budget))
    bat = cfg.get("battery", {})
    vbat = float(bat.get("nominal_v", 3.7))
    usable = float(bat.get("usable_fraction", 0.85))
    eol = float(bat.get("eol_fraction", 0.80))
    rated = a.capacity_mah or bat.get("rated_mah")
    target_h = cfg.get("target_runtime_h")
    rails = {str(k): v for k, v in cfg.get("rails", {}).items()}
    modes = cfg["modes"]
    parts = cfg["parts"]
    factors = {"optimistic": 0.8, "baseline": 1.0, "pessimistic": 2.0}
    factors.update(cfg.get("scenario_factors", {}))

    warnings = []
    duty_sum = sum(float(m["duty"]) for m in modes)
    if abs(duty_sum - 1.0) > 1e-3:
        warnings.append(f"mode duties sum to {duty_sum:.3f}, not 1.0; normalized")
    names = [m["name"] for m in modes]

    # per-mode battery current (bottom-up)
    per_mode = {}
    peaks = {}
    contrib = {}
    for m in modes:
        tot = 0.0
        pk = 0.0
        w = float(m["duty"]) / duty_sum
        for p in parts:
            cm = p.get("currents_ma", {})
            cur = float(cm.get(m["name"], cm.get("*", 0.0)))
            rail_v = float(p.get("rail_v", vbat))
            rail = rails.get(str(p["rail"]), {"type": "direct"}) if p.get("rail") else {"type": "direct"}
            ib = battery_current(cur, rail_v, rail, vbat)
            tot += ib
            contrib[p["ref"]] = contrib.get(p["ref"], 0.0) + ib * w
            if cur > 0 and p.get("peak_ma") is not None and m["name"] in p.get("peak_modes", names):
                pk += battery_current(float(p["peak_ma"]), rail_v, rail, vbat)
            else:
                pk += ib
        # regulator quiescent current: once per rail, unless the rail is off in this mode
        for rn, r in rails.items():
            if m["name"] in r.get("off_modes", []):
                continue
            iq = float(r.get("iq_ma", 0.0))
            tot += iq
            pk += iq
            contrib["rail " + rn] = contrib.get("rail " + rn, 0.0) + iq * w
        per_mode[m["name"]] = tot
        peaks[m["name"]] = pk
    avg = sum(per_mode[m["name"]] * float(m["duty"]) for m in modes) / duty_sum

    # missing evidence
    for p in parts:
        ev = str(p.get("evidence", ""))
        if not ev.startswith("[") or not any(t in ev for t in ("verified", "estimate", "assumption", "measured")):
            warnings.append(f"{p['ref']}: no evidence tag ([verified|measured|estimate|assumption: ...])")

    scen = {k: avg * float(f) for k, f in factors.items()}
    measured = cfg.get("measured_avg_ma")
    if measured:
        scen["measured"] = float(measured)

    emp = []
    for c in cfg.get("comparables", []):
        cur = float(c["capacity_mah"]) * float(c.get("usable_fraction", 0.9)) / float(c["runtime_h"])
        emp.append(dict(c, avg_ma=round(cur, 3)))
    if emp:
        scen["empirical"] = sum(e["avg_ma"] for e in emp) / len(emp)

    def runtime(cap, cur):
        return cap * usable / cur if cur > 0 else float("inf")

    def need(cur):
        return cur * target_h / (usable * eol) if target_h else None

    rows = []
    for k, cur in scen.items():
        r = dict(scenario=k, avg_ma=round(cur, 3))
        if rated:
            r["runtime_new_h"] = round(runtime(rated, cur), 1)
            r["runtime_eol_h"] = round(runtime(rated * eol, cur), 1)
        if target_h:
            r["rated_mah_needed"] = round(need(cur), 1)
            r["max_avg_ma_new"] = round(rated * usable / target_h, 3) if rated else None
            r["max_avg_ma_eol"] = round(rated * usable * eol / target_h, 3) if rated else None
        rows.append(r)

    # peak current chain
    worst_peak = max(peaks.values()) if peaks else 0.0
    limits = []
    for L in cfg.get("limits", []):
        mx = L.get("max_ma")
        if mx is None and L.get("c_rate") and rated:
            mx = float(L["c_rate"]) * rated
        if mx is None:
            continue
        limits.append(dict(name=L["name"], max_ma=round(float(mx), 1), worst_peak_ma=round(worst_peak, 1),
                           ok=worst_peak <= float(mx), evidence=L.get("evidence", "")))
        if worst_peak > float(mx):
            warnings.append(f"peak {worst_peak:.0f} mA exceeds {L['name']} ({float(mx):.0f} mA)")

    # per-rail worst-case load (sum of part peaks on the rail) vs the rail's max_ma; shared rails.json
    rail_load = {}
    for p in parts:
        if not p.get("rail"):
            continue
        cm = p.get("currents_ma", {})
        worst = max([float(v) for v in cm.values()] + [float(p.get("peak_ma") or 0)])
        rail_load[str(p["rail"])] = rail_load.get(str(p["rail"]), 0.0) + worst
    rails_table = {}
    for rn, r in rails.items():
        e = {k: r[k] for k in ("min", "max") if k in r} or {k: r[k] for k in ("nom", "tol") if k in r}
        if not e:
            warnings.append(f"rail {rn}: no voltage (give nom+tol or min+max)")
        if "max_ma" in r:
            e["max_ma"] = r["max_ma"]
            if rail_load.get(rn, 0) > float(r["max_ma"]):
                warnings.append(f"rail {rn}: worst-case load {rail_load[rn]:.0f} mA exceeds its max_ma {r['max_ma']}")
        rails_table[rn] = e
    if a.rails_out:
        json.dump(rails_table, open(a.rails_out, "w"), indent=1)

    # print
    print(f"Battery {vbat} V nominal, usable {usable:.0%}, end of life {eol:.0%}"
          + (f", rated {rated} mAh" if rated else "") + (f", target {target_h} h" if target_h else ""))
    print("\nMode            duty    battery mA   peak mA")
    for m in modes:
        print(f"{m['name']:<14} {float(m['duty']) / duty_sum:6.1%}   {per_mode[m['name']]:10.3f}  {peaks[m['name']]:8.1f}")
    print("\nScenario        avg mA   runtime new h   runtime EOL h   rated mAh needed")
    for r in rows:
        print(f"{r['scenario']:<14} {r['avg_ma']:7.3f}   {str(r.get('runtime_new_h', '-')):>13}   "
              f"{str(r.get('runtime_eol_h', '-')):>13}   {str(r.get('rated_mah_needed', '-')):>16}")
    top = sorted(contrib.items(), key=lambda kv: -kv[1])[:6]
    print("\nLargest contributors (baseline, duty-weighted): " +
          ", ".join(f"{k} {v:.3f} mA ({v / avg:.0%})" for k, v in top if avg > 0))
    for L in limits:
        print(f"Peak check: {L['name']}: worst-case {L['worst_peak_ma']} mA vs limit {L['max_ma']} mA -> "
              + ("OK" if L["ok"] else "EXCEEDED"))
    if "empirical" in scen and scen["empirical"] > 2 * avg:
        warnings.append(f"comparable products average {scen['empirical']:.2f} mA, {scen['empirical'] / avg:.1f}x the "
                        "bottom-up baseline: plan the cell on the pessimistic/empirical case until measured")
    if not measured:
        warnings.append("no measured_avg_ma yet: measure on a dev kit before ordering a custom cell or a mold")
    for w in warnings:
        print("WARNING:", w)

    out = dict(inputs=a.budget, rails=rails_table, rail_worst_load_ma=rail_load, battery=dict(nominal_v=vbat, usable_fraction=usable, eol_fraction=eol, rated_mah=rated),
               target_runtime_h=target_h, per_mode_ma=per_mode, peak_ma=peaks, scenarios=rows,
               contributors_ma=contrib, comparables=emp, limits=limits, warnings=warnings)
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1)
    gate = all(L["ok"] for L in limits)
    worst = max(r.get("rated_mah_needed") or 0 for r in rows) if target_h else None
    print(f"\nSUMMARY baseline {avg:.3f} mA; " + (f"cell needed {need(avg):.0f}-{worst:.0f} mAh rated; " if target_h else "")
          + ("peaks OK" if gate else "PEAK LIMIT EXCEEDED"))
    return 0 if gate else 2


if __name__ == "__main__":
    sys.exit(main())
