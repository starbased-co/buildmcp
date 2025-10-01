"""Tests for checksum.py - JSON path operations and hashing utilities."""

import json
from pathlib import Path

import pytest

from buildmcp.checksum import (
    check_mcp_lock,
    hash_json_data,
    hash_json_paths,
    hash_profiles,
    read_dot_mcp,
    read_json_path,
    write_dot_mcp,
    write_json_path,
    write_mcp_lock,
)


class TestReadJsonPath:
    """Test reading values from JSON files at specific paths."""

    def test_read_root_path(self, tmp_path: Path):
        """Read entire file with root path '.'"""
        data = {"key": "value", "number": 42}
        file = tmp_path / "test.json"
        file.write_text(json.dumps(data))

        result = read_json_path(file, ".")
        assert result == data

    def test_read_nested_path(self, tmp_path: Path):
        """Read nested key using dpath."""
        data = {"a": {"b": {"c": "deep_value"}}}
        file = tmp_path / "test.json"
        file.write_text(json.dumps(data))

        result = read_json_path(file, ".a.b.c")
        assert result == "deep_value"

    def test_read_missing_file(self, tmp_path: Path):
        """FileNotFoundError raised for missing file."""
        file = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            read_json_path(file, ".")

    def test_read_invalid_json(self, tmp_path: Path):
        """JSONDecodeError raised for invalid JSON."""
        file = tmp_path / "invalid.json"
        file.write_text("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            read_json_path(file, ".")

    def test_read_missing_key(self, tmp_path: Path):
        """KeyError raised for missing key."""
        data = {"key": "value"}
        file = tmp_path / "test.json"
        file.write_text(json.dumps(data))

        with pytest.raises(KeyError):
            read_json_path(file, ".missing")


class TestWriteJsonPath:
    """Test writing values to JSON files at specific paths."""

    def test_write_root_replaces_entire_file(self, tmp_path: Path):
        """Writing to root path replaces entire file."""
        file = tmp_path / "test.json"
        file.write_text(json.dumps({"old": "data"}))

        new_data = {"new": "content"}
        write_json_path(file, new_data, ".")

        result = json.loads(file.read_text())
        assert result == new_data

    def test_write_nested_path_creates_intermediates(self, tmp_path: Path):
        """dpath.new creates intermediate keys automatically."""
        file = tmp_path / "test.json"
        file.write_text(json.dumps({}))

        write_json_path(file, "deep_value", ".a.b.c")

        result = json.loads(file.read_text())
        assert result == {"a": {"b": {"c": "deep_value"}}}

    def test_write_creates_parent_directory(self, tmp_path: Path):
        """Writing creates parent directory if missing."""
        file = tmp_path / "subdir" / "test.json"
        assert not file.parent.exists()

        write_json_path(file, {"key": "value"}, ".")

        assert file.parent.exists()
        assert file.exists()

    def test_write_adds_trailing_newline(self, tmp_path: Path):
        """Written files have trailing newline."""
        file = tmp_path / "test.json"
        write_json_path(file, {"key": "value"}, ".")

        content = file.read_text()
        assert content.endswith("\n")

    def test_write_uses_indent_2(self, tmp_path: Path):
        """Written files use 2-space indentation."""
        file = tmp_path / "test.json"
        write_json_path(file, {"key": {"nested": "value"}}, ".")

        content = file.read_text()
        assert '  "key"' in content

    def test_write_preserves_unrelated_keys(self, tmp_path: Path):
        """Partial updates preserve other keys."""
        file = tmp_path / "test.json"
        file.write_text(json.dumps({"keep": "this", "change": "old"}))

        write_json_path(file, "new", ".change")

        result = json.loads(file.read_text())
        assert result["keep"] == "this"
        assert result["change"] == "new"


class TestMcpHelpers:
    """Test convenience helpers for MCP configuration files."""

    def test_read_dot_mcp_default_path(self, tmp_path: Path, monkeypatch):
        """read_dot_mcp uses ~/.claude/mcp.json by default."""
        mcp_dir = tmp_path / ".claude"
        mcp_dir.mkdir()
        mcp_file = mcp_dir / "mcp.json"
        data = {"profiles": {"default": []}}
        mcp_file.write_text(json.dumps(data))

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = read_dot_mcp()
        assert result == data

    def test_read_dot_mcp_custom_path(self, tmp_path: Path):
        """read_dot_mcp accepts custom path."""
        file = tmp_path / "custom.json"
        data = {"key": "value"}
        file.write_text(json.dumps(data))

        result = read_dot_mcp(file)
        assert result == data

    def test_write_dot_mcp_default_path(self, tmp_path: Path, monkeypatch):
        """write_dot_mcp uses ~/.claude/mcp.json by default."""
        mcp_dir = tmp_path / ".claude"
        mcp_dir.mkdir()

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        data = {"profiles": {}}
        write_dot_mcp(data)

        mcp_file = mcp_dir / "mcp.json"
        result = json.loads(mcp_file.read_text())
        assert result == data


class TestHashJsonData:
    """Test JSON data hashing for change detection."""

    def test_hash_deterministic(self):
        """Same data produces same hash."""
        data = {"key": "value", "number": 42}
        hash1 = hash_json_data(data)
        hash2 = hash_json_data(data)
        assert hash1 == hash2

    def test_hash_different_data(self):
        """Different data produces different hash."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        hash1 = hash_json_data(data1)
        hash2 = hash_json_data(data2)
        assert hash1 != hash2

    def test_hash_order_independent(self):
        """Dict key order doesn't affect hash (sort_keys=True)."""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}
        hash1 = hash_json_data(data1)
        hash2 = hash_json_data(data2)
        assert hash1 == hash2

    def test_hash_sha256_algorithm(self):
        """SHA256 algorithm produces expected length hash."""
        data = {"key": "value"}
        hash_result = hash_json_data(data, algorithm="sha256")
        assert len(hash_result) == 64  # SHA256 hex digest length

    def test_hash_md5_algorithm(self):
        """MD5 algorithm produces expected length hash."""
        data = {"key": "value"}
        hash_result = hash_json_data(data, algorithm="md5")
        assert len(hash_result) == 32  # MD5 hex digest length

    def test_hash_various_types(self):
        """Hash works with various JSON types."""
        test_cases = [
            {"dict": "value"},
            ["list", "items"],
            "string",
            42,
            None,
            {"nested": {"deeply": ["mixed", 123, None]}},
        ]

        for data in test_cases:
            hash_result = hash_json_data(data)
            assert isinstance(hash_result, str)
            assert len(hash_result) > 0

    def test_hash_empty_structures(self):
        """Empty dict and list produce different hashes."""
        hash_dict = hash_json_data({})
        hash_list = hash_json_data([])
        assert hash_dict != hash_list


class TestHashJsonPaths:
    """Test hashing multiple JSON paths together."""

    def test_hash_single_path(self, tmp_path: Path):
        """Hash single path."""
        file = tmp_path / "test.json"
        data = {"profiles": {"default": ["server1", "server2"]}}
        file.write_text(json.dumps(data))

        hash_result = hash_json_paths(file, [".profiles.default"])
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_hash_multiple_paths(self, tmp_path: Path):
        """Hash multiple paths combined."""
        file = tmp_path / "test.json"
        data = {
            "profiles": {"default": ["server1"]},
            "mcpServers": {"base": {}},
        }
        file.write_text(json.dumps(data))

        hash_result = hash_json_paths(file, [".profiles.default", ".mcpServers"])
        assert isinstance(hash_result, str)

    def test_hash_paths_order_matters(self, tmp_path: Path):
        """Path order affects combined hash."""
        file = tmp_path / "test.json"
        data = {"a": 1, "b": 2}
        file.write_text(json.dumps(data))

        hash1 = hash_json_paths(file, [".a", ".b"])
        hash2 = hash_json_paths(file, [".b", ".a"])
        assert hash1 != hash2


class TestHashProfiles:
    """Test hashing all profiles in configuration."""

    def test_hash_profiles_with_profiles(self):
        """Hash all profiles in config."""
        config = {
            "profiles": {
                "default": ["server1", "server2"],
                "minimal": ["server1"],
            }
        }

        hashes = hash_profiles(config)
        assert "default" in hashes
        assert "minimal" in hashes
        assert hashes["default"] != hashes["minimal"]

    def test_hash_profiles_without_profiles(self):
        """No profiles returns empty dict."""
        config = {"mcpServers": {}}
        hashes = hash_profiles(config)
        assert hashes == {}

    def test_hash_profiles_deterministic(self):
        """Same profiles produce same hashes."""
        config = {"profiles": {"default": ["server1"]}}
        hashes1 = hash_profiles(config)
        hashes2 = hash_profiles(config)
        assert hashes1 == hashes2


class TestLockFileOperations:
    """Test lock file creation and validation."""

    def test_write_mcp_lock_creates_file(self, tmp_path: Path):
        """write_mcp_lock creates .lock file."""
        config_file = tmp_path / "mcp.json"
        config = {"profiles": {"default": ["server1"]}}
        config_file.write_text(json.dumps(config))

        write_mcp_lock(config_file)

        lock_file = tmp_path / "mcp.lock"
        assert lock_file.exists()

    def test_write_mcp_lock_content(self, tmp_path: Path):
        """Lock file contains profile hashes."""
        config_file = tmp_path / "mcp.json"
        config = {
            "profiles": {
                "default": ["server1"],
                "minimal": ["server2"],
            }
        }
        config_file.write_text(json.dumps(config))

        write_mcp_lock(config_file)

        lock_file = tmp_path / "mcp.lock"
        lock_data = json.loads(lock_file.read_text())
        assert "default" in lock_data
        assert "minimal" in lock_data

    def test_check_mcp_lock_no_lock_file(self, tmp_path: Path):
        """No lock file returns False for all profiles."""
        config_file = tmp_path / "mcp.json"
        config = {"profiles": {"default": [], "minimal": []}}
        config_file.write_text(json.dumps(config))

        status = check_mcp_lock(config_file)
        assert status["default"] is False
        assert status["minimal"] is False

    def test_check_mcp_lock_unchanged(self, tmp_path: Path):
        """Unchanged profiles return True."""
        config_file = tmp_path / "mcp.json"
        config = {"profiles": {"default": ["server1"]}}
        config_file.write_text(json.dumps(config))

        write_mcp_lock(config_file)
        status = check_mcp_lock(config_file)

        assert status["default"] is True

    def test_check_mcp_lock_changed(self, tmp_path: Path):
        """Changed profiles return False."""
        config_file = tmp_path / "mcp.json"
        config = {"profiles": {"default": ["server1"]}}
        config_file.write_text(json.dumps(config))

        write_mcp_lock(config_file)

        config["profiles"]["default"].append("server2")
        config_file.write_text(json.dumps(config))

        status = check_mcp_lock(config_file)
        assert status["default"] is False
