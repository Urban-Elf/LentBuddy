from pathlib import Path
import platform

# Determine platform
system = platform.system()
home_dir = Path.home()

if system == "Windows":
    ROOT_PATH = home_dir / "AppData" / "Roaming" / "LentBuddy"
elif system == "Darwin":  # macOS
    ROOT_PATH = home_dir / "Library" / "Application Support" / "LentBuddy"
else:  # Linux or unknown
    ROOT_PATH = home_dir / ".lentbuddy"

LIST_PATH = ROOT_PATH / "lists"

# Create directories
for path in [ROOT_PATH, LIST_PATH]:
    path.mkdir(parents=True, exist_ok=True)
