"""Tests for lam.pack.validator."""

import pytest

from lam.pack.validator import ValidationError, validate


def test_valid_directory(tmp_path):
    (tmp_path / "file.txt").write_text("hello")
    validate(tmp_path)  # should not raise


def test_nonexistent_directory(tmp_path):
    missing = tmp_path / "does_not_exist"
    with pytest.raises(ValidationError, match="does not exist"):
        validate(missing)


def test_empty_directory(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValidationError, match="empty"):
        validate(empty)


def test_zero_byte_file(tmp_path):
    (tmp_path / "normal.txt").write_text("data")
    (tmp_path / "empty.txt").write_bytes(b"")
    with pytest.raises(ValidationError, match="0-byte"):
        validate(tmp_path)


def test_zero_byte_nested(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "data.txt").write_text("content")
    (sub / "empty.bin").write_bytes(b"")
    with pytest.raises(ValidationError, match="0-byte"):
        validate(tmp_path)


def test_not_a_directory(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hi")
    with pytest.raises(ValidationError, match="not a directory"):
        validate(f)
