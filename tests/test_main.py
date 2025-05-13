import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import pyperclip

from tacz.main import (
    app,
    get_provider,
    setup,
    show_history,
    show_favorites,
    get_env_context,
    show_options,
    edit_command,
    break_down_command,
    ensure_directories,
    cleanup,
    interactive_mode
)
from tacz.llms.types import Command

class TestMain:
    @pytest.fixture
    def mock_ollama_provider(self):
        """Mock OllamaProvider."""
        with patch('tacz.main.OllamaProvider') as mock_provider_cls:
            mock_provider = MagicMock()
            mock_provider_cls.return_value = mock_provider
            yield mock_provider

    def test_show_favorites(self, mock_ollama_provider):
        """Test showing favorite commands."""
        mock_favorites = [
            {"command": "ls -la", "explanation": "List all files", "popularity": 5},
            {"command": "df -h", "explanation": "Check disk space", "popularity": 3}
        ]
        mock_ollama_provider.db.search.return_value = mock_favorites
        
        with patch('tacz.main.OllamaProvider') as mock_provider_class, \
             patch('tacz.main.Console') as mock_console_cls:
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            mock_provider_class.return_value = mock_ollama_provider
            
            show_favorites()
            
            mock_console.print.assert_called_once()
            mock_ollama_provider.db.search.assert_called_once_with("favorite", limit=20)
    
    def test_show_favorites_empty(self, mock_ollama_provider):
        """Test showing favorites when none exist."""
        mock_ollama_provider.db.search.return_value = []
        
        with patch('tacz.main.OllamaProvider') as mock_provider_class, \
             patch('builtins.print') as mock_print:
            mock_provider_class.return_value = mock_ollama_provider
            
            show_favorites()
            
            mock_print.assert_called_once_with("No favorite commands saved.")
    
    def test_show_favorites_exception(self, mock_ollama_provider):
        """Test error handling in show_favorites."""
        mock_ollama_provider.db.search.side_effect = Exception("Database error")
        
        with patch('tacz.main.OllamaProvider') as mock_provider_class, \
             patch('tacz.main.rprint') as mock_rprint:
            mock_provider_class.return_value = mock_ollama_provider
            
            show_favorites()
            
            mock_rprint.assert_called_once()
            assert "Error showing favorites" in mock_rprint.call_args[0][0]
    
    def test_edit_command(self):
        """Test command editing functionality."""
        with patch('tacz.main.questionary') as mock_questionary:
            mock_text = MagicMock()
            mock_questionary.text.return_value = mock_text
            mock_text.ask.return_value = "ls -la --color"
            
            result = edit_command("ls -la")
            assert result == "ls -la --color"
            mock_questionary.text.assert_called_with(
                "Edit command (press Enter to keep as-is):",
                default="ls -la"
            )
            
            mock_text.ask.return_value = ""
            result = edit_command("ls -la")
            assert result == "ls -la"
    
    def test_ensure_directories(self):
        """Test directory creation."""
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path("/mock/home")
            
            ensure_directories()
            
            mock_mkdir.assert_called_once_with(exist_ok=True)
            mock_home.assert_called_once()
    
    def test_cleanup(self):
        """Test cleanup function."""
        with patch('tacz.main._provider_instance', None):
            cleanup()

        mock_provider = MagicMock()
        with patch('tacz.main._provider_instance', mock_provider):
            cleanup()
            mock_provider.db.close.assert_called_once()
    
    def test_app_version_flag(self):
        """Test app function with --version flag."""
        with patch('sys.argv', ['tacz', '--version']), \
             patch('builtins.print') as mock_print, \
             patch('tacz.main.ensure_directories'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('tacz.main.dotenv.load_dotenv'):
            
            app()
            
            mock_print.assert_called_once_with("tacz version: 1.1.0 (local-only)")
    
    def test_app_history_flag(self):
        """Test app function with --history flag."""
        with patch('sys.argv', ['tacz', '--history']), \
             patch('tacz.main.show_history') as mock_show_history, \
             patch('tacz.main.ensure_directories'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('tacz.main.dotenv.load_dotenv'):
            
            app()
            
            mock_show_history.assert_called_once()
    
    def test_app_favorites_flag(self):
        """Test app function with --favorites flag."""
        with patch('sys.argv', ['tacz', '--favorites']), \
             patch('tacz.main.show_favorites') as mock_show_favorites, \
             patch('tacz.main.ensure_directories'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('tacz.main.dotenv.load_dotenv'):
            
            app()
            
            mock_show_favorites.assert_called_once()
    
    def test_app_setup_needed(self):
        """Test app function when setup is needed."""
        with patch('sys.argv', ['tacz']), \
             patch('tacz.main.ensure_directories'), \
             patch('pathlib.Path.exists', return_value=False), \
             patch('tacz.main.run_setup') as mock_run_setup, \
             patch('builtins.print') as mock_print, \
             patch('tacz.main.interactive_mode'):
            
            app()
            
            mock_run_setup.assert_called_once()
            mock_print.assert_called_once_with("\n✅ Setup complete!")
    
    def test_app_with_query(self):
        """Test app function with query arguments."""
        with patch('sys.argv', ['tacz', 'list', 'files']), \
             patch('tacz.main.ensure_directories'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('tacz.main.dotenv.load_dotenv'), \
             patch('tacz.main.show_options') as mock_show_options:
            
            app()
            
            mock_show_options.assert_called_once_with("list files")
    
    def test_app_interactive(self):
        """Test app function in interactive mode."""
        with patch('sys.argv', ['tacz']), \
             patch('tacz.main.ensure_directories'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('tacz.main.dotenv.load_dotenv'), \
             patch('tacz.main.interactive_mode') as mock_interactive:
            
            app()
            
            mock_interactive.assert_called_once()
    
    def test_interactive_mode(self):
        """Test interactive mode with various inputs."""
        with patch('tacz.main.Console') as mock_console_cls, \
             patch('tacz.main.questionary') as mock_questionary, \
             patch('tacz.main.show_history') as mock_show_history, \
             patch('tacz.main.show_favorites') as mock_show_favorites, \
             patch('tacz.main.show_options') as mock_show_options:
            
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            mock_text = MagicMock()
            mock_questionary.text.return_value = mock_text
            
            mock_text.ask.side_effect = ["exit"]
            interactive_mode()
            mock_console.print.assert_any_call("\n[green]Goodbye![/green]")
            
            mock_text.ask.side_effect = ["--history", "--favorites", "list files", "exit"]
            interactive_mode()
            mock_show_history.assert_called_once()
            mock_show_favorites.assert_called_once()
            mock_show_options.assert_called_once_with("list files")
    
    def test_show_options_with_commands(self, mock_ollama_provider):
        """Test show_options with valid commands."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
             patch('tacz.main.Console') as mock_console_cls, \
             patch('tacz.main.questionary') as mock_questionary, \
             patch('tacz.main.shutil.which', return_value="/usr/bin/ls"), \
             patch('builtins.print') as mock_print:
            
            mock_get_env_context.return_value = "Platform: Linux (bash)\nShell: bash"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd1 = Command(command="ls -la", explanation="List files", is_dangerous=False)
            cmd2 = Command(command="df -h", explanation="Check disk space", is_dangerous=False)
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd1, cmd2]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_select = MagicMock()
            mock_questionary.select.return_value = mock_select
            mock_select.ask.return_value = "cancel"
            
            show_options("list files")
            
            mock_print.assert_any_call("\nPlatform detected: Linux (bash)\n")
            mock_questionary.select.assert_called_once()
            
            choices = mock_questionary.select.call_args[1]["choices"]
            assert len(choices) > 2
    
    def test_show_options_with_invalid_response(self, mock_ollama_provider):
        """Test show_options with invalid response."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
             patch('tacz.main.Console') as mock_console_cls, \
             patch('builtins.print') as mock_print:
            
            mock_get_env_context.return_value = "Platform: Linux (bash)\nShell: bash"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            mock_response = MagicMock()
            mock_response.is_valid = False
            mock_response.explanation_if_not_valid = "Could not understand query"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            show_options("invalid query")
            
            mock_print.assert_called_with("\nCould not understand query")
    
    def test_show_options_no_commands(self, mock_ollama_provider):
        """Test show_options with no commands returned."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
             patch('tacz.main.Console') as mock_console_cls, \
             patch('builtins.print') as mock_print:
            
            mock_get_env_context.return_value = "Platform: Linux (bash)\nShell: bash"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = []
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            show_options("some query")
            
            mock_print.assert_any_call("\nNo commands available")
    
    def test_show_options_command_selection(self, mock_ollama_provider):
        """Test show_options with command selection and execution."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
             patch('tacz.main.Console') as mock_console_cls, \
             patch('tacz.main.questionary') as mock_questionary, \
             patch('tacz.main.edit_command') as mock_edit, \
             patch('tacz.main.sanitize_command') as mock_sanitize, \
             patch('tacz.main.pyperclip') as mock_pyperclip, \
             patch('tacz.main.break_down_command') as mock_break_down, \
             patch('tacz.main.has_command_chaining') as mock_has_chaining, \
             patch('tacz.main.is_rm_command') as mock_is_rm, \
             patch('tacz.main.run_command') as mock_run, \
             patch('tacz.main.rprint') as mock_rprint, \
             patch('shutil.which', return_value="/usr/bin/ls"):
            
            mock_get_env_context.return_value = "Platform: Linux (bash)\nShell: bash"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(command="ls -la", explanation="List files", is_dangerous=False)
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "ls", "args": [{"value": "-la", "type": "option"}]}
            mock_has_chaining.return_value = (False, [])
            mock_edit.return_value = "ls -la"
            mock_sanitize.return_value = "ls -la"
            mock_is_rm.return_value = False
            
            mock_select = MagicMock()
            mock_confirm = MagicMock()
            mock_text = MagicMock()
            
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm
            mock_questionary.text.return_value = mock_text
            
            mock_select.ask.return_value = cmd
            mock_confirm.ask.side_effect = [False, True]
            
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "file1 file2"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            show_options("list files")
            
            mock_run.assert_called_once_with("ls -la", shell=True, text=True, capture_output=True)
            mock_ollama_provider.db.record_history.assert_called_once()
            mock_rprint.assert_any_call("\n[green]✓ Command completed successfully[/green]")

    def test_break_down_command_empty(self):
        """Test break_down_command with empty command."""
        result = break_down_command("")
        
        assert result["command"] == ""
        assert len(result["args"]) == 0
    
    def test_break_down_command_single_word(self):
        """Test break_down_command with single word command."""
        result = break_down_command("ls")
        
        assert result["command"] == "ls"
        assert len(result["args"]) == 0

    def test_show_history_empty(self, mock_ollama_provider):
        """Test show_history when history is empty."""
        mock_ollama_provider.get_command_history.return_value = []
        
        with patch('builtins.print') as mock_print:
            show_history()
            mock_print.assert_called_once_with("No command history available.")

    def test_show_history_exception(self, mock_ollama_provider):
        """Test show_history error handling."""
        with patch('tacz.main.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_ollama_provider
            mock_ollama_provider.get_command_history.side_effect = Exception("Database error")
            
            with patch('tacz.main.rprint') as mock_rprint:
                show_history()
                mock_rprint.assert_called_once()
                assert "Error showing history" in mock_rprint.call_args[0][0]

    def test_show_options_none_response(self, mock_ollama_provider):
        """Test show_options with None response from provider."""
        with patch('tacz.main.get_env_context'), \
            patch('tacz.main.Console'), \
            patch('tacz.main.rprint') as mock_rprint:
            
            mock_ollama_provider.get_options.return_value = None
            
            show_options("list files")
            
            mock_rprint.assert_called_with("[red]Failed to generate commands. Make sure Ollama is running.[/red]")

    def test_show_options_exception(self, mock_ollama_provider):
        """Test show_options error handling."""
        with patch('tacz.main.get_env_context'), \
            patch('tacz.main.Console') as mock_console_cls:
            
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            mock_ollama_provider.get_options.side_effect = Exception("API error")
            
            show_options("list files")
            
            mock_console.print.assert_called_once()
            assert "Error" in str(mock_console.print.call_args[0][0])

    def test_show_options_clipboard_error(self, mock_ollama_provider):
        """Test clipboard error handling in show_options."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.pyperclip.copy') as mock_copy, \
            patch('tacz.main.rprint') as mock_rprint, \
            patch('tacz.main.break_down_command') as mock_break_down, \
            patch('tacz.main.has_command_chaining') as mock_has_chaining, \
            patch('tacz.main.edit_command') as mock_edit, \
            patch('tacz.main.sanitize_command') as mock_sanitize, \
            patch('shutil.which', return_value="/usr/bin/ls"):
            
            mock_get_env_context.return_value = "Platform: Linux (bash)"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(command="ls -la", explanation="List files", is_dangerous=False)
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "ls", "args": []}
            mock_has_chaining.return_value = (False, [])
            mock_edit.return_value = "ls -la"
            mock_sanitize.return_value = "ls -la"
            
            mock_copy.side_effect = pyperclip.PyperclipException("No clipboard")
            
            mock_select = MagicMock()
            mock_questionary.select.return_value = mock_select
            mock_select.ask.return_value = cmd
            
            mock_confirm = MagicMock()
            mock_questionary.confirm.return_value = mock_confirm
            mock_confirm.ask.return_value = False
            
            show_options("list files")
            
            mock_rprint.assert_any_call("[yellow]Could not copy to clipboard. Please install xclip/xsel (Linux) or pbcopy (Mac).[/yellow]")

    def test_show_options_dangerous_command(self, mock_ollama_provider):
        """Test show_options with dangerous command."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.break_down_command') as mock_break_down, \
            patch('tacz.main.has_command_chaining') as mock_has_chaining, \
            patch('tacz.main.edit_command') as mock_edit, \
            patch('tacz.main.sanitize_command') as mock_sanitize, \
            patch('tacz.main.pyperclip') as mock_pyperclip, \
            patch('shutil.which', return_value="/usr/bin/rm"):
            
            mock_get_env_context.return_value = "Platform: Linux (bash)"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(
                command="rm -rf /", 
                explanation="Delete everything", 
                is_dangerous=True, 
                danger_explanation="Will delete all files"
            )
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "rm", "args": [{"value": "-rf", "type": "option"}, {"value": "/", "type": "value"}]}
            mock_has_chaining.return_value = (False, [])
            mock_edit.return_value = "rm -rf /"
            mock_sanitize.return_value = "rm -rf /"
            
            mock_select = MagicMock()
            mock_questionary.select.return_value = mock_select
            mock_select.ask.return_value = cmd
            
            mock_confirm = MagicMock()
            mock_questionary.confirm.return_value = mock_confirm
            mock_confirm.ask.return_value = False 
            show_options("delete everything")
            
            assert mock_console.print.called
            
            warning_panel_found = False
            for call_args in mock_console.print.call_args_list:
                args = call_args[0]
                if args and hasattr(args[0], 'title') and "Danger Warning" in args[0].title:
                    warning_panel_found = True
                    break
            
            assert warning_panel_found, "No danger warning panel was displayed"

    def test_show_options_rm_command_execution(self, mock_ollama_provider):
        """Test rm command confirmation flow."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.edit_command') as mock_edit, \
            patch('tacz.main.sanitize_command') as mock_sanitize, \
            patch('tacz.main.pyperclip') as mock_pyperclip, \
            patch('tacz.main.break_down_command') as mock_break_down, \
            patch('tacz.main.has_command_chaining') as mock_has_chaining, \
            patch('tacz.main.is_rm_command') as mock_is_rm, \
            patch('tacz.main.run_command') as mock_run, \
            patch('tacz.main.rprint') as mock_rprint, \
            patch('builtins.input') as mock_input, \
            patch('shutil.which', return_value="/usr/bin/rm"):
            
            mock_get_env_context.return_value = "Platform: Linux (bash)"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(command="rm -rf temp", explanation="Delete temp directory", is_dangerous=True)
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "rm", "args": [{"value": "-rf", "type": "option"}, {"value": "temp", "type": "value"}]}
            mock_has_chaining.return_value = (False, [])
            mock_edit.return_value = "rm -rf temp"
            mock_sanitize.return_value = "rm -rf temp"
            mock_is_rm.return_value = True
            
            mock_input.return_value = "YES DELETE"
            
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            mock_select = MagicMock()
            mock_confirm = MagicMock()
            
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm
            
            mock_select.ask.return_value = cmd
            mock_confirm.ask.side_effect = [False, True]
            
            show_options("delete temp")
            
            deletion_panel_found = False
            for call_args in mock_console.print.call_args_list:
                args = call_args[0]
                if args and hasattr(args[0], 'title') and "Deletion" in args[0].title:
                    deletion_panel_found = True
                    break
            
            assert deletion_panel_found, "No deletion confirmation panel was displayed"
            
            mock_input.assert_called_once()
            
            mock_run.assert_called_once()

    def test_show_options_rm_command_cancelled(self, mock_ollama_provider):
        """Test rm command cancellation flow."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.edit_command') as mock_edit, \
            patch('tacz.main.sanitize_command') as mock_sanitize, \
            patch('tacz.main.pyperclip') as mock_pyperclip, \
            patch('tacz.main.break_down_command') as mock_break_down, \
            patch('tacz.main.has_command_chaining') as mock_has_chaining, \
            patch('tacz.main.is_rm_command') as mock_is_rm, \
            patch('tacz.main.run_command') as mock_run, \
            patch('tacz.main.rprint') as mock_rprint, \
            patch('builtins.input') as mock_input, \
            patch('shutil.which', return_value="/usr/bin/rm"):
            
            mock_get_env_context.return_value = "Platform: Linux (bash)"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(command="rm -rf temp", explanation="Delete temp directory", is_dangerous=True)
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "rm", "args": [{"value": "-rf", "type": "option"}, {"value": "temp", "type": "value"}]}
            mock_has_chaining.return_value = (False, [])
            mock_edit.return_value = "rm -rf temp"
            mock_sanitize.return_value = "rm -rf temp"
            mock_is_rm.return_value = True
            
            mock_input.return_value = "no"
            
            mock_select = MagicMock()
            mock_confirm = MagicMock()
            
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm
            
            mock_select.ask.return_value = cmd
            mock_confirm.ask.side_effect = [False, True]
            show_options("delete temp")
            
            mock_run.assert_not_called()
            mock_rprint.assert_any_call("[yellow]Command cancelled.[/yellow]")

    def test_interactive_mode_keyboard_interrupt(self):
        """Test interactive mode with keyboard interrupt."""
        with patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary:
            
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            mock_text = MagicMock()
            mock_questionary.text.return_value = mock_text
            
            mock_text.ask.side_effect = [KeyboardInterrupt, "exit"]
            
            interactive_mode()
            
            mock_console.print.assert_any_call("\n\n[yellow]Use 'exit' to quit.[/yellow]")

    def test_interactive_mode_general_exception(self):
        """Test interactive mode with general exception."""
        with patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary:
            
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            mock_text = MagicMock()
            mock_questionary.text.return_value = mock_text
            
            mock_text.ask.side_effect = [Exception("Random error"), "exit"]
            
            interactive_mode()
            
            mock_console.print.assert_any_call("\n[red]Error: Random error[/red]")

    def test_break_down_command_with_multiple_args(self):
        """Test break_down_command with multiple arguments."""
        result = break_down_command("grep 'pattern' file.txt")
        
        assert result["command"] == "grep"
        assert len(result["args"]) == 2
        assert result["args"][0]["value"] == "'pattern'"
        assert result["args"][0]["type"] == "value"
        assert result["args"][1]["value"] == "file.txt"
        assert result["args"][1]["type"] == "value"

    def test_break_down_command_with_chaining(self):
        """Test break_down_command with command chaining."""
        result = break_down_command("ls -la | grep test")
        
        assert result["command"] == "ls"
        assert len(result["args"]) == 1
        assert result["args"][0]["type"] == "complex"
        assert " | grep test" in result["args"][0]["value"]

    def test_show_options_add_to_favorites(self, mock_ollama_provider):
        """Test adding command to favorites."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.edit_command') as mock_edit, \
            patch('tacz.main.sanitize_command') as mock_sanitize, \
            patch('tacz.main.pyperclip') as mock_pyperclip, \
            patch('tacz.main.break_down_command') as mock_break_down, \
            patch('tacz.main.has_command_chaining') as mock_has_chaining, \
            patch('tacz.main.is_rm_command') as mock_is_rm, \
            patch('tacz.main.rprint') as mock_rprint, \
            patch('shutil.which', return_value="/usr/bin/ls"):
            
            mock_get_env_context.return_value = "Platform: Linux (bash)"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(command="ls -la", explanation="List files", is_dangerous=False)
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "ls", "args": [{"value": "-la", "type": "option"}]}
            mock_has_chaining.return_value = (False, [])
            mock_edit.return_value = "ls -la"
            mock_sanitize.return_value = "ls -la"
            mock_is_rm.return_value = False
            
            mock_select = MagicMock()
            mock_confirm = MagicMock()
            mock_text = MagicMock()
            
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm
            mock_questionary.text.return_value = mock_text
            
            mock_select.ask.return_value = cmd
            mock_confirm.ask.side_effect = [True, False]
            mock_text.ask.return_value = "Custom description"
            
            show_options("list files")
            
            mock_ollama_provider.add_to_favorites.assert_called_once_with("ls -la", "Custom description")
            mock_rprint.assert_any_call("[green]✓[/green] Added to favorites!")
    
    def test_show_options_command_execution_failure(self, mock_ollama_provider):
        """Test command execution failure."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.edit_command') as mock_edit, \
            patch('tacz.main.sanitize_command') as mock_sanitize, \
            patch('tacz.main.pyperclip') as mock_pyperclip, \
            patch('tacz.main.break_down_command') as mock_break_down, \
            patch('tacz.main.has_command_chaining') as mock_has_chaining, \
            patch('tacz.main.is_rm_command') as mock_is_rm, \
            patch('tacz.main.run_command') as mock_run, \
            patch('tacz.main.rprint') as mock_rprint:
            
            mock_get_env_context.return_value = "Platform: Linux (bash)"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(command="invalid-command", explanation="Invalid command", is_dangerous=False)
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "invalid-command", "args": []}
            mock_has_chaining.return_value = (False, [])
            mock_edit.return_value = "invalid-command"
            mock_sanitize.return_value = "invalid-command"
            mock_is_rm.return_value = False
            
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "command not found: invalid-command"
            mock_run.return_value = mock_result
            
            mock_select = MagicMock()
            mock_confirm = MagicMock()
            
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm
            
            mock_select.ask.return_value = cmd
            mock_confirm.ask.side_effect = [False, True] 
            show_options("run invalid command")
            
            mock_rprint.assert_any_call("\n[red]✗ Command failed with exit code 1[/red]")
            mock_ollama_provider.db.record_history.assert_called_once_with(
                query="run invalid command",
                command="invalid-command",
                executed=True,
                success=False,
                platform=mock_response.platform_detected
            )

    def test_show_options_command_execution_exception(self, mock_ollama_provider):
        """Test command execution with exception."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.edit_command') as mock_edit, \
            patch('tacz.main.sanitize_command') as mock_sanitize, \
            patch('tacz.main.pyperclip') as mock_pyperclip, \
            patch('tacz.main.break_down_command') as mock_break_down, \
            patch('tacz.main.has_command_chaining') as mock_has_chaining, \
            patch('tacz.main.is_rm_command') as mock_is_rm, \
            patch('tacz.main.run_command') as mock_run, \
            patch('tacz.main.rprint') as mock_rprint:
            
            mock_get_env_context.return_value = "Platform: Linux (bash)"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(command="problematic-command", explanation="Command that raises exception", is_dangerous=False)
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "problematic-command", "args": []}
            mock_has_chaining.return_value = (False, [])
            mock_edit.return_value = "problematic-command"
            mock_sanitize.return_value = "problematic-command"
            mock_is_rm.return_value = False
            
            mock_run.side_effect = Exception("Command execution error")
            
            mock_select = MagicMock()
            mock_confirm = MagicMock()
            
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm
            
            mock_select.ask.return_value = cmd
            mock_confirm.ask.side_effect = [False, True]
            
            show_options("run problematic command")
            
            mock_rprint.assert_any_call("\n[red]Error executing command: Command execution error[/red]")
            mock_ollama_provider.db.record_history.assert_called_once_with(
                query="run problematic command",
                command="problematic-command",
                executed=True,
                success=False,
                platform=mock_response.platform_detected
            )

    def test_show_options_with_command_chaining(self, mock_ollama_provider):
        """Test show_options with command that has chaining."""
        with patch('tacz.main.get_env_context') as mock_get_env_context, \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.edit_command') as mock_edit, \
            patch('tacz.main.sanitize_command') as mock_sanitize, \
            patch('tacz.main.pyperclip') as mock_pyperclip, \
            patch('tacz.main.break_down_command') as mock_break_down, \
            patch('tacz.main.has_command_chaining') as mock_has_chaining, \
            patch('shutil.which', return_value="/usr/bin/find"):
            
            mock_get_env_context.return_value = "Platform: Linux (bash)"
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            cmd = Command(
                command="find . -name '*.py' | grep test", 
                explanation="Find Python test files", 
                is_dangerous=False
            )
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            mock_response.commands = [cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_break_down.return_value = {"command": "find", "args": [{"value": ". -name '*.py' | grep test", "type": "complex"}]}
            mock_has_chaining.return_value = (True, ["pipe (|)"])
            mock_edit.return_value = "find . -name '*.py' | grep test"
            mock_sanitize.return_value = "find . -name '*.py'"
            
            mock_select = MagicMock()
            mock_questionary.select.return_value = mock_select
            mock_select.ask.return_value = cmd
            
            mock_confirm = MagicMock()
            mock_questionary.confirm.return_value = mock_confirm
            mock_confirm.ask.return_value = False
            
            show_options("find python test files")
            
            command_breakdown_found = False
            for call_args in mock_console.print.call_args_list:
                args = call_args[0]
                if args and hasattr(args[0], 'title') and "Command Breakdown" in args[0].title:
                    command_breakdown_found = True
                    break
                    
            assert command_breakdown_found, "Command breakdown panel not found"

    def test_show_options_history_menu_item(self, mock_ollama_provider):
        """Test selecting history menu item in show_options."""
        with patch('tacz.main.get_env_context'), \
            patch('tacz.main.Console'), \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.show_history') as mock_show_history:
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            
            mock_cmd = MagicMock()
            mock_cmd.command = "ls -la"
            mock_cmd.explanation = "List files"
            mock_cmd.is_dangerous = False
            mock_response.commands = [mock_cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_select = MagicMock()
            mock_questionary.select.return_value = mock_select
            mock_select.ask.return_value = "history"
            
            show_options("do something")
            
            mock_show_history.assert_called_once()

    def test_show_options_favorites_menu_item(self, mock_ollama_provider):
        """Test selecting favorites menu item in show_options."""
        with patch('tacz.main.get_env_context'), \
            patch('tacz.main.Console'), \
            patch('tacz.main.questionary') as mock_questionary, \
            patch('tacz.main.show_favorites') as mock_show_favorites:
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            
            mock_cmd = MagicMock()
            mock_cmd.command = "ls -la"
            mock_cmd.explanation = "List files"
            mock_cmd.is_dangerous = False
            mock_response.commands = [mock_cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_select = MagicMock()
            mock_questionary.select.return_value = mock_select
            mock_select.ask.return_value = "favorites"
            
            show_options("do something")
            
            mock_show_favorites.assert_called_once()

    def test_show_options_cancel_menu_item(self, mock_ollama_provider):
        """Test selecting cancel menu item in show_options."""
        with patch('tacz.main.get_env_context'), \
            patch('tacz.main.Console'), \
            patch('tacz.main.questionary') as mock_questionary:
            
            mock_response = MagicMock()
            mock_response.is_valid = True
            
            mock_cmd = MagicMock()
            mock_cmd.command = "ls -la"
            mock_cmd.explanation = "List files"
            mock_cmd.is_dangerous = False
            mock_response.commands = [mock_cmd]
            mock_response.platform_detected = "Linux (bash)"
            
            mock_ollama_provider.get_options.return_value = mock_response
            
            mock_select = MagicMock()
            mock_questionary.select.return_value = mock_select
            mock_select.ask.return_value = "cancel"        

    def test_live_update_display(self, mock_ollama_provider):
        """Test the update_display callback in show_options."""
        with patch('tacz.main.get_env_context'), \
            patch('tacz.main.Console') as mock_console_cls, \
            patch('tacz.main.Live') as mock_live_cls, \
            patch('tacz.main.Panel') as mock_panel_cls, \
            patch('tacz.main.questionary'):
            
            mock_console = MagicMock()
            mock_console_cls.return_value = mock_console
            
            mock_live = MagicMock()
            mock_live_cls.return_value = mock_live
            
            mock_panel = MagicMock()
            mock_panel_cls.return_value = mock_panel
            
            def capture_callback(*args, **kwargs):
                callback = kwargs.get('display_callback')
                commands = [
                    {'cmd': 'ls -la', 'explanation': 'List files'},
                    {'cmd': 'df -h', 'explanation': 'Check disk space'}
                ]
                callback(commands)
                return MagicMock(is_valid=False)
                
            mock_ollama_provider.get_options.side_effect = capture_callback
            
            show_options("do something")
            
            mock_live.start.assert_called_once()
            mock_live.update.assert_called_once()
            mock_live.stop.assert_called_once()

    def test_app_setup_and_execute(self):
        """Test app function with --setup flag but config exists."""
        with patch('sys.argv', ['tacz', '--setup']), \
            patch('tacz.main.ensure_directories'), \
            patch('pathlib.Path.exists', return_value=True), \
            patch('tacz.main.run_setup') as mock_run_setup, \
            patch('builtins.print') as mock_print:
            
            app()
            
            mock_run_setup.assert_called_once()
            mock_print.assert_called_once_with("\n✅ Setup complete!")