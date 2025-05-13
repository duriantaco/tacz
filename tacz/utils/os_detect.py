import os
import platform
import shutil
from typing import Dict, Optional

def get_os_info() -> Dict[str, str]:
    """Get basic OS information"""
    system = platform.system()
    
    if system == "Windows":
        os_name = "Windows"
        if os.environ.get('PSModulePath'):
            shell = "PowerShell"
        else:
            shell = "CMD"
    elif system == "Darwin":
        os_name = "macOS"
        shell = os.environ.get('SHELL', '/bin/zsh').split('/')[-1]
    else:
        os_name = system
        shell = os.environ.get('SHELL', '/bin/bash').split('/')[-1]
    
    return {
        "os": os_name,
        "shell": shell,
        "path_sep": os.sep
    }

def get_available_tools() -> Dict[str, bool]:
    """Check if common tools are available"""
    return {
        "git": shutil.which("git") is not None,
        "docker": shutil.which("docker") is not None,
        "python": shutil.which("python") is not None or shutil.which("python3") is not None
    }