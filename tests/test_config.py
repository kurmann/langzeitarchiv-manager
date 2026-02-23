"""Tests for lam.config."""

import pytest

from lam import config as cfg


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect config file to a temporary directory for each test."""
    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path / "lam_config")
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / "lam_config" / "config.toml")


def test_get_default_redundancy():
    value = cfg.get("pack.redundancy_percent")
    assert value == 15


def test_get_default_format():
    value = cfg.get("pack.default_format")
    assert value == "tar"


def test_set_and_get_string():
    cfg.set_value("pack.default_format", "iso")
    assert cfg.get("pack.default_format") == "iso"


def test_set_and_get_int():
    cfg.set_value("pack.redundancy_percent", "20")
    assert cfg.get("pack.redundancy_percent") == 20


def test_set_creates_config_dir(tmp_path, monkeypatch):
    config_dir = tmp_path / "new_dir"
    monkeypatch.setattr(cfg, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cfg, "CONFIG_FILE", config_dir / "config.toml")
    cfg.set_value("pack.redundancy_percent", "10")
    assert (config_dir / "config.toml").exists()


def test_list_all_contains_defaults():
    data = cfg.list_all()
    assert "pack" in data
    assert data["pack"]["redundancy_percent"] == 15


def test_list_all_reflects_user_setting():
    cfg.set_value("pack.redundancy_percent", "30")
    data = cfg.list_all()
    assert data["pack"]["redundancy_percent"] == 30


def test_get_unknown_key_returns_none():
    value = cfg.get("nonexistent.key")
    assert value is None
