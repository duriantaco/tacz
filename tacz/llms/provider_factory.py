from tacz.config import config
from tacz.constants import LLMProviders


def get_inference_provider():
    """Get the configured inference provider"""
    provider_type = config.llm_provider
    
    if provider_type == LLMProviders.OLLAMA:
        from tacz.llms.providers.ollama_provider import OllamaProvider
        return OllamaProvider()    
    else:
        raise ValueError(f"Unknown provider: {provider_type}")