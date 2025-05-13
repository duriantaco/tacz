from typing import Optional, List
from pydantic import BaseModel, Field


class Command(BaseModel):
    command: str
    explanation: str
    is_dangerous: bool = False
    danger_explanation: Optional[str] = None
    requires_sudo: bool = False
    estimated_runtime: Optional[str] = None 

class CommandsResponse(BaseModel):
    commands: List[Command]
    is_valid: bool
    explanation_if_not_valid: Optional[str] = None
    platform_detected: str = "unknown"



class TemplateContext(BaseModel):
    template_name: str
    variables: dict
    description: str