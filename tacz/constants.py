# tacz/constants.py
from enum import Enum

class LLMProviders(str, Enum):
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"

PROVIDER_DEFAULTS = {
    LLMProviders.OLLAMA: {
        "url": "http://localhost:11434",
        "model": "llama3.1:8b",
    },
    LLMProviders.LLAMACPP: {
        "url": "http://localhost:8080",
        "model": "",
    },
}

PROMPT = """
You are a terminal command expert. Generate commands for this request: {prompt}

System context:
{context}

INSTRUCTIONS:
1. Return a JSON object with command options
2. Make sure commands work on the specified platform
3. Keep explanations clear and concise
4. Mark dangerous commands appropriately

FORMAT YOUR RESPONSE AS JSON:
{{
  "is_valid": true,
  "commands": [
    {{
      "command": "the_actual_command",
      "explanation": "what this command does",
      "is_dangerous": false
    }}
  ]
}}

EXAMPLES:
Query: "list files"
Response: {{"is_valid":true,"commands":[{{"command":"ls -la","explanation":"List all files including hidden ones with details","is_dangerous":false}}]}}

Query: "remove everything"
Response: {{"is_valid":true,"commands":[{{"command":"rm -rf *","explanation":"Recursively delete all files in current directory","is_dangerous":true,"danger_reason":"Will permanently delete files without confirmation"}}]}}

Query: "invalid request"
Response: {{"is_valid":false,"explanation_if_not_valid":"I couldn't understand what command you're looking for."}}

Only return valid JSON, no additional text or markdown.
"""

DANGEROUS_PATTERNS = [
    (r"\brm\s+-rf\s+/?\S*",            "Recursive delete of files/directories"),
    (r"\bdd\s+if=",                    "Raw disk overwrite with dd"),
    (r":\s*\(\)\s*{\s*:\s*|:\s*&\s*};\s*", "Fork bomb"),
    (r"\bmkfs\.",                     "Formatting a filesystem"),
    (r"\bshutdown\b",                 "System shutdown"),
    (r"\breboot\b",                   "System reboot"),
    (r"\bpoweroff\b",                 "Power off the machine"),
    (r"\bhalt\b",                     "Halt the machine"),
    (r"\bsystemctl\s+disable\b",      "Disabling a system service"),
    (r"\bchown\s+-R\s+",              "Recursive ownership change"),
    (r"(^|\s)sudo\s+",                "Elevation to super-user"),
    (r"\bchmod\s+7[0-7][0-7]\b",      "World-writable permission change"),
    (r"\b:(){:|:&};:\b",              "Alternate fork-bomb syntax"),
    (r"\bfind\s+.*\bdelete\b",        "File deletion with find"),
    (r"\bcp\s+-R\s+",                 "Recursive copy"),
    (r"\bmv\s+-R\s+",                 "Recursive move"),
    (r"\bexport\s+PATH\s*=\s*.*\b",   "Modifying PATH variable"),
    (r"\bexport\s+LD_PRELOAD\s*=\s*.*\b", "Modifying LD_PRELOAD variable"),
    (r"\bexport\s+LD_LIBRARY_PATH\s*=\s*.*\b", "Modifying LD_LIBRARY_PATH variable"),
    (r".*;.*rm\s+", "Command contains deletion after separator (;)"),
    (r".*&&.*rm\s+",                    "Command contains deletion after logical AND (&&)"),
    (r".*\|\|.*rm\s+",                  "Command contains deletion after logical OR (||)"),
    (r".*`.*`",                         "Command contains command substitution (backticks)"),
    (r".*\$\(.*\)",                     "Command contains command substitution ($(command))"),
    (r".*[><]\s*/etc/",                 "Command redirects to system configuration files"),
    (r".*[><]\s*/dev/",                 "Command redirects to device files"),
    (r"\brm\s+(?!-i\b).*", "File deletion without confirmation flag (-i)"),
    (r"\brm\s+-[a-zA-Z]*[fF][a-zA-Z]*\s+", "Forced deletion with rm -f"),
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+", "Recursive deletion with rm -r"),
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*\s+", "Dangerous recursive forced deletion"),
    (r"\brm\s+-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*\s+", "Dangerous recursive forced deletion"),
]