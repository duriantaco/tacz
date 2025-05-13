import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch
from tacz.config import config

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def temp_db_path(temp_dir):
    """Create a temporary database path."""
    return temp_dir / "test_commands.db"

@pytest.fixture
def mock_config(monkeypatch, temp_dir):
    """Mock config with test values."""
    test_config = {
        "OLLAMA_BASE_URL": "http://localhost:11434/v1",
        "OLLAMA_MODEL": "test-model",
        "ENABLE_CACHE": "true",
        "CACHE_TTL_HOURS": "24",
        "ENABLE_HISTORY": "true",
    }
    
    config_path = temp_dir / ".taczrc"
    with open(config_path, 'w') as f:
        for key, value in test_config.items():
            f.write(f"{key}={value}\n")
    
    monkeypatch.setattr("pathlib.Path.home", lambda: temp_dir)
    monkeypatch.setattr(config, "vals", test_config)
    
    return test_config

@pytest.fixture
def mock_db_ops():
    with patch('tacz.utils.command_db.CommandDatabase.add_command', autospec=True) as mock_add, \
         patch('tacz.utils.command_db.CommandDatabase.record_history', autospec=True) as mock_record:
        
        mock_add.return_value = 1
        
        yield {
            'add_command': mock_add,
            'record_history': mock_record
        }

@pytest.fixture
def test_db(temp_db_path):
    """Create a test database with complete schema."""
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY,
        command TEXT NOT NULL,
        explanation TEXT,
        category TEXT,
        platform TEXT,
        dangerous INTEGER DEFAULT 0,
        danger_reason TEXT,
        popularity INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS command_tags (
        command_id INTEGER,
        tag TEXT,
        PRIMARY KEY (command_id, tag),
        FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS command_history (
        id INTEGER PRIMARY KEY,
        query TEXT NOT NULL,
        command TEXT NOT NULL,
        executed INTEGER DEFAULT 0,
        success INTEGER DEFAULT 0,
        platform TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS command_fts USING fts5(
        command, explanation, category, tags,
        content='commands',
        content_rowid='id'
    )
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS commands_ai AFTER INSERT ON commands BEGIN
        INSERT INTO command_fts(rowid, command, explanation, category, tags)
        VALUES (new.id, new.command, new.explanation, new.category, 
                (SELECT GROUP_CONCAT(tag, ' ') FROM command_tags WHERE command_id = new.id));
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS commands_ad AFTER DELETE ON commands BEGIN
        DELETE FROM command_fts WHERE rowid = old.id;
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS commands_au AFTER UPDATE ON commands BEGIN
        UPDATE command_fts SET
            command = new.command,
            explanation = new.explanation,
            category = new.category,
            tags = (SELECT GROUP_CONCAT(tag, ' ') FROM command_tags WHERE command_id = new.id)
        WHERE rowid = new.id;
    END;
    ''')
    
    cursor.execute(
        "INSERT INTO commands (command, explanation, category, platform, dangerous) VALUES (?, ?, ?, ?, ?)",
        ("ls -la", "List all files", "file", "linux,macos", 0)
    )
    
    cmd_id = cursor.lastrowid
    cursor.execute("INSERT INTO command_tags (command_id, tag) VALUES (?, ?)", (cmd_id, "file"))
    cursor.execute("INSERT INTO command_tags (command_id, tag) VALUES (?, ?)", (cmd_id, "listing"))
    
    cursor.execute(
        "INSERT INTO commands (command, explanation, category, platform, dangerous, danger_reason) VALUES (?, ?, ?, ?, ?, ?)",
        ("rm -rf *", "Delete everything", "file", "linux,macos", 1, "Dangerous deletion")
    )
    
    cmd_id = cursor.lastrowid
    cursor.execute("INSERT INTO command_tags (command_id, tag) VALUES (?, ?)", (cmd_id, "file"))
    cursor.execute("INSERT INTO command_tags (command_id, tag) VALUES (?, ?)", (cmd_id, "deletion"))
    
    cursor.execute(
        "INSERT INTO command_history (query, command, executed, success, platform) VALUES (?, ?, ?, ?, ?)",
        ("show files", "ls -la", 1, 1, "linux")
    )
    
    conn.commit()
    
    yield conn
    
    conn.close()