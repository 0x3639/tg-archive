"""Tests for configuration validation."""
import pytest

from tgarchive import validate_path, validate_config, get_config


class TestValidatePath:
    """Tests for validate_path function."""

    def test_blocks_path_traversal(self):
        """Path traversal sequences should be rejected."""
        with pytest.raises(ValueError, match="Path traversal"):
            validate_path("../etc/passwd", "test_path")

    def test_blocks_nested_path_traversal(self):
        """Nested path traversal should be rejected."""
        with pytest.raises(ValueError, match="Path traversal"):
            validate_path("foo/../../etc/passwd", "test_path")

    def test_blocks_absolute_paths(self):
        """Absolute paths should be rejected."""
        with pytest.raises(ValueError, match="Absolute paths"):
            validate_path("/etc/passwd", "test_path")

    def test_allows_valid_relative_path(self):
        """Valid relative paths should be allowed."""
        result = validate_path("media/photos", "test_path")
        assert result == "media/photos"

    def test_allows_simple_filename(self):
        """Simple filenames should be allowed."""
        result = validate_path("test.jpg", "test_path")
        assert result == "test.jpg"

    def test_allows_nested_path(self):
        """Nested relative paths should be allowed."""
        result = validate_path("a/b/c/d.txt", "test_path")
        assert result == "a/b/c/d.txt"


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_requires_api_id_when_credentials_required(self):
        """Missing api_id should raise error when credentials required."""
        config = {"api_hash": "test", "group": "test"}
        with pytest.raises(ValueError, match="api_id"):
            validate_config(config, require_credentials=True)

    def test_requires_api_hash_when_credentials_required(self):
        """Missing api_hash should raise error when credentials required."""
        config = {"api_id": "123", "group": "test"}
        with pytest.raises(ValueError, match="api_hash"):
            validate_config(config, require_credentials=True)

    def test_requires_group_when_credentials_required(self):
        """Missing group should raise error when credentials required."""
        config = {"api_id": "123", "api_hash": "test"}
        with pytest.raises(ValueError, match="group"):
            validate_config(config, require_credentials=True)

    def test_allows_missing_credentials_when_not_required(self):
        """Missing credentials should be allowed when not required."""
        config = {"fetch_wait": 5, "fetch_batch_size": 100, "per_page": 50}
        # Should not raise
        validate_config(config, require_credentials=False)

    def test_rejects_negative_fetch_wait(self):
        """Negative fetch_wait should be rejected."""
        config = {"fetch_wait": -1}
        with pytest.raises(ValueError, match="fetch_wait"):
            validate_config(config)

    def test_rejects_invalid_fetch_wait_type(self):
        """Non-numeric fetch_wait should be rejected."""
        config = {"fetch_wait": "invalid"}
        with pytest.raises(ValueError, match="fetch_wait"):
            validate_config(config)

    def test_rejects_invalid_fetch_batch_size(self):
        """Non-integer fetch_batch_size should be rejected."""
        config = {"fetch_batch_size": "invalid"}
        with pytest.raises(ValueError, match="fetch_batch_size"):
            validate_config(config)

    def test_rejects_zero_fetch_batch_size(self):
        """Zero fetch_batch_size should be rejected."""
        config = {"fetch_batch_size": 0}
        with pytest.raises(ValueError, match="fetch_batch_size"):
            validate_config(config)

    def test_rejects_invalid_per_page(self):
        """Invalid per_page should be rejected."""
        config = {"per_page": -10}
        with pytest.raises(ValueError, match="per_page"):
            validate_config(config)

    def test_validates_path_configs(self):
        """Path configurations should be validated."""
        config = {"media_dir": "../escape"}
        with pytest.raises(ValueError, match="Path traversal"):
            validate_config(config)

    def test_accepts_valid_config(self, sample_config):
        """Valid configuration should pass validation."""
        # Should not raise
        validate_config(sample_config, require_credentials=True)


class TestGetConfig:
    """Tests for get_config function."""

    def test_loads_config_file(self, temp_config_file):
        """Config file should be loaded correctly."""
        config = get_config(temp_config_file)
        assert config["api_id"] == "123456"
        assert config["group"] == "test_group"

    def test_merges_with_defaults(self, temp_config_file):
        """Config should be merged with default values."""
        config = get_config(temp_config_file)
        # Check a default value that wasn't in the test config
        assert "telegram_url" in config

    def test_validates_on_load(self):
        """Config should be validated when loaded."""
        import tempfile
        import yaml

        # Create config with invalid path
        invalid_config = {"media_dir": "../escape"}
        with tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False) as f:
            yaml.dump(invalid_config, f)
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="Path traversal"):
                get_config(config_path)
        finally:
            import os
            os.unlink(config_path)
