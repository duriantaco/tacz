import json
import sqlite3
import platform
import struct
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from rich.console import Console

console = Console()

_EMBED_MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
_MODEL = None

def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        with console.status("Loading embedding model…", spinner="dots"):
            _MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
    return _MODEL

def _embed(text: str) -> bytes:
    vec = _get_model().encode(text, normalize_embeddings=True)
    return vec.astype(np.float32).tobytes()

def _blob_to_vec(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)

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

    def _ensure_fts_schema(self):
        cursor = self.conn.cursor()
        cursor.executescript(
            """
            DROP TABLE IF EXISTS command_fts;
            CREATE VIRTUAL TABLE command_fts USING fts5(
                command,
                explanation,
                category
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO command_fts(rowid, command, explanation, category)
            SELECT c.id, c.command, c.explanation, c.category
            FROM commands c;
            """
        )
        self.conn.commit()

    def _detect_platform(self) -> str:
        system = platform.system()
        if system == "Darwin":
            return "macos"
        if system == "Linux":
            return "linux"
        if system == "Windows":
            return "windows"
        return "unknown"

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY,
                command TEXT NOT NULL,
                explanation TEXT,
                category TEXT,
                platform TEXT,
                dangerous INTEGER DEFAULT 0,
                danger_reason TEXT,
                popularity INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                embedding BLOB
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY,
                query TEXT NOT NULL,
                command TEXT NOT NULL,
                executed INTEGER DEFAULT 0,
                success INTEGER DEFAULT 0,
                platform TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("PRAGMA table_info(commands)")
        if not any(row[1] == "embedding" for row in cursor.fetchall()):
            cursor.execute("ALTER TABLE commands ADD COLUMN embedding BLOB")
        cursor.execute("DROP TABLE IF EXISTS command_fts")
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS command_fts USING fts5(
                command, explanation, category
            )
            """
        )
        cursor.execute("DROP TRIGGER IF EXISTS commands_ai")
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS commands_ai AFTER INSERT ON commands BEGIN
                INSERT INTO command_fts(rowid, command, explanation, category)
                VALUES (new.id, new.command, new.explanation, new.category);
            END;
            """
        )
        cursor.execute("DROP TRIGGER IF EXISTS commands_au")
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS commands_au AFTER UPDATE ON commands BEGIN
                DELETE FROM command_fts WHERE rowid = new.id;
                INSERT INTO command_fts(rowid, command, explanation, category)
                VALUES (new.id, new.command, new.explanation, new.category);
            END;
            """
        )
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS commands_ad AFTER DELETE ON commands BEGIN
                DELETE FROM command_fts WHERE rowid = old.id;
            END;
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_commands_platform ON commands(platform);
            """
        )
        cursor.execute("DELETE FROM command_fts")
        cursor.execute(
            """
            INSERT INTO command_fts(rowid, command, explanation, category)
            SELECT id, command, explanation, category FROM commands
            """
        )
        self.conn.commit()
        self._backfill_embeddings()
        cursor.execute("SELECT COUNT(*) FROM commands")
        if cursor.fetchone()[0] == 0:
            self._preload_common_commands()

    def _backfill_embeddings(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, command, explanation, category FROM commands WHERE embedding IS NULL
            """
        )
        for row_id, cmd, expl, cat in cur.fetchall():
            vec_blob = _embed(f"{cmd}\n{expl or ''}\n{cat or ''}")
            cur.execute("UPDATE commands SET embedding=? WHERE id=?", (vec_blob, row_id))
        self.conn.commit()

    def _load_commands_from_json(self):
        try:
            json_path = Path(__file__).parent.parent / "data" / "commands.json"
            if not json_path.exists():
                return {}
            with open(json_path, "r") as f:
                commands_data = json.load(f)
            all_commands = []
            for category, commands in commands_data.items():
                for cmd in commands:
                    if "category" not in cmd:
                        cmd["category"] = category
                    all_commands.append(cmd)
            return all_commands
        except Exception:
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
                    "dangerous": False,
                },
                {
                    "command": "grep -r 'pattern' .",
                    "explanation": "Recursively search for pattern in current directory",
                    "category": "search",
                    "platform": "linux,macos",
                    "dangerous": False,
                },
                {
                    "command": "du -sh *",
                    "explanation": "Show disk usage of all items in current directory",
                    "category": "system",
                    "platform": "linux,macos",
                    "dangerous": False,
                },
            ]
        cursor = self.conn.cursor()
        for cmd in commands:
            vec_blob = _embed(f"{cmd['command']}\n{cmd['explanation']}\n{cmd.get('category', '')}")
            cursor.execute(
                """
                INSERT INTO commands (command, explanation, category, platform, dangerous, danger_reason, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cmd["command"],
                    cmd["explanation"],
                    cmd.get("category", ""),
                    cmd.get("platform", ""),
                    1 if cmd.get("dangerous", False) else 0,
                    cmd.get("danger_reason", ""),
                    vec_blob,
                ),
            )
        self.conn.commit()

    def preload_from_json(self, commands_json: List[Dict[str, Any]]):
        cursor = self.conn.cursor()
        for cmd in commands_json:
            vec_blob = _embed(f"{cmd['command']}\n{cmd['explanation']}\n{cmd.get('category', '')}")
            cursor.execute(
                """
                INSERT INTO commands (command, explanation, category, platform, dangerous, danger_reason, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cmd["command"],
                    cmd["explanation"],
                    cmd.get("category", ""),
                    cmd.get("platform", ""),
                    1 if cmd.get("dangerous", False) else 0,
                    cmd.get("danger_reason", ""),
                    vec_blob,
                ),
            )
        self.conn.commit()

    def add_command(
        self,
        command: str,
        explanation: str,
        category: str = None,
        platform: str = None,
        dangerous: bool = False,
        danger_reason: str = None,
    ) -> int:
        cursor = self.conn.cursor()
        vec_blob = _embed(f"{command}\n{explanation or ''}\n{category or ''}")
        cursor.execute(
            """
            INSERT INTO commands (command, explanation, category, platform, dangerous, danger_reason, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                command,
                explanation,
                category,
                platform,
                1 if dangerous else 0,
                danger_reason,
                vec_blob,
            ),
        )
        command_id = cursor.lastrowid
        self.conn.commit()
        return command_id

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        q_vec = _blob_to_vec(_embed(query))
        q_norm = np.linalg.norm(q_vec)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM commands
            WHERE (platform LIKE ? OR platform IS NULL OR platform = '')
              AND embedding IS NOT NULL
            """,
            (f"%{self.current_platform}%",),
        )
        rows = [dict(r) for r in cursor.fetchall()]
        if not rows:
            return []
        mat = np.stack([_blob_to_vec(r["embedding"]) for r in rows])
        norms = np.linalg.norm(mat, axis=1)
        sims = (mat @ q_vec) / (norms * q_norm + 1e-9)
        pops = np.array([r.get("popularity", 0) for r in rows], dtype=np.float32)
        scores = sims * (1 + 0.1 * pops)
        top_idx = scores.argsort()[-limit:][::-1]
        return [rows[i] for i in top_idx if scores[i] > 0.15]

    def record_history(
        self,
        query: str,
        command: str,
        executed: bool = False,
        success: bool = None,
        platform: str = None,
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO command_history (query, command, executed, success, platform)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                query,
                command,
                1 if executed else 0,
                1 if success else 0 if success is False else None,
                platform,
            ),
        )
        cursor.execute(
            "UPDATE commands SET popularity = popularity + 1 WHERE command = ?",
            (command,),
        )
        self.conn.commit()

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM command_history ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def search_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM command_history
            WHERE query LIKE ? OR command LIKE ?
            ORDER BY timestamp DESC LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()