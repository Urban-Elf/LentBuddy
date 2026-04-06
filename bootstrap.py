import platform
import sys
from src.main import main
from src.updater import self_update, run_updater, VERSION

def _init_app():
    if "--apply-update" in sys.argv:
        run_updater()
        sys.exit(0)

    args = sys.argv[1:]

    # Check if there's at least one argument
    if args:
        if args[0] in ("--version", "-v", "version"):
            print(f"lentbuddy v{VERSION} (by Urban-Elf)")
            return
        elif args[0] in ("--help", "-h", "help"):
            print("Usage: lentbuddy [options]")
            print("Options:")
            print("  --version, -v, version   Show version information")
            print("  --help, -h, help        Show this help message")
            return

    if self_update():
        return

    # Start app
    main()

if __name__ == "__main__":
    _init_app()