import json
from pathlib import Path

config_dir = Path.home() / ".dictation-app"
config_file = config_dir / "config.json"

print(f"Checking {config_file}")
if config_file.exists():
    with open(config_file, 'r') as f:
        data = json.load(f)
        print(f"Current hotkey in file: {data.get('hotkey')}")
else:
    print("File does not exist")
