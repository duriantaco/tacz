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

def test_run_setup_llamacpp_provider(mock_questionary, temp_dir):
    """Test run_setup with llama.cpp provider."""
    with patch('pathlib.Path.home', return_value=temp_dir):
        config_path = temp_dir / ".taczrc"
        
        mock_questionary.select().ask.return_value = "llamacpp"
        
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["http://localhost:8080", "my-model.gguf", "24"]
        mock_questionary.text.return_value = text_mock
        
        confirm_mock = MagicMock()
        confirm_mock.ask.return_value = True
        mock_questionary.confirm.return_value = confirm_mock
        
        with patch('builtins.print') as mock_print:
            run_setup()
            
            port_message_found = False
            for call in mock_print.call_args_list:
                call_str = str(call)
                if "port" in call_str.lower() or "8080" in call_str:
                    port_message_found = True
                    break
            
            assert port_message_found, "Port 8080 should be mentioned in next steps"
        
        assert config_path.exists()
        config_content = config_path.read_text()
        
        assert "LLM_PROVIDER=llamacpp" in config_content
        assert "LLAMACPP_URL=http://localhost:8080" in config_content
        assert "LLAMACPP_MODEL=my-model.gguf" in config_content

def test_run_setup_ollama_custom_model(mock_questionary, temp_dir):
    """Test run_setup with Ollama and custom model selection."""
    with patch('pathlib.Path.home', return_value=temp_dir):
        config_path = temp_dir / ".taczrc"
        
        mock_questionary.select().ask.side_effect = ["ollama", "custom"]
        
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["http://localhost:11434/v1", "my-custom-model:latest", "24"]
        mock_questionary.text.return_value = text_mock
        
        confirm_mock = MagicMock()
        confirm_mock.ask.return_value = True
        mock_questionary.confirm.return_value = confirm_mock
        
        run_setup()
        
        assert config_path.exists()
        config_content = config_path.read_text()
        
        assert "OLLAMA_MODEL=my-custom-model:latest" in config_content

def test_run_setup_cache_ttl_validation(mock_questionary, temp_dir):
    """Test cache TTL validation in run_setup."""
    with patch('pathlib.Path.home', return_value=temp_dir):
        mock_questionary.select().ask.return_value = "ollama"
        
        text_mock = MagicMock()
        text_responses = ["http://localhost:11434/v1", "llama3.1:8b"]
        text_mock.ask.side_effect = text_responses
        mock_questionary.text.return_value = text_mock
        
        ttl_text_mock = MagicMock()
        ttl_text_mock.ask.return_value = "48"
        
        original_text = mock_questionary.text
        
        def mock_text_factory(*args, **kwargs):
            if 'validate' in kwargs:
                validator = kwargs['validate']
                assert not validator("abc")
                assert validator("123")
                return ttl_text_mock
            return text_mock
            
        mock_questionary.text = mock_text_factory
        
        confirm_mock = MagicMock()
        confirm_mock.ask.return_value = True
        mock_questionary.confirm.return_value = confirm_mock
        
        run_setup()
        
        config_content = (temp_dir / ".taczrc").read_text()
        assert "CACHE_TTL_HOURS=48" in config_content
        
        mock_questionary.text = original_text

def test_run_setup_toggle_features(mock_questionary, temp_dir):
    """Test run_setup with features toggled off."""
    with patch('pathlib.Path.home', return_value=temp_dir):
        config_path = temp_dir / ".taczrc"
        
        mock_questionary.select().ask.return_value = "ollama"
        
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["http://localhost:11434/v1", "llama3.1:8b", "24"]
        mock_questionary.text.return_value = text_mock
        
        confirm_mock = MagicMock()
        confirm_mock.ask.side_effect = [False, False, False]
        mock_questionary.confirm.return_value = confirm_mock
        
        run_setup()
        
        assert config_path.exists()
        config_content = config_path.read_text()
        
        assert "ENABLE_CACHE=false" in config_content
        assert "ENABLE_HISTORY=false" in config_content
        assert "ENABLE_SAFETY_CHECKS=false" in config_content

def test_run_setup_help_text(mock_questionary, temp_dir):
    """Test help text for safety checks in run_setup."""
    with patch('pathlib.Path.home', return_value=temp_dir):
        mock_questionary.select().ask.return_value = "ollama"
        
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["http://localhost:11434/v1", "llama3.1:8b", "24"]
        mock_questionary.text.return_value = text_mock
        
        confirm_mock = MagicMock()
        confirm_mock.ask.return_value = True
        mock_questionary.confirm.return_value = confirm_mock
        
        with patch.object(mock_questionary, 'confirm') as mock_confirm_factory:
            mock_confirm_factory.return_value = confirm_mock
            run_setup()
            
            safety_call = [call for call in mock_confirm_factory.call_args_list 
                          if "safety" in str(call).lower()]
            assert safety_call
            assert "help" in safety_call[0][1]
            assert "Enable safety checks for dangerous commands" in safety_call[0][1]["help"]