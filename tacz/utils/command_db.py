# tacz/utils/command_db.py
import json
import sqlite3
import re
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class CommandDatabase:
    def __init__(self, db_path=None):
        if not db_path:
            db_dir = Path.home() / ".tacz"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "commands.db"
        
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        
        self.current_platform = self._detect_platform()
    
    def _detect_platform(self) -> str:
        system = platform.system()
        if system == "Darwin":
            return "macos"
        elif system == "Linux":
            return "linux"
        elif system == "Windows":
            return "windows"
        else:
            return "unknown"
    
    def _init_db(self):
        cursor = self.conn.cursor()
        
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
        
        # fts5 virtual table for full-text search
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
        
        # indexed
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_commands_platform ON commands(platform);
        ''')
        
        self.conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM commands")
        if cursor.fetchone()[0] == 0:
            self._preload_common_commands()
    
    def _load_commands_from_json(self):
        try:
            json_path = Path(__file__).parent.parent / "data" / "commands.json"
            
            if not json_path.exists():
                print(f"Commands file not found: {json_path}")
                return {}
            
            with open(json_path, 'r') as f:
                commands_data = json.load(f)
            
            all_commands = []
            for category, commands in commands_data.items():
                for cmd in commands:
                    if "category" not in cmd:
                        cmd["category"] = category
                    all_commands.append(cmd)
            
            return all_commands
        except Exception as e:
            print(f"Error loading commands: {e}")
            return []
    
    def _preload_common_commands(self):
        commands = self._load_commands_from_json()
        
        if not commands:
            commands = [
                {
                    "command": "ls -la", 
                    "explanation": "List all files including hidden ones with details",
                    "category": "file",
                    "platform": "linux,macos",
                    "dangerous": False
                },
                {
                    "command": "grep -r 'pattern' .", 
                    "explanation": "Recursively search for pattern in current directory",
                    "category": "search",
                    "platform": "linux,macos",
                    "dangerous": False
                },
                {
                    "command": "du -sh *", 
                    "explanation": "Show disk usage of all items in current directory",
                    "category": "system",
                    "platform": "linux,macos",
                    "dangerous": False
                }
            ]
        
        cursor = self.conn.cursor()
        for cmd in commands:
            platform = cmd.get("platform", "")
            danger_reason = cmd.get("danger_reason", "") if cmd.get("dangerous", False) else ""
            
            cursor.execute(
                "INSERT INTO commands (command, explanation, category, platform, dangerous, danger_reason) VALUES (?, ?, ?, ?, ?, ?)",
                (cmd["command"], cmd["explanation"], cmd.get("category", ""), platform,
                1 if cmd.get("dangerous", False) else 0, danger_reason)
            )
        
        self.conn.commit()
        print(f"Added {len(commands)} commands to the database")

    def preload_from_json(self, commands_json: List[Dict[str, Any]]):
        cursor = self.conn.cursor()
        
        for cmd in commands_json:
            cursor.execute(
                """INSERT INTO commands 
                (command, explanation, category, platform, dangerous, danger_reason) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cmd["command"],
                    cmd["explanation"],
                    cmd.get("category", ""),
                    cmd.get("platform", ""),
                    1 if cmd.get("dangerous", False) else 0,
                    cmd.get("danger_reason", "")
                )
            )
            command_id = cursor.lastrowid
            
            if "tags" in cmd and command_id:
                for tag in cmd["tags"]:
                    cursor.execute(
                        "INSERT INTO command_tags (command_id, tag) VALUES (?, ?)",
                        (command_id, tag.lower())
                    )
        
        self.conn.commit()
    
    def add_command(self, command: str, explanation: str, category: str = None, 
       platform: str = None, dangerous: bool = False, 
       danger_reason: str = None, tags: List[str] = None) -> int:
        cursor = self.conn.cursor()
        
        cursor.execute(
            "INSERT INTO commands (command, explanation, category, platform, dangerous, danger_reason) VALUES (?, ?, ?, ?, ?, ?)",
            (command, explanation, category, platform, 1 if dangerous else 0, danger_reason)
        )
        command_id = cursor.lastrowid
        
        if tags and command_id:
            for tag in tags:
                cursor.execute(
                    "INSERT OR IGNORE INTO command_tags (command_id, tag) VALUES (?, ?)",
                    (command_id, tag.lower())
                )
            
            cursor.execute(
                "UPDATE commands SET command = command WHERE id = ?",
                (command_id,)
            )
        
        self.conn.commit()
        return command_id
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """hybrid approach (FTS + tag matching)"""
        query = query.strip().lower()
        if not query:
            return []
        
        cursor = self.conn.cursor()
        
        platform_filter = ""
        param_values = []
        
        platform_filter = f"AND (c.platform LIKE ? OR c.platform IS NULL OR c.platform = '')"
        param_values.append(f"%{self.current_platform}%")
        
        fts_query = ' OR '.join(query.split())
        
        cursor.execute(f"""
            SELECT c.*, GROUP_CONCAT(ct.tag) as tags
            FROM command_fts
            JOIN commands c ON command_fts.rowid = c.id
            LEFT JOIN command_tags ct ON c.id = ct.command_id
            WHERE command_fts MATCH ?
            {platform_filter}
            GROUP BY c.id
            ORDER BY c.popularity DESC
            LIMIT ?
        """, [fts_query] + param_values + [limit])
        
        fts_results = [dict(row) for row in cursor.fetchall()]
        
        if len(fts_results) < limit:
            remaining = limit - len(fts_results)
            fts_ids = [r['id'] for r in fts_results]
            
            terms = set(query.split())
            
            cursor.execute(f"""
                SELECT c.id, c.*, GROUP_CONCAT(ct.tag) as tags, COUNT(DISTINCT ct.tag) as tag_matches
                FROM command_tags ct
                JOIN commands c ON ct.command_id = c.id
                WHERE ct.tag IN ({','.join('?' for _ in terms)})
                AND c.id NOT IN ({','.join('?' for _ in fts_ids) if fts_ids else '-1'})
                {platform_filter}
                GROUP BY c.id
                ORDER BY tag_matches DESC, c.popularity DESC
                LIMIT ?
            """, list(terms) + fts_ids + param_values + [remaining])
            
            tag_results = [dict(row) for row in cursor.fetchall()]
            
            combined_results = fts_results + tag_results
        else:
            combined_results = fts_results
        
        for result in combined_results:
            if result.get('tags'):
                result['tags'] = result['tags'].split(',')
            else:
                result['tags'] = []
        
        return combined_results

    def record_history(self, query: str, command: str, executed: bool = False, 
                      success: bool = None, platform: str = None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO command_history (query, command, executed, success, platform) VALUES (?, ?, ?, ?, ?)",
            (query, command, 1 if executed else 0, 1 if success else 0 if success is False else None, platform)
        )
        
        cursor.execute(
            "UPDATE commands SET popularity = popularity + 1 WHERE command = ?",
            (command,)
        )
        
        self.conn.commit()
    
    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM command_history ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def search_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM command_history WHERE query LIKE ? OR command LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        if self.conn:
            self.conn.close()