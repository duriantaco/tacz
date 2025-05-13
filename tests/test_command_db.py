import pytest
import sqlite3
from tacz.utils.command_db import CommandDatabase

def _setup_test_db(db):
    """Helper function to properly set up test database with FTS tables."""
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