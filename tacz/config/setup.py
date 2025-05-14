import questionary
from pathlib import Path
from typing import Dict
from dotenv import dotenv_values
import logging
from tacz.constants import LLMProviders, PROVIDER_DEFAULTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_setup() -> None:
    config_path = Path.home() / ".taczrc"

    existing_values: Dict[str, str] = {}
    if config_path.exists():
        existing_values = dotenv_values(config_path)  # type: ignore[assignment]

    logger.info("🚀 Welcome to Tacz! Let's set up your local command assistant.")

    provider_choices = [
        questionary.Choice(
            title="Ollama",
            value=LLMProviders.OLLAMA,
            description="Easy to use, popular (recommended)",
        ),
        questionary.Choice(
            title="llama.cpp server",
            value=LLMProviders.LLAMACPP,
            description="Lightweight, fast, customizable",
        ),
    ]

    selected_provider = questionary.select(
        "Choose your local LLM provider:",
        choices=provider_choices,
        default=existing_values.get("LLM_PROVIDER", LLMProviders.OLLAMA),
    ).ask()

    config_values: Dict[str, str] = {"LLM_PROVIDER": selected_provider}

    url_key = f"{selected_provider.upper()}_URL"
    default_url = PROVIDER_DEFAULTS[selected_provider]["url"]
    provider_url = questionary.text(
        f"{selected_provider.title()} server URL:",
        default=existing_values.get(url_key, default_url),
    ).ask()
    config_values[url_key] = provider_url

    model_key = f"{selected_provider.upper()}_MODEL"
    default_model = PROVIDER_DEFAULTS[selected_provider]["model"]

    if selected_provider == LLMProviders.OLLAMA:
        model_choices = [
            questionary.Choice(title="llama3.1:8b", value="llama3.1:8b", description="Recommended"),
            questionary.Choice(title="phi3:mini", value="phi3:mini", description="Fastest, smallest"),
            questionary.Choice(title="mistral:latest", value="mistral:latest", description="Good for creative tasks"),
            questionary.Choice(title="custom", value="custom", description="Enter custom model name"),
        ]

        model_choice = questionary.select(
            "Choose Ollama model:",
            choices=model_choices,
            default=existing_values.get(model_key, "llama3.1:8b"),
        ).ask()

        if model_choice == "custom":
            model_name = questionary.text(
                "Enter model name:",
                default=existing_values.get(model_key, default_model),
            ).ask()
        else:
            model_name = model_choice
    else:
        model_name = questionary.text(
            "Model identifier (loaded when starting server):",
            default=existing_values.get(model_key, ""),
        ).ask()

    config_values[model_key] = model_name

    enable_cache = questionary.confirm(
        "Enable command caching?",
        default=existing_values.get("ENABLE_CACHE", "true") == "true",
    ).ask()

    cache_ttl = questionary.text(
        "Cache TTL (hours):",
        default=existing_values.get("CACHE_TTL_HOURS", "24"),
        validate=lambda x: x.isdigit(),
    ).ask()

    enable_history = questionary.confirm(
        "Enable command history?",
        default=existing_values.get("ENABLE_HISTORY", "true") == "true",
    ).ask()

    enable_safety_checks = questionary.confirm(
        "Enable safety checks?",
        default=existing_values.get("ENABLE_SAFETY_CHECKS", "true") == "true",
        help="Enable safety checks for dangerous commands.",
    ).ask()

    config_values.update(
        {
            "ENABLE_CACHE": str(enable_cache).lower(),
            "CACHE_TTL_HOURS": cache_ttl,
            "ENABLE_HISTORY": str(enable_history).lower(),
            "ENABLE_SAFETY_CHECKS": str(enable_safety_checks).lower(),}
    )

    config_content = "\n".join(f"{k}={v}" for k, v in config_values.items()) + "\n"
    config_path.write_text(config_content)

    logger.info("\n✅ Configuration saved!")

    if selected_provider == LLMProviders.OLLAMA:
        logger.info("\n💡 Next steps:")
        logger.info("1. Start Ollama: ollama serve")
        logger.info(f"2. Pull model: ollama pull {model_name}")
        logger.info("3. Test: tacz 'list files'")
    else:
        port = config_values["LLAMACPP_URL"].split(":")[-1].split("/")[0]
        logger.info("\n💡 Next steps:")
        logger.info("1. Download model from HuggingFace (GGUF format)")
        logger.info(f"2. Start server: ./server -m model.gguf -p {port}")
        logger.info("3. Test: tacz 'list files'")