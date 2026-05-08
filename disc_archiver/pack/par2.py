"""PAR2 redundancy-data creation via par2cmdline."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class Par2Error(Exception):
    """Raised when par2create fails or is not available."""


def create(archive_path: Path, redundancy_percent: int, volumes: int = 1) -> list[Path]:
    """Create PAR2 sidecar files next to *archive_path*.

    Parameters
    ----------
    archive_path:
        Path to the archive file (TAR / ISO / DMG) to protect.
    redundancy_percent:
        Redundancy level expressed as an integer percentage (e.g. 15 → 15 %).
    volumes:
        Number of PAR2 volume files to create (``-n`` flag). Defaults to 1,
        which consolidates all recovery data into a single volume file.

    Returns
    -------
    list[Path]
        Sorted list of the generated .par2 files.

    Raises
    ------
    Par2Error
        If ``par2`` / ``par2create`` is not on PATH or the subprocess exits
        with a non-zero return code.
    """
    # par2cmdline exposes either "par2" or "par2create"
    binary = shutil.which("par2") or shutil.which("par2create")
    if binary is None:
        raise Par2Error(
            "par2 / par2create not found. "
            "Install it first (e.g. `brew install par2` on macOS or "
            "`apt install par2` on Debian/Ubuntu)."
        )

    base_name = archive_path.stem  # e.g. "Familie_2025"
    par2_base = archive_path.parent / base_name

    cmd = [
        binary,
        "create",
        f"-r{redundancy_percent}",
        f"-n{volumes}",
        str(par2_base),
        str(archive_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Par2Error(
            f"par2 exited with code {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # Collect generated .par2 files (they live next to the archive)
    par2_files = sorted(archive_path.parent.glob(f"{base_name}*.par2"))
    return par2_files
