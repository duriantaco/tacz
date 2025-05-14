# tacz/main.py
import sys
import os
from pathlib import Path
from subprocess import run as run_command
import dotenv
import pyperclip
import questionary
import shutil
import re
import atexit
import logging

from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

from tacz.config.setup import run_setup
from tacz.llms.providers.ollama_provider import OllamaProvider
from tacz.utils.os_detect import get_os_info, get_available_tools
from tacz.utils.safety import has_command_chaining, is_rm_command, sanitize_command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_provider_instance = None

def get_provider():
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = OllamaProvider()
    return _provider_instance

def cleanup():
    """Clean up resources before exit"""
    global _provider_instance
    if _provider_instance is not None:
        _provider_instance.db.close()

atexit.register(cleanup)

def setup():
    run_setup()

def show_history():
    try:
        provider = get_provider()
        history = provider.get_command_history(limit=20)
        
        if not history:
            logger.info("No command history available.")
            return
        
        table = Table(title="Recent Commands")
        table.add_column("Time", style="cyan")
        table.add_column("Query", style="green")
        table.add_column("Command", style="yellow")
        table.add_column("Status", style="magenta")
        
        for entry in history:
            status = "✓" if entry.get("executed") else "○"
            if entry.get("success") is False:
                status = "✗"
            
            timestamp = entry.get("timestamp", "")
            if len(timestamp) > 19:
                timestamp = timestamp[:19]
                
            table.add_row(
                timestamp,
                entry.get("query", "")[:50],
                entry.get("command", "")[:50],
                status
            )
        
        console = Console()
        console.print(table)
    except Exception as e:
        logger.error("Error showing history: %s", e, exc_info=True)

def show_favorites():
    try:
        provider = OllamaProvider()
        favorites = provider.db.search("favorite", limit=20)
        
        if not favorites:
            logger.info("No favorite commands saved.")
            return
        
        table = Table(title="Favorite Commands")
        table.add_column("Command", style="yellow")
        table.add_column("Description", style="green")
        table.add_column("Popularity", style="cyan")
        
        for fav in favorites:
            table.add_row(
                fav.get("command", ""),
                fav.get("explanation", ""),
                str(fav.get("popularity", 0))
            )
        
        console = Console()
        console.print(table)
    except Exception as e:
        logger.error("Error showing favorites: %s", e, exc_info=True)

def get_env_context() -> str:
    os_info = get_os_info()
    tools = get_available_tools()
    
    platform_detected = f"{os_info['os']} ({os_info['shell']})"
    os_str = f"Platform: {platform_detected}"
    shell_str = f"Shell: {os_info['shell']}"
    python_version = f"Python: {sys.version.split()[0]}"
    
    try:
        cwd = f"Directory: {os.getcwd()}"
    except:
        cwd = "Directory: unknown"
    
    git_info = ""
    if tools["git"]:
        try:
            result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                               capture_output=True, text=True)
            if result.returncode == 0:
                git_info = f"Git Branch: {result.stdout.strip()}"
        except:
            pass
    
    context_parts = [os_str, shell_str, python_version, cwd, f"Path Separator: {os_info['path_sep']}"]
    if git_info:
        context_parts.append(git_info)
        
    return "\n".join(context_parts)

def edit_command(command: str) -> str:
    edited = questionary.text(
        "Edit command (press Enter to keep as-is):",
        default=command
    ).ask()
    return edited if edited else command

def break_down_command(command: str) -> dict:
    if not command:
        return {"command": "", "args": []}
        
    if command.count(" ") <= 1 and not any(op in command for op in "|;&><"):
        parts = command.split()
        if not parts:
            return {"command": "", "args": []}
        if len(parts) == 1:
            return {"command": parts[0], "args": []}

        arg = parts[1]
        arg_type = "option" if arg.startswith("-") else "value"
        return {"command": parts[0], "args": [{"value": arg, "type": arg_type}]}
    
    if '|' not in command and ';' not in command and '&&' not in command and '||' not in command:
        parts = command.split()
        if not parts:
            return {"command": "", "args": []}
        
        base_command = parts[0]
        args = []
        
        for part in parts[1:]:
            if part.startswith('-'):
                arg_type = "option"
            else:
                arg_type = "value"
            
            args.append({"value": part, "type": arg_type})
        
        return {
            "command": base_command,
            "args": args
        }
    
    first_part = re.split(r'[|;&]', command)[0].strip()
    parts = first_part.split()
    base_command = parts[0] if parts else ""
    
    return {
        "command": base_command,
        "args": [{"value": command[len(base_command):].strip(), "type": "complex"}]
    }

def show_options(query: str):
    context = get_env_context()
    console = Console()
    
    try:
        provider = OllamaProvider()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]\nPlease run 'tacz --setup' to configure Ollama settings.")
        console.print("Please run 'tacz --setup' to configure Ollama settings.")
        return
    
    live = None
    current_commands = []
    
    def update_display(commands):
        nonlocal live, current_commands
        
        if live is None:
            live = Live(
                Panel("[bold blue]Thinking...[/bold blue]", border_style="blue"),
                console=console,
                refresh_per_second=10
            )
            live.start()
            current_commands = []
        
        current_commands = commands
        
        display = Text()
        display.append("Generating commands...\n\n", style="bold blue")
        
        for i, cmd in enumerate(current_commands):
            command_str = cmd.get('cmd', '')
            explanation = cmd.get('explanation', '')
            
            if command_str.strip().startswith('{'):
                continue
                
            display.append(f"Command {i+1}: ", style="yellow")
            display.append(f"{command_str}\n", style="green bold")
            
            if explanation:
                display.append(f"  {explanation}\n", style="dim")
        
        live.update(Panel(display, border_style="blue"))
    
    try:
        response = provider.get_options(prompt=query, context=context, display_callback=update_display)
        
        if live:
            live.stop()
    
    except Exception as e:
        if live:
            live.stop()
        console.print(f"[red]Error: {e}[/red]")
        return
    
    if response is None:
        logger.error("Failed to generate commands. Make sure Ollama is running.")
        return
    
    if not response.is_valid or not response.commands:
        logger.info(response.explanation_if_not_valid or "Model could not understand your request.")
        return
    
    console.print(f"\nPlatform detected: {response.platform_detected}\n")

    choices = []
    for cmd in response.commands:
        if not shutil.which(cmd.command.split()[0]):
            cmd.explanation += " (⚠ command not found on this system)"
            cmd.is_dangerous = True
            cmd.danger_explanation = "Command not available — might fail."
        
        desc_parts = []
        if cmd.explanation:
            desc_parts.append(cmd.explanation)
        if cmd.is_dangerous:
            desc_parts.append("⚠ dangerous")
        if getattr(cmd, 'requires_sudo', False):
            desc_parts.append("sudo")
        if getattr(cmd, 'estimated_runtime', None):
            desc_parts.append(f"~{cmd.estimated_runtime}")

        choice = questionary.Choice(
            title=cmd.command,
            value=cmd,
            description=" | ".join(desc_parts)
        )
        choices.append(choice)
    
    choices.extend([
        questionary.Separator(),
        questionary.Choice("📚 Show command history", value="history"),
        questionary.Choice("⭐ Show favorite commands", value="favorites"),
        questionary.Choice("❌ Cancel", value="cancel"),
    ])
    
    selected = questionary.select(
        "Select a command:",
        choices=choices,
        use_shortcuts=True,
        style=questionary.Style([
            ("answer", "fg:#61afef bold"),
            ("question", "bold"),
            ("instruction", "fg:#98c379"),
            ("selected", "fg:#ffffff bg:#61afef"),
            ("pointer", "fg:#61afef bold"),
        ])
    ).ask()
    
    if selected == "cancel":
        return
    elif selected == "history":
        show_history()
        return
    elif selected == "favorites":
        show_favorites()
        return
    
    if selected:
        print()
        
        if selected.is_dangerous:
            danger_reason = getattr(selected, 'danger_explanation', None) or "Unknown danger"
            warning_panel = Panel(
                f"[bold red]⚠️  WARNING[/bold red]\n\n"
                f"This command is potentially dangerous:\n"
                f"[yellow]{danger_reason}[/yellow]\n\n"
                f"Please review carefully before executing.",
                title="Danger Warning",
                border_style="red"
            )
            console.print(warning_panel)
            print()
        
        parts = break_down_command(selected.command)
        has_chains, operators = has_command_chaining(selected.command)

        breakdown = Text()
        breakdown.append(f"Command: ", style="bold")
        breakdown.append(f"{parts['command']}\n", style="cyan bold")

        if parts["args"]:
            breakdown.append("Arguments:\n", style="bold")
            for arg in parts["args"]:
                if arg["type"] == "option":
                    breakdown.append(f"  {arg['value']}", style="yellow")
                else:
                    breakdown.append(f"  {arg['value']}", style="green")
                breakdown.append("\n")

        if has_chains:
            breakdown.append("\nCommand contains these operations:\n", style="bold yellow")
            for op in operators:
                breakdown.append(f"  • {op}\n", style="yellow")
            
            breakdown.append("\nThis command will execute multiple operations. Please review carefully.\n", style="yellow")

        console.print(Panel(breakdown, title="Command Breakdown", border_style="blue"))
        print()
        
        final_command = edit_command(selected.command)
        final_command = sanitize_command(final_command)

        console.print(Panel(final_command, title="Command", border_style="blue"))
        
        try:
            pyperclip.copy(final_command)
            rprint("[green]✓[/green] Copied to clipboard!")
        except pyperclip.PyperclipException:
            rprint("[yellow]Could not copy to clipboard. Please install xclip/xsel (Linux) or pbcopy (Mac).[/yellow]")
        
        if questionary.confirm("Add to favorites?").ask():
            description = questionary.text(
                "Enter a description for this favorite:",
                default=selected.explanation
            ).ask()
            provider.add_to_favorites(final_command, description)
            rprint("[green]✓[/green] Added to favorites!")
        
        if questionary.confirm("Execute this command?", default=False).ask():
            if is_rm_command(final_command):
                rm_warning = Panel(
                    f"[bold red]⚠️ DELETION WARNING ⚠️[/bold red]\n\n"
                    f"This command uses [bold]rm[/bold] which permanently deletes files!\n"
                    f"There is [bold]NO UNDO[/bold] for this operation.\n\n"
                    f"Type [bold yellow]\"YES DELETE\"[/bold yellow] to confirm you want to proceed:",
                    title="Deletion Confirmation Required",
                    border_style="red"
                )
                console.print(rm_warning)
                
                deletion_confirmation = input("Confirmation (type 'YES DELETE' to proceed): ")
                
                if deletion_confirmation != "YES DELETE":
                    rprint("[yellow]Command cancelled.[/yellow]")
                    return
                
            print("\n" + "="*50)
            rprint(f"[cyan]Running:[/cyan] {final_command}")
            print("="*50)
            
            try:
                result = run_command(final_command, shell=True, text=True, capture_output=True)
                success = result.returncode == 0
                
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    rprint(f"[red]{result.stderr}[/red]")
                
                provider.db.record_history(
                    query=query,
                    command=final_command,
                    executed=True,
                    success=success,
                    platform=response.platform_detected
                )
                
                if success:
                    rprint("\n[green]✓ Command completed successfully[/green]")
                else:
                    rprint(f"\n[red]✗ Command failed with exit code {result.returncode}[/red]")
                    
            except Exception as e:
                rprint(f"\n[red]Error executing command: {e}[/red]")
                
                provider.db.record_history(
                    query=query,
                    command=final_command,
                    executed=True,
                    success=False,
                    platform=response.platform_detected
                )

def interactive_mode():
    console = Console()
    console.print("\n[bold blue]tacz - Local Command Assistant[/bold blue]")
    console.print("Type 'exit' to quit, '--history' for command history, '--favorites' for favorites\n")
    
    while True:
        try:
            user_input = questionary.text(
                "What do you want to do?",
                style=questionary.Style([
                    ("question", "fg:#98c379 bold"),
                ])
            ).ask()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("\n[green]Goodbye![/green]")
                break
            elif user_input.lower() == '--history':
                show_history()
                continue
            elif user_input.lower() == '--favorites':
                show_favorites()
                continue
            
            show_options(user_input)
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Use 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")

def ensure_directories():
    tacz_dir = Path.home() / ".tacz"
    tacz_dir.mkdir(exist_ok=True)

def app():
    ensure_directories()
    
    args = [arg.strip() for arg in sys.argv[1:]]
    config_path = Path.home() / ".taczrc"
    
    if not config_path.exists() or (args and args[0] == "--setup"):
        run_setup()
        print("\n✅ Setup complete!")
        if args and args[0] == "--setup":
            return
    
    dotenv.load_dotenv(config_path, override=True)
    
    if args:
        if args[0] == "--version":
            print("tacz version: 1.1.0 (local-only)")
            return
        elif args[0] == "--history":
            show_history()
            return
        elif args[0] == "--favorites":
            show_favorites()
            return
    if args:
        query = " ".join(args).rstrip("?")
        show_options(query)
    else:
        interactive_mode()

if __name__ == "__main__":
    app()