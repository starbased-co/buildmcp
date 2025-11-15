"""Tests for builder.py - MCP configuration building and deployment."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from buildmcp.builder import MCPBuilder


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_valid_config(self, config_file: Path):
        """Load valid JSON configuration."""
        builder = MCPBuilder(mcp_json=config_file)
        config = builder.load_config()

        assert "mcpServers" in config
        assert "templates" in config
        assert "profiles" in config
        assert "targets" in config

    def test_load_missing_file(self, tmp_path: Path, capsys):
        """Missing file logs error and exits."""
        missing_file = tmp_path / "missing.json"
        builder = MCPBuilder(mcp_json=missing_file)

        try:
            builder.load_config()
            assert False, "Should have raised SystemExit"
        except BaseException as e:
            assert e.code == 1
            captured = capsys.readouterr()
            assert "not found" in captured.err

    def test_load_invalid_json(self, tmp_path: Path, capsys):
        """Invalid JSON logs error and exits."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json")
        builder = MCPBuilder(mcp_json=invalid_file)

        try:
            builder.load_config()
            assert False, "Should have raised SystemExit"
        except BaseException as e:
            assert e.code == 1
            captured = capsys.readouterr()
            assert "Error parsing JSON" in captured.err


class TestSubstituteEnvVars:
    """Test environment variable substitution."""

    def test_substitute_single_var(self, mock_env):
        """Substitute single environment variable."""
        mock_env(FOO="bar")
        builder = MCPBuilder()

        result = builder.substitute_env_vars("${FOO}")
        assert result == "bar"

    def test_substitute_multiple_vars(self, mock_env):
        """Substitute multiple variables in string."""
        mock_env(FOO="hello", BAR="world")
        builder = MCPBuilder()

        result = builder.substitute_env_vars("${FOO}_${BAR}")
        assert result == "hello_world"

    def test_substitute_missing_var_preserves_placeholder(self):
        """Missing variable preserves placeholder."""
        builder = MCPBuilder(check_env=True)

        result = builder.substitute_env_vars("${MISSING}")
        assert result == "${MISSING}"
        assert "MISSING" in builder._missing_vars

    def test_substitute_missing_var_tracked(self):
        """Missing variables tracked in _missing_vars."""
        builder = MCPBuilder()

        builder.substitute_env_vars("${VAR1} and ${VAR2}")
        assert "VAR1" in builder._missing_vars
        assert "VAR2" in builder._missing_vars

    def test_substitute_sensitive_data_masking(self, mock_env):
        """Sensitive data (>10 chars with KEY/TOKEN) masked in verbose mode."""
        mock_env(API_KEY="verylongsecretkey123")
        builder = MCPBuilder(verbose=True)

        result = builder.substitute_env_vars("${API_KEY}")
        assert result == "verylongsecretkey123"

    def test_substitute_short_sensitive_not_masked(self, mock_env):
        """Short sensitive values (<= 10 chars) not masked."""
        mock_env(API_KEY="short")
        builder = MCPBuilder(verbose=True)

        result = builder.substitute_env_vars("${API_KEY}")
        assert result == "short"

    def test_substitute_dict_recursion(self, mock_env):
        """Substitute recursively in dict."""
        mock_env(FOO="bar")
        builder = MCPBuilder()

        data = {"key1": "${FOO}", "nested": {"key2": "${FOO}"}}
        result = builder.substitute_env_vars(data)

        assert result["key1"] == "bar"
        assert result["nested"]["key2"] == "bar"

    def test_substitute_list_recursion(self, mock_env):
        """Substitute recursively in list."""
        mock_env(FOO="bar")
        builder = MCPBuilder()

        data = ["${FOO}", {"nested": "${FOO}"}]
        result = builder.substitute_env_vars(data)

        assert result[0] == "bar"
        assert result[1]["nested"] == "bar"

    def test_substitute_primitives_passthrough(self):
        """Primitives (int, bool, None) pass through unchanged."""
        builder = MCPBuilder()

        assert builder.substitute_env_vars(42) == 42
        assert builder.substitute_env_vars(True) is True
        assert builder.substitute_env_vars(None) is None

    def test_substitute_no_placeholders(self):
        """Strings without placeholders unchanged."""
        builder = MCPBuilder()

        result = builder.substitute_env_vars("no placeholders here")
        assert result == "no placeholders here"

    def test_substitute_empty_string(self):
        """Empty string handled correctly."""
        builder = MCPBuilder()

        result = builder.substitute_env_vars("")
        assert result == ""


class TestBuildServersJson:
    """Test building server configurations."""

    def test_build_empty_base_empty_templates(self):
        """Empty base and templates returns empty dict."""
        builder = MCPBuilder()

        result = builder.build_servers_json([], {}, {})
        assert result == {}

    def test_build_base_servers_only(self):
        """Build with base servers only."""
        builder = MCPBuilder()
        base = {"base1": {"command": "cmd"}}

        result = builder.build_servers_json([], {}, base)
        assert result == base

    def test_build_templates_only(self, sample_templates: dict[str, Any]):
        """Build with templates only."""
        builder = MCPBuilder()

        result = builder.build_servers_json(["server1"], sample_templates, None)
        assert "server1" in result
        assert result["server1"]["command"] == "cmd1"

    def test_build_base_and_templates_no_conflict(self, sample_templates: dict[str, Any]):
        """Build with base and templates (no name conflicts)."""
        builder = MCPBuilder()
        base = {"base1": {"command": "base_cmd"}}

        result = builder.build_servers_json(["server1"], sample_templates, base)
        assert "base1" in result
        assert "server1" in result

    def test_build_name_conflict_template_wins(self, sample_templates: dict[str, Any]):
        """Name conflict: template overrides base."""
        builder = MCPBuilder()
        base = {"server1": {"command": "old_cmd"}}

        result = builder.build_servers_json(["server1"], sample_templates, base)
        assert result["server1"]["command"] == "cmd1"  # From template

    def test_build_missing_template_warning(self, sample_templates: dict[str, Any]):
        """Missing template logs warning and skips."""
        builder = MCPBuilder()

        result = builder.build_servers_json(
            ["server1", "missing_server"], sample_templates, None
        )
        assert "server1" in result
        assert "missing_server" not in result

    def test_build_deep_copy_prevents_mutation(self, sample_templates: dict[str, Any]):
        """Deep copy prevents mutation of templates."""
        builder = MCPBuilder()

        result = builder.build_servers_json(["server1"], sample_templates, None)
        result["server1"]["command"] = "modified"

        assert sample_templates["server1"]["command"] == "cmd1"

    def test_build_verbose_output(self, sample_templates: dict[str, Any]):
        """Verbose mode outputs server additions."""
        builder = MCPBuilder(verbose=True)

        with patch("buildmcp.builder.console.print") as mock_print:
            builder.build_servers_json(["server1"], sample_templates, None)
            mock_print.assert_called()

    def test_build_template_with_name_field(self):
        """Template with 'name' field uses custom server key."""
        builder = MCPBuilder()
        templates = {
            "template-key": {
                "name": "custom-server-name",
                "command": "echo",
                "args": ["test"],
            }
        }

        result = builder.build_servers_json(["template-key"], templates, None)

        assert "custom-server-name" in result
        assert "template-key" not in result
        assert "name" not in result["custom-server-name"]
        assert result["custom-server-name"]["command"] == "echo"

    def test_build_base_server_with_name_field(self):
        """Base server with 'name' field uses custom server key."""
        builder = MCPBuilder()
        base = {
            "base-key": {
                "name": "renamed-base-server",
                "command": "base-cmd",
                "args": ["base"],
            }
        }

        result = builder.build_servers_json([], {}, base)

        assert "renamed-base-server" in result
        assert "base-key" not in result
        assert "name" not in result["renamed-base-server"]
        assert result["renamed-base-server"]["command"] == "base-cmd"

    def test_build_mixed_name_field(self):
        """Mix of servers with and without 'name' field."""
        builder = MCPBuilder()
        templates = {
            "standard": {"command": "cmd1"},
            "with-name": {"name": "custom-name", "command": "cmd2"},
        }

        result = builder.build_servers_json(["standard", "with-name"], templates, None)

        assert "standard" in result
        assert "custom-name" in result
        assert "with-name" not in result
        assert len(result) == 2

    def test_build_name_field_deep_copy(self):
        """Name field extraction doesn't mutate original template."""
        builder = MCPBuilder()
        templates = {
            "template-key": {
                "name": "custom-name",
                "command": "echo",
            }
        }

        builder.build_servers_json(["template-key"], templates, None)

        assert "name" in templates["template-key"]
        assert templates["template-key"]["name"] == "custom-name"

    def test_build_name_field_verbose_output(self):
        """Verbose mode shows custom name usage."""
        builder = MCPBuilder(verbose=True)
        templates = {
            "template-key": {
                "name": "custom-name",
                "command": "echo",
            }
        }

        with patch("buildmcp.builder.console.print") as mock_print:
            builder.build_servers_json(["template-key"], templates, None)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("custom-name" in str(call) for call in calls)


class TestLockFileOperations:
    """Test lock file loading and saving."""

    def test_load_lock_file_missing(self, tmp_path: Path):
        """Missing lock file loads empty dict."""
        builder = MCPBuilder(mcp_json=tmp_path / "mcp.json")

        builder.load_lock_file()
        assert builder._locked_hashes == {}

    def test_load_lock_file_valid(self, tmp_path: Path):
        """Valid lock file loads hashes."""
        config_file = tmp_path / "mcp.json"
        lock_file = tmp_path / "mcp.lock"
        lock_data = {"default": "abc123"}
        lock_file.write_text(json.dumps(lock_data))

        builder = MCPBuilder(mcp_json=config_file)
        builder.load_lock_file()

        assert builder._locked_hashes == lock_data

    def test_load_lock_file_corrupt(self, tmp_path: Path):
        """Corrupt lock file continues with warning."""
        config_file = tmp_path / "mcp.json"
        lock_file = tmp_path / "mcp.lock"
        lock_file.write_text("{invalid json")

        builder = MCPBuilder(mcp_json=config_file, verbose=True)
        builder.load_lock_file()

        assert builder._locked_hashes == {}

    def test_save_lock_file_empty_hashes(self, tmp_path: Path):
        """Empty hashes doesn't write lock file."""
        builder = MCPBuilder(mcp_json=tmp_path / "mcp.json")

        builder.save_lock_file()
        lock_file = tmp_path / "mcp.lock"
        assert not lock_file.exists()

    def test_save_lock_file_with_hashes(self, tmp_path: Path):
        """Save hashes to lock file."""
        config_file = tmp_path / "mcp.json"
        builder = MCPBuilder(mcp_json=config_file)
        builder._profile_hashes = {"default": "abc123"}

        builder.save_lock_file()

        lock_file = tmp_path / "mcp.lock"
        assert lock_file.exists()
        data = json.loads(lock_file.read_text())
        assert data == {"default": "abc123"}

    def test_save_lock_file_error_handling(self, tmp_path: Path):
        """Save error handled gracefully."""
        config_file = tmp_path / "readonly" / "mcp.json"
        builder = MCPBuilder(mcp_json=config_file)
        builder._profile_hashes = {"default": "abc123"}

        builder.save_lock_file()


class TestWriteTarget:
    """Test writing configurations to targets."""

    def test_write_dry_run(self):
        """Dry run prints without writing."""
        builder = MCPBuilder(dry_run=True)
        servers = {"server1": {"command": "cmd"}}

        with patch("buildmcp.builder.console.print") as mock_print:
            result = builder.write_target("target.json", servers)

            assert result is True
            mock_print.assert_called()

    def test_write_json_file(self, tmp_path: Path):
        """Write to JSON file."""
        target_file = tmp_path / "output.json"
        builder = MCPBuilder()
        servers = {"server1": {"command": "cmd"}}

        result = builder.write_target(str(target_file), servers)

        assert result is True
        assert target_file.exists()
        data = json.loads(target_file.read_text())
        assert "mcpServers" in data
        assert data["mcpServers"] == servers

    def test_write_shell_command_success(self):
        """Shell command write succeeds."""
        builder = MCPBuilder()
        servers = {"server1": {"command": "cmd"}}
        target = {"write": "cat > /dev/null"}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            result = builder.write_target(target, servers)

            assert result is True
            mock_run.assert_called_once()

    def test_write_shell_command_success_pattern(self):
        """Shell command with success pattern."""
        builder = MCPBuilder()
        servers = {"server1": {"command": "cmd"}}
        target = {"write": "echo 'test'"}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="Configuration saved successfully", stderr=""
            )

            result = builder.write_target(target, servers)

            assert result is True

    def test_write_shell_command_failure(self):
        """Shell command write fails."""
        builder = MCPBuilder()
        servers = {"server1": {"command": "cmd"}}
        target = {"write": "false"}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Error occurred"
            )

            result = builder.write_target(target, servers)

            assert result is False

    def test_write_invalid_target_spec(self):
        """Invalid target spec returns False."""
        builder = MCPBuilder()
        servers = {"server1": {"command": "cmd"}}

        result = builder.write_target(123, servers)  # Invalid spec
        assert result is False

    def test_write_exception_handling(self, tmp_path: Path):
        """Exception during write handled."""
        builder = MCPBuilder()
        servers = {"server1": {"command": "cmd"}}
        target_file = tmp_path / "test.json"

        with patch("buildmcp.builder.write_json_path", side_effect=OSError("error")):
            result = builder.write_target(str(target_file), servers)
            assert result is False

    def test_write_verbose_output(self):
        """Verbose mode captures output."""
        builder = MCPBuilder(verbose=True)
        servers = {"server1": {"command": "cmd"}}
        target = {"write": "echo 'output'"}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")

            builder.write_target(target, servers)

    def test_write_success_in_stderr(self):
        """Success message in stderr handled."""
        builder = MCPBuilder()
        servers = {"server1": {"command": "cmd"}}
        target = {"write": "test"}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Configuration saved successfully"
            )

            result = builder.write_target(target, servers)
            assert result is True


class TestProcessTarget:
    """Test complete profile processing flow."""

    def test_process_empty_servers(self, config_file: Path, sample_templates: dict):
        """Empty servers skips processing."""
        builder = MCPBuilder(mcp_json=config_file)

        result = builder.process_target(
            "profile1", [], "target.json", sample_templates, None
        )
        assert result is True

    def test_process_full_flow(self, tmp_path: Path, sample_templates: dict, mock_env):
        """Full processing: build → substitute → hash → write."""
        mock_env(ENV_VAR="value")
        target_file = tmp_path / "output.json"
        builder = MCPBuilder()

        result = builder.process_target(
            "profile1",
            ["server1"],
            str(target_file),
            sample_templates,
            None,
        )

        assert result is True
        assert "profile1" in builder._profile_hashes

    def test_process_force_flag(self, tmp_path: Path, sample_templates: dict):
        """Force flag bypasses hash check."""
        target_file = tmp_path / "output.json"
        builder = MCPBuilder(force=True)
        builder._locked_hashes = {"profile1": "matching_hash"}

        with patch.object(MCPBuilder, "build_servers_json", return_value={"s": {}}):
            with patch.object(MCPBuilder, "write_target", return_value=True) as mock_write:
                builder.process_target(
                    "profile1", ["server1"], str(target_file), sample_templates, None
                )

                mock_write.assert_called_once()

    def test_process_hash_match_skips_write(self, tmp_path: Path, sample_templates: dict, capsys):
        """Matching hash skips write."""
        builder = MCPBuilder()
        builder._locked_hashes = {"profile1": "abc123"}

        with patch.object(MCPBuilder, "build_servers_json", return_value={"s": {}}):
            with patch("buildmcp.builder.hash_json_data", return_value="abc123"):
                with patch.object(MCPBuilder, "write_target") as mock_write:
                    builder.process_target(
                        "profile1",
                        ["server1"],
                        "target.json",
                        sample_templates,
                        None,
                    )

                    mock_write.assert_not_called()
                    captured = capsys.readouterr()
                    assert "Skipping" in captured.err or "unchanged" in captured.err

    def test_process_hash_mismatch_writes(self, tmp_path: Path, sample_templates: dict):
        """Hash mismatch triggers write."""
        target_file = tmp_path / "output.json"
        builder = MCPBuilder()
        builder._locked_hashes = {"profile1": "old_hash"}

        with patch.object(MCPBuilder, "build_servers_json", return_value={"s": {}}):
            with patch("buildmcp.checksum.hash_json_data", return_value="new_hash"):
                with patch.object(MCPBuilder, "write_target", return_value=True) as mock_write:
                    builder.process_target(
                        "profile1",
                        ["server1"],
                        str(target_file),
                        sample_templates,
                        None,
                    )

                    mock_write.assert_called_once()

    def test_process_first_run_no_lock(self, tmp_path: Path, sample_templates: dict):
        """First run (no lock hash) triggers write."""
        target_file = tmp_path / "output.json"
        builder = MCPBuilder()

        with patch.object(MCPBuilder, "build_servers_json", return_value={"s": {}}):
            with patch.object(MCPBuilder, "write_target", return_value=True) as mock_write:
                builder.process_target(
                    "profile1", ["server1"], str(target_file), sample_templates, None
                )

                mock_write.assert_called_once()


class TestRun:
    """Test main run() orchestration."""

    def test_run_no_profiles(self, empty_config_file: Path):
        """No profiles defined shows warning."""
        builder = MCPBuilder(mcp_json=empty_config_file)

        with patch("buildmcp.builder.console.print") as mock_print:
            builder.run()
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("No profiles" in str(call) for call in calls)

    def test_run_no_targets(self, tmp_path: Path):
        """No targets defined shows warning."""
        config = {
            "mcpServers": {},
            "templates": {},
            "profiles": {"default": []},
            "targets": {},
        }
        config_file = tmp_path / "mcp.json"
        config_file.write_text(json.dumps(config))
        builder = MCPBuilder(mcp_json=config_file)

        with patch("buildmcp.builder.console.print") as mock_print:
            builder.run()
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("No targets" in str(call) for call in calls)

    def test_run_profile_without_target(self, tmp_path: Path):
        """Profile without target shows error."""
        config = {
            "mcpServers": {},
            "templates": {},
            "profiles": {"default": []},
            "targets": {"other": "file.json"},
        }
        config_file = tmp_path / "mcp.json"
        config_file.write_text(json.dumps(config))
        builder = MCPBuilder(mcp_json=config_file)

        builder.run()

    def test_run_complete_success(self, tmp_path: Path, mock_env):
        """Complete successful run."""
        mock_env(API_KEY="test_key")
        config = {
            "mcpServers": {},
            "templates": {"server1": {"command": "cmd"}},
            "profiles": {"default": ["server1"]},
            "targets": {"default": str(tmp_path / "output.json")},
        }
        config_file = tmp_path / "mcp.json"
        config_file.write_text(json.dumps(config))
        builder = MCPBuilder(mcp_json=config_file)

        builder.run()

        output_file = tmp_path / "output.json"
        assert output_file.exists()
