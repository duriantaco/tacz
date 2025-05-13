# tacz/utils/db_populator.py
import json
from pathlib import Path
from tacz.utils.command_db import CommandDatabase

def populate_database(force_rebuild=False):
    """Populate the command database from the commands data file"""
    db = CommandDatabase()
    
    if not force_rebuild:
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM commands")
        count = cursor.fetchone()[0]
        if count > 50:
            return
    
    commands_file = Path(__file__).parent.parent / "data" / "commands.json"
    if not commands_file.exists():
        print(f"Warning: Commands file not found at {commands_file}")
        return
    
    with open(commands_file, 'r') as f:
        commands_data = json.load(f)
    
    if force_rebuild:
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM commands")
        db.conn.commit()
    
    for category, tasks in commands_data.items():
        for task, platforms in tasks.items():
            for platform, commands in platforms.items():
                for cmd_info in commands:
                    db.add_command(
                        command=cmd_info["command"],
                        explanation=cmd_info["explanation"],
                        category=category,
                        platform=platform,
                        dangerous=cmd_info.get("dangerous", False),
                        danger_reason=cmd_info.get("danger_reason", "")
                    )
    
    print(f"Database populated with {len(commands_data)} categories of commands")