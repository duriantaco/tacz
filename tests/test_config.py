from pathlib import Path
from tacz.config import Config, get_tacz_dir, get_db_path

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