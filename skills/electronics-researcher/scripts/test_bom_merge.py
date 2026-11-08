#!/usr/bin/env python3
"""Tests for bom_merge.py on the fictional data in templates/examples/. Standard library only.

Run from anywhere: python3 test_bom_merge.py
"""
import csv
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.join(HERE, "..", "templates", "examples")
CASES = []


def case(f):
    CASES.append(f)
    return f


def run(bom, *extra):
    cmd = [sys.executable, os.path.join(HERE, "bom_merge.py"), "--bom", bom, "--parts", os.path.join(EX, "parts"),
           "--rails", os.path.join(EX, "power", "rails.json"), "--today", "2026-01-20", *extra]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def rows(bom):
    with open(bom, newline="", encoding="utf-8") as f:
        return {r["ref"]: r for r in csv.DictReader(f)}


def with_note(tmp, ref, note):
    src = os.path.join(EX, "bom.csv")
    dst = os.path.join(tmp, "bom.csv")
    with open(src, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        fields, data = rd.fieldnames, list(rd)
    for r in data:
        if r["ref"] == ref:
            r["notes"] = note
    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(data)
    return dst


@case
def clean_example_passes():
    tmp = tempfile.mkdtemp()
    bom = os.path.join(tmp, "bom.csv")
    shutil.copy(os.path.join(EX, "bom.csv"), bom)
    code, out = run(bom)
    assert code == 0, out


@case
def overwrite_merges_notes_instead_of_replacing():
    # the Pocket Beacon PoC bug: --overwrite replaced the BOM owner's note with the dossier note
    tmp = tempfile.mkdtemp()
    bom = with_note(tmp, "U2", "suffix ok; placed under the shield")
    code, out = run(bom, "--overwrite")
    n = rows(bom)["U2"]["notes"]
    assert code == 0, out
    assert n.startswith("suffix ok; placed under the shield"), n
    assert "order the 1.8 V suffix" in n, n


@case
def notes_are_not_duplicated_on_rerun():
    tmp = tempfile.mkdtemp()
    bom = with_note(tmp, "U2", "suffix ok")
    run(bom, "--overwrite")
    first = rows(bom)["U2"]["notes"]
    run(bom, "--overwrite")
    second = rows(bom)["U2"]["notes"]
    assert first == second and second.count("order the 1.8 V suffix") == 1, (first, second)


@case
def different_note_is_not_a_conflict_without_overwrite():
    tmp = tempfile.mkdtemp()
    bom = with_note(tmp, "U2", "hand-placed note")
    code, out = run(bom)
    assert "conflict in `notes`" not in out, out
    assert "hand-placed note" in rows(bom)["U2"]["notes"]


if __name__ == "__main__":
    bad = 0
    for c in CASES:
        try:
            c()
            print("ok  ", c.__name__)
        except AssertionError as ex:
            bad += 1
            print("FAIL", c.__name__, str(ex)[:400])
    print(f"test_bom_merge: {len(CASES) - bad}/{len(CASES)} passed")
    sys.exit(1 if bad else 0)
