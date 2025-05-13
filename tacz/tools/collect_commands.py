# tools/collect_commands.py

import json
import os
from pathlib import Path

def load_existing_commands():
    """Load existing commands file or create new structure"""
    commands_file = Path(__file__).parent.parent / "tacz" / "data" / "commands.json"
    if commands_file.exists():
        with open(commands_file, 'r') as f:
            return json.load(f)
    else:
        commands_file.parent.mkdir(exist_ok=True)
        return {}

def save_commands(commands_data):
    """Save commands to JSON file"""
    commands_file = Path(__file__).parent.parent / "tacz" / "data" / "commands.json"
    with open(commands_file, 'w') as f:
        json.dump(commands_data, f, indent=2)
    print(f"Commands saved to {commands_file}")

def add_command_interactive():
    """Add a command interactively"""
    commands_data = load_existing_commands()
    
    category = input("Category (e.g., file_management, system_info): ").strip()
    task = input("Task (e.g., list_files, check_memory): ").strip()
    platform = input("Platform (linux, macos, windows, or comma-separated): ").strip()
    command = input("Command: ").strip()
    explanation = input("Explanation: ").strip()
    dangerous = input("Is dangerous? (y/n): ").strip().lower() == 'y'
    danger_reason = input("Danger reason (if dangerous): ").strip() if dangerous else ""
    
    if category not in commands_data:
        commands_data[category] = {}
    if task not in commands_data[category]:
        commands_data[category][task] = {}
    if platform not in commands_data[category][task]:
        commands_data[category][task][platform] = []
    
    cmd_info = {
        "command": command,
        "explanation": explanation
    }
    if dangerous:
        cmd_info["dangerous"] = True
        cmd_info["danger_reason"] = danger_reason
    
    commands_data[category][task][platform].append(cmd_info)
    
    save_commands(commands_data)
    print("Command added successfully!")

def bulk_add_from_file(filename):
    """Add commands in bulk from a specially formatted text file"""
    commands_data = load_existing_commands()
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    current_category = None
    current_task = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('=='):
            current_category = line.strip('= ').lower().replace(' ', '_')
            if current_category not in commands_data:
                commands_data[current_category] = {}
            print(f"Processing category: {current_category}")
            continue
            
        if line.startswith('--'):
            current_task = line.strip('- ').lower().replace(' ', '_')
            if current_task not in commands_data[current_category]:
                commands_data[current_category][current_task] = {}
            print(f"Processing task: {current_task}")
            continue
        
        if line.startswith('linux:') or line.startswith('macos:') or line.startswith('windows:'):
            platform, cmd = line.split(':', 1)
            cmd = cmd.strip()
            if '|' in cmd:
                cmd, explanation = cmd.split('|', 1)
                cmd = cmd.strip()
                explanation = explanation.strip()
            else:
                explanation = "No explanation provided"
            
            if platform not in commands_data[current_category][current_task]:
                commands_data[current_category][current_task][platform] = []
            
            commands_data[current_category][current_task][platform].append({
                "command": cmd,
                "explanation": explanation
            })
    
    save_commands(commands_data)
    print("Bulk import completed!")

def main():
    """Main function"""
    print("Command Collection Utility")
    print("=========================")
    print("1. Add a command interactively")
    print("2. Bulk add from text file")
    print("3. Exit")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == '1':
        add_command_interactive()
    elif choice == '2':
        filename = input("Enter filename: ").strip()
        bulk_add_from_file(filename)
    elif choice == '3':
        print("Goodbye!")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()