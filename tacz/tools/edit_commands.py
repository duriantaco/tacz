# tools/edit_commands.py
import json
import os
from pathlib import Path

def load_commands():
    json_path = Path(__file__).parent.parent / "tacz" / "data" / "commands.json"
    
    json_path.parent.mkdir(exist_ok=True)
    
    if json_path.exists():
        with open(json_path, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_commands(commands):
    json_path = Path(__file__).parent.parent / "tacz" / "data" / "commands.json"
    with open(json_path, 'w') as f:
        json.dump(commands, f, indent=2)
    print(f"Saved {sum(len(cmds) for cmds in commands.values())} commands")

def add_commands():
    commands = load_commands()
    
    print("\nAvailable categories:")
    for i, category in enumerate(commands.keys(), 1):
        print(f"{i}. {category}")
    print(f"{len(commands) + 1}. [Create new category]")
    
    choice = input("\nSelect category number or enter new category name: ")
    
    if choice.isdigit() and 1 <= int(choice) <= len(commands):
        category = list(commands.keys())[int(choice) - 1]
    else:
        category = choice.strip().lower().replace(" ", "_")
        if category not in commands:
            commands[category] = []
    
    print(f"\nAdding commands to category: {category}")
    print("Enter commands one by one. Type 'done' when finished.")
    
    command_count = 0
    while True:
        command = input("\nCommand (or 'done'): ").strip()
        if command.lower() == 'done':
            break
        
        explanation = input("Explanation: ").strip()
        platform = input("Platform (linux, macos, windows, or comma-separated): ").strip()
        dangerous = input("Dangerous? (y/n): ").lower() == 'y'
        
        cmd_info = {
            "command": command,
            "explanation": explanation,
            "platform": platform,
            "dangerous": dangerous
        }
        
        if dangerous:
            danger_reason = input("Danger reason: ").strip()
            cmd_info["danger_reason"] = danger_reason
        
        commands[category].append(cmd_info)
        command_count += 1
        print("Command added!")
    
    if command_count > 0:
        save_commands(commands)
        print(f"Added {command_count} commands to category '{category}'")
    else:
        print("No commands added")

def batch_add_commands():
    commands = load_commands()
    
    filename = input("Enter text file path: ").strip()
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    category = None
    added = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('[') and line.endswith(']'):
            category = line[1:-1].strip().lower().replace(' ', '_')
            if category not in commands:
                commands[category] = []
            print(f"Processing category: {category}")
            continue
        
        parts = line.split('|')
        if len(parts) < 3:
            print(f"Skipping invalid line: {line}")
            continue
        
        command = parts[0].strip()
        platform = parts[1].strip()
        explanation = parts[2].strip()
        
        dangerous = False
        danger_reason = ""
        if len(parts) > 3:
            dangerous = parts[3].strip().lower() == 'y'
            if dangerous and len(parts) > 4:
                danger_reason = parts[4].strip()
        
        cmd_info = {
            "command": command,
            "explanation": explanation,
            "platform": platform,
            "dangerous": dangerous
        }
        
        if dangerous:
            cmd_info["danger_reason"] = danger_reason
        
        commands[category].append(cmd_info)
        added += 1
    
    save_commands(commands)
    print(f"Added {added} commands from {filename}")

def main():
    print("Command Editor")
    print("=============")
    print("1. Add commands interactively")
    print("2. Batch add commands from text file")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        add_commands()
    elif choice == '2':
        batch_add_commands()
    else:
        print("Goodbye!")

if __name__ == "__main__":
    main()