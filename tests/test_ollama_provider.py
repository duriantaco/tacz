import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from tacz.llms.providers.ollama_provider import OllamaProvider
from tacz.llms.types import CommandsResponse, Command

class TestOllamaProvider:
    @pytest.fixture
    def mock_openai(self):
        """Mock the OpenAI client."""
        with patch('tacz.llms.providers.ollama_provider.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def mock_db(self):
        """Mock the CommandDatabase."""
        with patch('tacz.llms.providers.ollama_provider.CommandDatabase') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            yield mock_db_instance
    
    def test_initialization(self, mock_config, mock_openai, mock_db):
        """Test that OllamaProvider initializes properly."""
        from tacz.config import get_db_path
        
        provider = OllamaProvider()
        
        assert provider.model == "test-model"
        assert provider.client is not None
        assert provider.db is mock_db
    
    def test_get_options_from_db(self, mock_config, mock_openai, mock_db):
        """Test getting options from the database."""
        db_results = [
            {
                "command": "ls -la",
                "explanation": "List all files",
                "dangerous": 0,
                "danger_reason": ""
            }
        ]
        mock_db.search.return_value = db_results
        
        provider = OllamaProvider()
        
        response = provider.get_options(
            prompt="list files",
            context="Platform: Linux (bash)\nShell: bash\nPython: 3.9.0"
        )
        
        assert response is not None
        assert response.is_valid
        assert len(response.commands) == 1
        assert response.commands[0].command == "ls -la"
        assert response.platform_detected == "Linux (bash)"
    
    def test_get_options_from_llm_json(self, mock_config, mock_openai, mock_db):
        """Test getting options from the LLM with valid JSON response."""
        mock_db.search.return_value = []
        
        mock_chat = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_chat
        mock_chat.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "is_valid": True,
                "commands": [
                    {
                        "command": "ls -la",
                        "explanation": "List all files",
                        "is_dangerous": False
                    }
                ]
            })))
        ]
        
        provider = OllamaProvider()
        
        response = provider.get_options(
            prompt="list files",
            context="Platform: Linux (bash)\nShell: bash\nPython: 3.9.0"
        )
        
        assert response is not None
        assert response.is_valid
        assert len(response.commands) == 1
        assert response.commands[0].command == "ls -la"
        assert response.platform_detected == "Linux (bash)"
        
        mock_db.add_command.assert_called_once()
    
    def test_get_options_json_parsing_fallback(self, mock_config, mock_openai, mock_db):
        """Test JSON parsing fallbacks."""
        mock_db.search.return_value = []
        
        mock_chat = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_chat
        mock_chat.choices = [
            MagicMock(message=MagicMock(content="""
            Here's the command:
            
            ```
            {"is_valid": true, "commands": [{"command": "ls -la", "explanation": "List all files", "is_dangerous": false}]}
            ```
            
            Hope this helps!
            """))
        ]
        
        provider = OllamaProvider()
        
        response = provider.get_options(
            prompt="list files",
            context="Platform: Linux (bash)\nShell: bash\nPython: 3.9.0"
        )
        
        assert response is not None
        assert response.is_valid
        assert len(response.commands) == 1
        assert response.commands[0].command == "ls -la"
    
    def test_get_options_code_block_fallback(self, mock_config, mock_openai, mock_db):
        """Test code block fallback parsing."""
        mock_db.search.return_value = []
        
        mock_chat = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_chat
        mock_chat.choices = [
            MagicMock(message=MagicMock(content="""
            You can list files using this command:
            
            ```bash
            ls -la
            ```
            
            This will show all files including hidden ones.
            """))
        ]
        
        provider = OllamaProvider()
        
        response = provider.get_options(
            prompt="list files",
            context="Platform: Linux (bash)\nShell: bash\nPython: 3.9.0"
        )
        
        assert response is not None
        assert response.is_valid
        assert len(response.commands) == 1
        assert response.commands[0].command == "ls -la"
        assert "hidden ones" in response.commands[0].explanation
    
    def test_get_options_plain_text_fallback(self, mock_config, mock_openai, mock_db):
        mock_db.search.return_value = []
        
        mock_chat = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_chat
        mock_chat.choices = [
            MagicMock(message=MagicMock(content="""
            ls -la
            This command lists all files including hidden ones.
            """))
        ]
        
        provider = OllamaProvider()
        
        response = provider.get_options(
            prompt="list files",
            context="Platform: Linux (bash)\nShell: bash\nPython: 3.9.0"
        )
        
        assert response is not None
        assert response.is_valid
        assert len(response.commands) == 1
        assert response.commands[0].command == "ls -la"
    
    def test_safety_checks(self, mock_config, mock_openai, mock_db):
        mock_db.search.return_value = []
        
        mock_chat = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_chat
        mock_chat.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "is_valid": True,
                "commands": [
                    {
                        "command": "rm -rf /",
                        "explanation": "Delete everything",
                        "is_dangerous": False
                    }
                ]
            })))
        ]
        
        provider = OllamaProvider()
        
        response = provider.get_options(
            prompt="delete everything",
            context="Platform: Linux (bash)\nShell: bash\nPython: 3.9.0"
        )
        
        assert response is not None
        assert response.is_valid
        assert len(response.commands) == 1
        assert response.commands[0].command == "rm -rf /"
        assert response.commands[0].is_dangerous
        assert response.commands[0].danger_explanation
    
    def test_add_to_favorites(self, mock_config, mock_openai, mock_db):
        """Test adding command to favorites."""
        provider = OllamaProvider()
        
        provider.add_to_favorites(
            command="ls -la",
            description="List all files including hidden ones"
        )
        
        mock_db.add_command.assert_called_once_with(
            command="ls -la",
            explanation="List all files including hidden ones",
            category="favorite",
            dangerous=False
        )
    
    def test_get_command_history(self, mock_config, mock_openai, mock_db):
        """Test getting command history."""
        mock_history = [
            {"query": "list files", "command": "ls -la", "executed": 1, "success": 1},
            {"query": "check disk", "command": "df -h", "executed": 1, "success": 1}
        ]
        mock_db.get_history.return_value = mock_history
        
        provider = OllamaProvider()
        
        history = provider.get_command_history()
        
        assert history == mock_history
        mock_db.get_history.assert_called_once_with(limit=10)
    
    def test_get_command_history_with_query(self, mock_config, mock_openai, mock_db):
        """Test getting command history with query."""
        mock_history = [
            {"query": "list files", "command": "ls -la", "executed": 1, "success": 1}
        ]
        mock_db.search_history.return_value = mock_history
        
        provider = OllamaProvider()
        
        history = provider.get_command_history(query="files")
        
        assert history == mock_history
        mock_db.search_history.assert_called_once_with("files", 10)