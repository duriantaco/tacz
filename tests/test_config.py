from pathlib import Path
from tacz.config import Config, get_tacz_dir, get_db_path
import pytest
from unittest.mock import patch, MagicMock
import os

def test_config_initialization(mock_config):
    """Test that Config initializes properly."""
    config = Config()
    assert config.config_path.name == ".taczrc"
    assert config.keyring_service == "tacz"

def test_get_tacz_dir(mock_config, temp_dir):
    """Test get_tacz_dir creates and returns the correct directory."""
    tacz_dir = temp_dir / ".tacz"
    if tacz_dir.exists():
        tacz_dir.rmdir()
    
    config = Config()
    dir_path = config.get_tacz_dir()
    
    assert dir_path.exists()
    assert dir_path.is_dir()
    assert dir_path == tacz_dir

def test_get_db_path(mock_config, temp_dir):
    """Test get_db_path returns the correct path."""
    config = Config()
    db_path = config.get_db_path()
    
    expected_path = temp_dir / ".tacz" / "commands.db"
    assert db_path == expected_path

def test_ollama_base_url(mock_config):
    """Test ollama_base_url property."""
    config = Config()
    assert config.ollama_base_url == "http://localhost:11434/v1"

def test_ollama_model(mock_config):
    """Test ollama_model property."""
    config = Config()
    assert config.ollama_model == "test-model"

def test_cache_ttl_hours(mock_config):
    """Test cache_ttl_hours property."""
    config = Config()
    assert config.cache_ttl_hours == 24

def test_enable_cache(mock_config):
    """Test enable_cache property."""
    config = Config()
    assert config.enable_cache is True

def test_enable_history(mock_config):
    """Test enable_history property."""
    config = Config()
    assert config.enable_history is True

def test_global_helpers(mock_config, temp_dir):
    """Test global helper functions."""
    expected_tacz_dir = temp_dir / ".tacz"
    expected_db_path = expected_tacz_dir / "commands.db"
    
    assert get_tacz_dir() == expected_tacz_dir
    assert get_db_path() == expected_db_path

def test_get_secure_value_from_env(mock_config):
    """Test get_secure_value returns value from environment variable."""
    with patch.dict(os.environ, {"TEST_VAR": "env_value"}):
        config = Config()
        value = config.get_secure_value("test_key", "TEST_VAR")
        assert value == "env_value"

def test_get_secure_value_from_keyring(mock_config):
    """Test get_secure_value returns value from keyring."""
    with patch.dict(os.environ, {}, clear=True), \
         patch('keyring.get_password', return_value="keyring_value"):
        config = Config()
        value = config.get_secure_value("test_key", "TEST_VAR")
        assert value == "keyring_value"

def test_get_secure_value_from_config(mock_config):
    """Test get_secure_value returns value from config file."""
    with patch.dict(os.environ, {}, clear=True), \
         patch('keyring.get_password', return_value=None):
        config = Config()
        config.vals = {"TEST_VAR": "config_value"}
        value = config.get_secure_value("test_key", "TEST_VAR")
        assert value == "config_value"

def test_get_secure_value_not_found(mock_config):
    """Test get_secure_value returns None when value is not found."""
    with patch.dict(os.environ, {}, clear=True), \
         patch('keyring.get_password', return_value=None):
        config = Config()
        config.vals = {}
        value = config.get_secure_value("test_key", "TEST_VAR")
        assert value is None

def test_get_secure_value_keyring_exception(mock_config):
    """Test get_secure_value handles keyring exceptions gracefully."""
    with patch.dict(os.environ, {}, clear=True), \
         patch('keyring.get_password', side_effect=Exception("Keyring error")):
        config = Config()
        config.vals = {"TEST_VAR": "config_value"}
        value = config.get_secure_value("test_key", "TEST_VAR")
        assert value == "config_value"

def test_cache_ttl_hours_invalid_value(mock_config):
    """Test cache_ttl_hours handles non-integer values."""
    config = Config()
    config.vals = {"CACHE_TTL_HOURS": "invalid"}
    assert config.cache_ttl_hours == 24

def test_default_values(mock_config):
    """Test default values when config is empty."""
    config = Config()
    config.vals = {}
    
    assert config.ollama_base_url == "http://localhost:11434/v1"
    assert config.ollama_model == "llama3.1:8b"
    assert config.cache_ttl_hours == 24
    assert config.enable_cache is True
    assert config.enable_history is True

def test_property_values_from_config(mock_config):
    """Test properties read values from config."""
    config = Config()
    config.vals = {
        "OLLAMA_BASE_URL": "http://custom:1234",
        "OLLAMA_MODEL": "custom-model",
        "CACHE_TTL_HOURS": "48",
        "ENABLE_CACHE": "false",
        "ENABLE_HISTORY": "false"
    }
    
    assert config.ollama_base_url == "http://custom:1234"
    assert config.ollama_model == "custom-model"
    assert config.cache_ttl_hours == 48
    assert config.enable_cache is False
    assert config.enable_history is False