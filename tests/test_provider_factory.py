import pytest
from unittest.mock import patch, MagicMock

from tacz.llms.provider_factory import get_inference_provider
from tacz.constants import LLMProviders

@patch('tacz.llms.provider_factory.config')
def test_get_inference_provider_ollama(mock_config):
    mock_config.vals = {'LLM_PROVIDER': 'ollama'}
    mock_config.llm_provider = LLMProviders.OLLAMA
    
    with patch('tacz.llms.providers.ollama_provider.OllamaProvider') as mock_provider:
        mock_instance = MagicMock()
        mock_provider.return_value = mock_instance
        
        provider = get_inference_provider()
        
        assert provider == mock_instance
        mock_provider.assert_called_once()

@patch('tacz.llms.provider_factory.config')
def test_get_inference_provider_invalid(mock_config):
    """Test get_inference_provider with invalid provider type."""
    mock_config.vals = {'LLM_PROVIDER': 'invalid_provider'}
    mock_config.llm_provider = 'invalid_provider'
    
    with pytest.raises(ValueError) as excinfo:
        get_inference_provider()
    
    assert "Unknown provider" in str(excinfo.value)