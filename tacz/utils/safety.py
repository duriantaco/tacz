import re
from typing import Tuple, List
from tacz.constants import DANGEROUS_PATTERNS

def is_dangerous_command(command: str) -> Tuple[bool, str]:
    command_clean = command.strip()
    
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command_clean, re.IGNORECASE):
            return True, reason
    
    if _contains_destructive_intent(command_clean):
        return True, "Command appears to have destructive intent"
    
    return False, ""

def _contains_destructive_intent(command: str) -> bool:
    """Check for potentially destructive patterns not caught by regex"""
    destructive_indicators = [
        "format",
        "erase",
        "wipe",
        "destroy",
        "delete all",
        "remove all",
    ]
    
    command_lower = command.lower()
    for indicator in destructive_indicators:
        if indicator in command_lower:
            return True
    
    return False

def sanitize_command(command: str) -> str:
    """Sanitize command by removing potentially dangerous elements"""
    command = re.sub(r'[;&|].*$', '', command)
    
    # remove excessive wildcards
    command = re.sub(r'\*{2,}', '*', command)
    
    return command.strip()

class CommandValidator:
    def __init__(self):
        self.whitelist_commands = {
            'ls', 'cd', 'pwd', 'echo', 'cat', 'less', 'more', 'grep',
            'find', 'locate', 'which', 'man', 'info', 'help', 'history',
            'date', 'cal', 'uptime', 'whoami', 'id', 'groups', 'ps',
            'top', 'htop', 'df', 'du', 'free', 'netstat', 'ss',
        }
    
    def is_safe_command(self, command: str) -> bool:
        base_command = command.split()[0] if command else ""
        return base_command in self.whitelist_commands
    
    def validate_and_suggest(self, command: str) -> Tuple[bool, List[str]]:
        is_dangerous, reason = is_dangerous_command(command)
        
        if is_dangerous:
            suggestions = self._get_safer_alternatives(command)
            return False, suggestions
        
        return True, []
    
    def _get_safer_alternatives(self, command: str) -> List[str]:
        alternatives = []
        
        if "rm -rf" in command:
            alternatives.append("# Consider using 'rm -i' for interactive deletion")
            alternatives.append("# Or use 'trash' command if available for safer deletion")
        
        if "chmod 777" in command:
            alternatives.append("# Consider using more restrictive permissions like 755 or 644")
            alternatives.append("# Use principle of least privilege")
        
        return alternatives