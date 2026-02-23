"""Structural validation of the source directory before archiving."""

from __future__ import annotations

from pathlib import Path


class ValidationError(Exception):
    """Raised when the source directory fails a validation check."""


def validate(source_dir: Path) -> None:
    """Validate *source_dir* before archiving.

    Raises :class:`ValidationError` with a descriptive message on the first
    problem found. Checks performed (in order):

    1. Directory exists.
    2. Directory is not empty.
    3. No file is 0 bytes.
    """
    if not source_dir.exists():
        raise ValidationError(f"Source directory does not exist: {source_dir}")
    if not source_dir.is_dir():
        raise ValidationError(f"Source path is not a directory: {source_dir}")

    all_files = [p for p in source_dir.rglob("*") if p.is_file()]

    if not all_files:
        raise ValidationError(f"Source directory is empty: {source_dir}")

    zero_byte_files = [p for p in all_files if p.stat().st_size == 0]
    if zero_byte_files:
        names = ", ".join(str(p) for p in zero_byte_files[:5])
        extra = f" (and {len(zero_byte_files) - 5} more)" if len(zero_byte_files) > 5 else ""
        raise ValidationError(f"Found 0-byte file(s): {names}{extra}")
