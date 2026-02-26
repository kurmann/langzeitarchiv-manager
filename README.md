# Langzeitarchiv-Manager (LAM)

A CLI tool for long-term digital archiving. It packs directories into
uncompressed archives (TAR / ISO / DMG), adds PAR2 redundancy data, and
provides a TOML-based configuration system.

---

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| **par2** / **par2cmdline** | PAR2 redundancy data | `brew install par2` (macOS) · `apt install par2` (Debian/Ubuntu) |
| **hdiutil** | ISO and DMG image creation (`--format iso` / `--format dmg`) | built-in macOS only |

Python **3.12+** is required.

---

## Installation

```bash
pipx install .
```

This registers two entry points: `langzeitarchiv-manager` and the shorter alias `lam`.

---

## Usage

### `lam pack`

Pack a directory into an archive and create PAR2 redundancy data alongside it.

```bash
lam pack <source_dir> [--format tar|iso|dmg] [--output <dir>] [--redundancy <percent>]
```

**Examples**

```bash
# Create an uncompressed TAR in ~/LAM/staging/ with 15 % PAR2 redundancy
lam pack ~/Projects/Familie_2025

# Create an ISO with 20 % redundancy in a custom output directory
lam pack ~/Projects/Familie_2025 --format iso --output /Volumes/Archive --redundancy 20

# Use a DMG (macOS only)
lam pack ~/Projects/MyApp --format dmg --output ~/Desktop/Archives
```

**What it does**

1. Validates the source directory (checks for emptiness and 0-byte files).
2. Creates an archive (`Familie_2025.tar`, `.iso`, or `.dmg`) in the output directory.
3. Creates PAR2 sidecar files next to the archive.
4. Prints a summary table of all created files and their sizes.

### `lam config`

Manage persistent settings stored in `~/.config/langzeitarchiv-manager/config.toml`.

```bash
# List all settings
lam config list

# Get a single value
lam config get pack.redundancy_percent

# Set a value
lam config set pack.redundancy_percent 20
lam config set pack.output_dir /Volumes/Archive/staging
lam config set pack.default_format iso
```

**Supported configuration keys**

| Key | Type | Default | Description |
|---|---|---|---|
| `pack.redundancy_percent` | int | `15` | PAR2 redundancy in % |
| `pack.output_dir` | str | `~/LAM/staging/` | Default output directory |
| `pack.default_format` | str | `tar` | Default archive format |

---

## Development

```bash
# Install in editable mode with test dependencies
pip install -e ".[dev]"

# Run the test suite
pytest
```
