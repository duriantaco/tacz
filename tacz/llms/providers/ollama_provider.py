# tacz/llms/providers/ollama_provider.py
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from openai import OpenAI

from tacz.config import config
from tacz.llms.types import CommandsResponse, Command
from tacz.utils.command_db import CommandDatabase
from tacz.utils.safety import is_dangerous_command
from tacz.constants import PROMPT
from tacz.config import get_db_path

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

            db_results = self.db.search(prompt, limit=3)

            if db_results and len(db_results) >= 1:
                commands = []
                for result in db_results:
                    commands.append(Command(
                        command=result["command"],
                        explanation=result["explanation"],
                        is_dangerous=bool(result["dangerous"]),
                        danger_explanation=result["danger_reason"]
                    ))
                
                platform_detected = next(
                    (line for line in context.split("\n") if "Platform:" in line), 
                    "unknown"
                ).replace("Platform: ", "")
                
                return CommandsResponse(
                    commands=commands,
                    is_valid=True,
                    platform_detected=platform_detected
                )
            
            full_prompt = self.prompt_template.format(prompt=prompt, context=context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.3,
                max_tokens=1000,
                timeout=60.0
            )
            
            content = response.choices[0].message.content
            
            response_data = self._parse_response(content)
            
            response_data = self._enhance_with_safety_checks(response_data)
            
            platform_detected = next(
                (line for line in context.split("\n") if "Platform:" in line), 
                "unknown"
            ).replace("Platform: ", "")
            
            commands_response = CommandsResponse(
                platform_detected=platform_detected, 
                **response_data
            )
            
            if commands_response.is_valid and commands_response.commands:
                for cmd in commands_response.commands:
                    self.db.add_command(
                        command=cmd.command,
                        explanation=cmd.explanation,
                        dangerous=cmd.is_dangerous,
                        danger_reason=cmd.danger_explanation
                    )
            
            if display_callback and commands_response.commands:
                display_cmds = [{"cmd": cmd.command, "explanation": cmd.explanation} 
                               for cmd in commands_response.commands]
                display_callback(display_cmds)
            
            return commands_response
            
        except Exception as e:
            import traceback
            print(f"Error generating commands: {e}")
            traceback.print_exc()
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