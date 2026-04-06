import platform
import sys
from src.main import main
from src.updater import apply_pending_update, self_update, VERSION

def _init_app():
    args = sys.argv[1:]

    # Check if there's at least one argument
    if args and args[0] in ("--version", "-v", "version"):
        print(f"lentbuddy v{VERSION} (by Urban-Elf)")
        return
    
    if platform.system().lower() == "windows":
        apply_pending_update()

    if self_update():
        return

    main()

if __name__ == "__main__":
    _init_app()