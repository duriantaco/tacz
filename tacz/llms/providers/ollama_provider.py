# tacz/llms/providers/ollama_provider.py
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from openai import OpenAI
import logging 

from tacz.config import config
from tacz.llms.types import CommandsResponse, Command
from tacz.utils.command_db import CommandDatabase
from tacz.utils.safety import is_dangerous_command
from tacz.constants import PROMPT
from tacz.config import get_db_path
import time
from rich.console import Console

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

class OllamaProvider:
    def __init__(self):
        if not config.ollama_base_url:
            raise ValueError("OLLAMA_BASE_URL must be set.")
        if not config.ollama_model:
            raise ValueError("OLLAMA_MODEL must be set.")
        
        self.client = OpenAI(base_url=config.ollama_base_url, api_key="ollama")
        self.model = config.ollama_model
        
        self.db = CommandDatabase(get_db_path())
        self.prompt_template = PROMPT
    
    def get_options(self, prompt: str, context: str, display_callback=None) -> Optional[CommandsResponse]:
        try:
            start = time.perf_counter()
            with console.status("Searching...", spinner="dots"):
                db_results = self.db.search(prompt, limit=3)
            elapsed = time.perf_counter() - start

            logger.info("DB Search for '%s' returned %d results in %.2fs", prompt, len(db_results), elapsed)
            for r in db_results:
                logger.debug("  - %s | tags: %s", r.get("command", "N/A"), r.get("tags", []))

            commands = []
            for result in db_results:
                commands.append(Command(
                    command=result["command"],
                    explanation=result["explanation"],
                    is_dangerous=bool(result["dangerous"]),
                    danger_explanation=result.get("danger_reason", "")
                ))
            
            platform_detected = next(
                (line for line in context.split("\n") if "Platform:" in line), 
                "unknown"
            ).replace("Platform: ", "")
            
            return CommandsResponse(
                commands=commands,
                is_valid=True if commands else False,
                platform_detected=platform_detected,
                explanation_if_not_valid="No matching commands found in database." if not commands else None
            )
        except Exception as e:
            logger.error("Error during database search: %s", e, exc_info=True)
            return None
        
    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass
        
        json_match = re.search(r'{.*}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        code_block_match = re.search(r'```(?:bash|shell|zsh|)?\s*(.*?)\s*```', content, re.DOTALL)
        if code_block_match:
            command = code_block_match.group(1).strip()
            explanation = re.sub(r'```.*?```\s*', '', content, flags=re.DOTALL).strip()
            
            return {
                "commands": [{
                    "command": command,
                    "explanation": explanation,
                    "is_dangerous": False
                }],
                "is_valid": True
            }
        
        lines = content.strip().split('\n')
        if lines and len(lines[0]) > 3 and not lines[0].startswith('{'):
            command = lines[0].strip()
            explanation = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
            
            return {
                "commands": [{
                    "command": command,
                    "explanation": explanation,
                    "is_dangerous": False
                }],
                "is_valid": True
            }
        
        return {
            "commands": [],
            "is_valid": False,
            "explanation_if_not_valid": "Could not understand the model's response"
        }
    
    def _enhance_with_safety_checks(self, response_data: dict) -> dict:
        if "commands" in response_data:
            for cmd in response_data["commands"]:
                if "command" in cmd:
                    is_dangerous, reason = is_dangerous_command(cmd["command"])
                    if is_dangerous:
                        cmd["is_dangerous"] = True
                        cmd["danger_explanation"] = cmd.get("danger_explanation", "") + f" {reason}"
        
        return response_data
    
    def add_to_favorites(self, command: str, description: str):
        self.db.add_command(
            command=command,
            explanation=description,
            category="favorite",
            dangerous=False
        )
    
    def get_command_history(self, query: str = "", limit: int = 10):
        if query:
            return self.db.search_history(query, limit)
        return self.db.get_history(limit=limit)