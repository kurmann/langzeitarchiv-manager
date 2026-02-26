"""Tests for lam.pack.packager (TAR creation)."""

import tarfile

import pytest

from lam.pack.packager import PackagerError, create_archive


@pytest.fixture()
def source_dir(tmp_path):
    d = tmp_path / "Familie_2025"
    d.mkdir()
    (d / "photo.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)
    (d / "video.mp4").write_bytes(b"\x00" * 1024)
    sub = d / "sub"
    sub.mkdir()
    (sub / "doc.txt").write_text("archival document")
    return d


def test_create_tar(source_dir, tmp_path):
    output_dir = tmp_path / "output"
    archive = create_archive(source_dir, output_dir, fmt="tar")

    assert archive.exists()
    assert archive.suffix == ".tar"
    assert archive.stem == source_dir.name


def test_tar_contains_all_files(source_dir, tmp_path):
    output_dir = tmp_path / "output"
    archive = create_archive(source_dir, output_dir, fmt="tar")

    with tarfile.open(archive, "r:") as tf:
        names = tf.getnames()
    assert any("photo.jpg" in n for n in names)
    assert any("video.mp4" in n for n in names)
    assert any("doc.txt" in n for n in names)


def test_tar_is_uncompressed(source_dir, tmp_path):
    """The TAR must be opened in 'store' (uncompressed) mode."""
    output_dir = tmp_path / "output"
    archive = create_archive(source_dir, output_dir, fmt="tar")
    # tarfile.is_tarfile confirms it's a valid tar
    assert tarfile.is_tarfile(archive)
    # mode "r:" only opens uncompressed tars – raises if compressed
    with tarfile.open(archive, "r:") as tf:
        assert len(tf.getmembers()) > 0


def test_output_dir_created_automatically(source_dir, tmp_path):
    output_dir = tmp_path / "a" / "b" / "c"
    assert not output_dir.exists()
    create_archive(source_dir, output_dir, fmt="tar")
    assert output_dir.exists()


def test_unknown_format_raises(source_dir, tmp_path):
    with pytest.raises(PackagerError, match="Unknown format"):
        create_archive(source_dir, tmp_path, fmt="zip")  # type: ignore[arg-type]


def test_iso_missing_tool(source_dir, tmp_path, monkeypatch):
    """When hdiutil is absent, PackagerError is raised."""
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(PackagerError, match="hdiutil"):
        create_archive(source_dir, tmp_path, fmt="iso")


def test_dmg_missing_tool(source_dir, tmp_path, monkeypatch):
    """When hdiutil is absent, PackagerError is raised."""
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(PackagerError, match="hdiutil"):
        create_archive(source_dir, tmp_path, fmt="dmg")
