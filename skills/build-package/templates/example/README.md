# Test fixture

A fictional board ("fixture board") used only to test `assemble_release.py` and `release_check.py`. It is not a product and not a design example.

- `scripts/selftest.py` copies `hw/` to a temporary folder and adds the binary-like files: a Gerber zip with dummy layers, a STEP stub, an STL stub and a PDF stub.
- All part numbers start with `FIXTURE-` and do not exist.
