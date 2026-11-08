# Fictional test data

The companies, part numbers and prices in this folder are made up. They exist only to test `scripts/bom_merge.py`. Do not use them in a design.

From the skill's base directory:

```
cp templates/examples/bom.csv /tmp/bom.csv
python3 scripts/bom_merge.py --bom /tmp/bom.csv --parts templates/examples/parts \
  --rails templates/examples/power/rails.json --today 2026-01-20
```

Expected result:

- exit 0, with warnings;
- U1's truncated MPN `EXB200-QF` is corrected to `EXB200-QF32-R7`;
- U1 gets a lifecycle warning (`sampling`, while the distributor says Active);
- U2's rail `1V8` (1.75–1.85 V in `power/rails.json`) is checked against its supply range of 1.7–1.95 V.
