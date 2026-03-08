from pathlib import Path
import platform

# Determine platform
system = platform.system()
home_dir = Path.home()

ROOT_PATH = home_dir / ".lentbuddy"
LIST_PATH = ROOT_PATH / "lists"

# Create directories
for path in [ROOT_PATH, LIST_PATH]:
    path.mkdir(parents=True, exist_ok=True)
