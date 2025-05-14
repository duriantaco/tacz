import pytest
import sqlite3
from tacz.utils.command_db import CommandDatabase
from unittest.mock import patch

def _setup_test_db(db):
    cursor = db.conn.cursor()
    
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS command_fts USING fts5(
        command, explanation, category, tags
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
        DELETE FROM command_fts WHERE rowid = new.id;
        INSERT INTO command_fts(rowid, command, explanation, category, tags)
        VALUES (
            new.id, 
            new.command, 
            new.explanation, 
            new.category, 
            (SELECT GROUP_CONCAT(tag, ' ') FROM command_tags WHERE command_id = new.id)
        );
    END;
    ''')
    
    cursor.execute(
        "INSERT INTO commands (command, explanation, category, platform, dangerous) VALUES (?, ?, ?, ?, ?)",
        ("ls -la", "List all files", "file", "linux,macos", 0)
    )
    cmd_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO command_tags (command_id, tag) VALUES (?, ?)", (cmd_id, "file"))
    cursor.execute("INSERT INTO command_tags (command_id, tag) VALUES (?, ?)", (cmd_id, "list"))
    
    cursor.execute(
        "INSERT INTO command_fts (rowid, command, explanation, category, tags) VALUES (?, ?, ?, ?, ?)",
        (cmd_id, "ls -la", "List all files", "file", "file list")
    )
    
    db.conn.commit()

def test_command_db_initialization(temp_db_path):
    """Test CommandDatabase initializes with the correct path."""
    db = CommandDatabase(temp_db_path)
    assert db.db_path == temp_db_path
    assert isinstance(db.conn, sqlite3.Connection)
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert "commands" in tables
    assert "command_history" in tables
    assert "command_tags" in tables
    
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS command_fts USING fts5(
        command, explanation, category, tags
    )
    ''')
    db.conn.commit()
    
    db.close()

def test_add_command(temp_db_path):
    """Test adding a command to the database."""
    db = CommandDatabase(temp_db_path)
    
    cmd_id = db.add_command(
        command="echo 'hello world'",
        explanation="Print hello world",
        category="basic",
        platform="linux,macos,windows",
        dangerous=False
    )
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM commands WHERE id = ?", (cmd_id,))
    cmd = cursor.fetchone()
    
    assert cmd is not None
    assert cmd["command"] == "echo 'hello world'"
    assert cmd["explanation"] == "Print hello world"
    assert cmd["category"] == "basic"
    assert cmd["platform"] == "linux,macos,windows"
    assert cmd["dangerous"] == 0
    
    db.close()

def test_add_command_with_tags(temp_db_path):
    db = CommandDatabase(str(temp_db_path))
    cmd_id = db.add_command("ls -la", "List files", tags=["files", "list"])

    rows = db.conn.execute(
        "SELECT tag FROM command_tags WHERE command_id=?", (cmd_id,)
    ).fetchall()
    assert {r[0] for r in rows} == {"files", "list"}

def test_record_history(temp_db_path):
    db = CommandDatabase(str(temp_db_path))
    
    cmd_id = db.add_command("echo hi", "Say hello")
    
    query = "show greeting"
    command = "echo hi"
    db.record_history(query=query, command=command, executed=True, success=True, platform="darwin")
    
    row = db.conn.execute(
        "SELECT query, command, executed, success FROM command_history"
    ).fetchone()
    
    assert row[0] == "show greeting"
    assert row[1] == "echo hi"
    assert row[2] == 1                # executed (True -> 1)
    assert row[3] == 1                # success (True -> 1)

def test_get_history(temp_db_path):
    db = CommandDatabase(str(temp_db_path))
    db.conn.executemany(
        "INSERT INTO command_history (query, command, executed, success, platform, timestamp) "
        "VALUES (?, ?, 1, 1, 'linux', '2023-01-01')",
        [("check disk", "df -h"), ("show files", "ls -la")],
    )
    history = db.get_history(limit=10)
    assert len(history) == 2
    assert history[0]["query"] == "check disk"  # first row returned

def test_search_history(temp_db_path):
    db = CommandDatabase(str(temp_db_path))
    db.conn.execute(
        "INSERT INTO command_history (query, command, executed, success, platform, timestamp) "
        "VALUES ('show files', 'ls -la', 1, 1, 'linux', '2023-01-01')"
    )
    results = db.search_history("files", limit=5)
    assert results and results[0]["command"] == "ls -la"

def test_search(test_db, temp_db_path):
    """Test searching for commands."""
    db = CommandDatabase(temp_db_path)
    _setup_test_db(db)
    
    results = db.search("file")
    
    assert len(results) > 0, "Search should return at least one result"
    assert any("ls" in cmd["command"] for cmd in results), "Should find ls command"
    
    db.close()

def test_db_close(temp_db_path):
    db = CommandDatabase(temp_db_path)
    db.close()
    
    with pytest.raises(sqlite3.ProgrammingError):
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM commands")

def test_detect_platform(temp_db_path):
    """Test platform detection logic."""
    db = CommandDatabase(temp_db_path)
    
    with patch('platform.system', return_value='Darwin'):
        assert db._detect_platform() == "macos"
    
    with patch('platform.system', return_value='Linux'):
        assert db._detect_platform() == "linux"
    
    with patch('platform.system', return_value='Windows'):
        assert db._detect_platform() == "windows"
    
    with patch('platform.system', return_value='Unknown'):
        assert db._detect_platform() == "unknown"

def test_load_commands_from_json(temp_db_path):
    """Test loading commands from JSON file."""
    db = CommandDatabase(temp_db_path)
    
    with patch('pathlib.Path.exists', return_value=False), \
         patch('builtins.print') as mock_print:
        result = db._load_commands_from_json()
        assert result == {}
        mock_print.assert_called_once()
    
    mock_json_data = {
        "file": [
            {"command": "ls", "explanation": "List files", "category": "file", "platform": "linux,macos"}
        ],
        "system": [
            {"command": "top", "explanation": "Show processes", "platform": "linux,macos"}
        ]
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', create=True), \
         patch('json.load', return_value=mock_json_data):
        result = db._load_commands_from_json()
        assert len(result) == 2
        assert result[0]["command"] == "ls"
        assert result[0]["category"] == "file"
        assert result[1]["command"] == "top"
        assert result[1]["category"] == "system"
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', create=True), \
         patch('json.load', side_effect=Exception("JSON error")), \
         patch('builtins.print') as mock_print:
        result = db._load_commands_from_json()
        assert result == []
        mock_print.assert_called_once()

def test_preload_from_json(temp_db_path):
    """Test preloading commands from JSON structure."""
    db = CommandDatabase(temp_db_path)
    
    test_commands = [
        {
            "command": "test-cmd",
            "explanation": "Test command",
            "category": "test",
            "platform": "all",
            "dangerous": True,
            "danger_reason": "For testing",
            "tags": ["test", "demo"]
        },
        {
            "command": "another-cmd", 
            "explanation": "Another test",
            "tags": ["demo"]
        }
    ]
    
    db.preload_from_json(test_commands)
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM commands WHERE command IN (?, ?)", 
                  ("test-cmd", "another-cmd"))
    count = cursor.fetchone()[0]
    assert count == 2
    
    cursor.execute("SELECT COUNT(*) FROM command_tags WHERE tag IN (?, ?)", 
                  ("test", "demo"))
    tag_count = cursor.fetchone()[0]
    assert tag_count == 3

def test_search_empty_query(temp_db_path):
    """Test search with empty query."""
    db = CommandDatabase(temp_db_path)
    
    results = db.search("")
    assert results == []
    
    results = db.search("   ")
    assert results == []

def test_search_no_matches(temp_db_path):
    """Test search with no matching results."""
    db = CommandDatabase(temp_db_path)
    
    db.add_command("test command", "A test", category="test")
    
    results = db.search("nonexistent")
    assert results == []

def test_search_with_complex_conditions(temp_db_path):
    """Test search with more complex conditions."""
    with patch.object(CommandDatabase, '_preload_common_commands'):
        db = CommandDatabase(temp_db_path)
        
        db.add_command("ls -la", "List all files", category="file",
                      platform="linux,macos", tags=["list", "files"])
    
        db.add_command("grep -i pattern file.txt", "Case insensitive search",
                      category="search", platform="linux,macos", tags=["grep", "search"])
    
        db.add_command("find . -name pattern", "Find files by name",
                      category="search", platform="linux,macos", tags=["find", "files"])
    
        results = db.search("grep")
        assert len(results) > 0
        assert any("grep" in cmd["command"] for cmd in results)
    
        results = db.search("search")
        assert len(results) >= 2
    
        results = db.search("files list")
        assert any("ls" in cmd["command"] for cmd in results)
    
        with patch.object(db, 'current_platform', 'windows'):
            results = db.search("list")
            assert len(results) == 0

def test_update_command_popularity(temp_db_path):
    """Test that command popularity is updated when recording history."""
    db = CommandDatabase(temp_db_path)
    
    cmd_id = db.add_command("test command", "A test")
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT popularity FROM commands WHERE id=?", (cmd_id,))
    initial_popularity = cursor.fetchone()[0]
    
    db.record_history("test", "test command")
    
    cursor.execute("SELECT popularity FROM commands WHERE id=?", (cmd_id,))
    updated_popularity = cursor.fetchone()[0]
    
    assert updated_popularity == initial_popularity + 1