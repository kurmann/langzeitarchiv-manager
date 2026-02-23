"""Archive creation for TAR, ISO, and DMG formats."""

from __future__ import annotations

import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Literal

ArchiveFormat = Literal["tar", "iso", "dmg"]


class PackagerError(Exception):
    """Raised when archive creation fails."""


def create_archive(
    source_dir: Path,
    output_dir: Path,
    fmt: ArchiveFormat = "tar",
) -> Path:
    """Create an archive of *source_dir* inside *output_dir*.

    Parameters
    ----------
    source_dir:
        The directory to archive.
    output_dir:
        Destination directory (created if it doesn't exist).
    fmt:
        Archive format: ``"tar"``, ``"iso"``, or ``"dmg"``.

    Returns
    -------
    Path
        Path to the created archive file.

    Raises
    ------
    PackagerError
        If the chosen format's external tool is unavailable or fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_name = source_dir.name  # e.g. "Familie_2025"

    if fmt == "tar":
        return _create_tar(source_dir, output_dir, archive_name)
    elif fmt == "iso":
        return _create_iso(source_dir, output_dir, archive_name)
    elif fmt == "dmg":
        return _create_dmg(source_dir, output_dir, archive_name)
    else:
        raise PackagerError(f"Unknown format: {fmt!r}")


# ---------------------------------------------------------------------------
# Format implementations
# ---------------------------------------------------------------------------


def _create_tar(source_dir: Path, output_dir: Path, name: str) -> Path:
    archive_path = output_dir / f"{name}.tar"
    with tarfile.open(archive_path, mode="w:") as tf:
        tf.add(source_dir, arcname=name)
    return archive_path


def _create_iso(source_dir: Path, output_dir: Path, name: str) -> Path:
    archive_path = output_dir / f"{name}.iso"
    binary = shutil.which("xorriso")
    if binary is None:
        raise PackagerError(
            "xorriso not found. "
            "Install it first (e.g. `brew install xorriso` on macOS or "
            "`apt install xorriso` on Debian/Ubuntu)."
        )
    cmd = [
        binary,
        "-as", "mkisofs",
        "-o", str(archive_path),
        "-V", name[:32],   # volume label (max 32 chars)
        "-udf",
        "-r",
        str(source_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise PackagerError(
            f"xorriso exited with code {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return archive_path


def _create_dmg(source_dir: Path, output_dir: Path, name: str) -> Path:
    archive_path = output_dir / f"{name}.dmg"
    binary = shutil.which("hdiutil")
    if binary is None:
        raise PackagerError(
            "hdiutil not found. "
            "hdiutil is a macOS built-in tool and is not available on this system."
        )
    cmd = [
        binary,
        "create",
        "-volname", name,
        "-srcfolder", str(source_dir),
        "-ov",
        "-format", "UDRO",   # read-only, uncompressed (store mode)
        str(archive_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise PackagerError(
            f"hdiutil exited with code {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return archive_path
