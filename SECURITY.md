# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| `0.1.x` / `main` | Yes |

## Reporting a Vulnerability

If you discover a security issue in the Hardware Design Toolkit (for example in toolchain installation scripts, headless browser automation, CAD/EDA script execution, or CSV/manifest generation), please report it responsibly:

1. **Preferred:** Open a private security advisory via [GitHub Security Advisories](https://github.com/ctresb/hardware-design-toolkit/security/advisories/new).
2. **Public Issue (non-exploitable hardening gaps):** Open an issue using the bug report template and tag it with `security`.

## Security Hardening Principles in This Repository

- **Loopback Isolation for Headless Browser Checks:** `skills/product-presentation/scripts/layout_check.py` serves presentation directories over an ephemeral `127.0.0.1` HTTP server with `--disable-background-networking` rather than opening `file://` URLs with `--allow-file-access-from-files`.
- **Checksum Verification for Toolchain Binaries:** `skills/toolchain-setup/scripts/` verifies SHA-256 checksums before installing downloaded archives (`FREEROUTING_SHA256`, `AWSCLI_SHA256`, `SSM_PLUGIN_SHA256`).
- **CSV Formula Injection Neutralization:** `skills/build-package/scripts/release_lib.py` sanitizes leading formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) when writing BOM and CPL CSV artifacts.
