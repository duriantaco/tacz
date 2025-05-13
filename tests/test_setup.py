import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from tacz.config.setup import run_setup
from tacz.constants import LLMProviders

@pytest.fixture
def mock_questionary():
    """Mock questionary library."""
    with patch('tacz.config.setup.questionary') as mock_quest:
        mock_select = MagicMock()
        mock_text = MagicMock()
        mock_confirm = MagicMock()
        
        mock_quest.select.return_value = mock_select
        mock_quest.text.return_value = mock_text
        mock_quest.confirm.return_value = mock_confirm
        
        mock_select.ask.return_value = LLMProviders.OLLAMA
        mock_text.ask.return_value = "http://localhost:11434/v1"
        mock_confirm.ask.return_value = True
        
        mock_quest.Choice = MagicMock
        
        yield mock_quest

def test_run_setup(mock_questionary, temp_dir):
    """Test run_setup creates the config file with expected values."""
    with patch('pathlib.Path.home', return_value=temp_dir):
        config_path = temp_dir / ".taczrc"
        
        mock_questionary.select().ask.return_value = "ollama"
       
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["http://localhost:11434/v1", "llama3.1:8b", "24"]
        mock_questionary.text.return_value = text_mock
        
        confirm_mock = MagicMock()
        confirm_mock.ask.return_value = True
        mock_questionary.confirm.return_value = confirm_mock
        
        run_setup()
        
        assert config_path.exists()
        
        config_content = config_path.read_text()
        
        assert "LLM_PROVIDER=" in config_content
        assert "OLLAMA_" in config_content 
        assert "ENABLE_CACHE=" in config_content
        assert "CACHE_TTL_HOURS=" in config_content
        assert "ENABLE_HISTORY=" in config_content

def test_run_setup_existing_config(mock_questionary, temp_dir):
    """Test run_setup with an existing config file."""
    config_path = temp_dir / ".taczrc"
    existing_config = """
    LLM_PROVIDER=llamacpp
    LLAMACPP_URL=http://localhost:8080
    LLAMACPP_MODEL=custom-model
    ENABLE_CACHE=false
    CACHE_TTL_HOURS=12
    ENABLE_HISTORY=false
    """
    config_path.write_text(existing_config)
    
    with patch('pathlib.Path.home', return_value=temp_dir):
        mock_questionary.select().ask.return_value = "ollama"
        
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["http://localhost:11434/v1", "llama3.1:8b", "24"]
        mock_questionary.text.return_value = text_mock
        
        confirm_mock = MagicMock()
        confirm_mock.ask.return_value = True
        mock_questionary.confirm.return_value = confirm_mock
        
        with patch('tacz.config.setup.dotenv_values', return_value={
            "LLM_PROVIDER": "llamacpp",
            "LLAMACPP_URL": "http://localhost:8080",
            "LLAMACPP_MODEL": "custom-model",
            "ENABLE_CACHE": "false",
            "CACHE_TTL_HOURS": "12",
            "ENABLE_HISTORY": "false"
        }):
            run_setup()
        
        config_content = config_path.read_text()
        
        assert "LLM_PROVIDER=" in config_content