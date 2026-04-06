import sys
from src.main import main
from src.updater import LOCKFILE, self_update, run_updater, VERSION

# Create lock file to signal the app is running
#with open(LOCKFILE, "w") as f:
#    print(f"Creating lock file at {LOCKFILE} with PID {os.getpid()}")
#    f.write(str(os.getpid()))

# Ensure lock is removed on exit
#def remove_lock():
#    try:
#        print("Cleaning up lock file...")
#        os.remove(LOCKFILE)
#    except FileNotFoundError:
#        pass
#atexit.register(remove_lock)

def _init_app():
    # If updater mode, run updater and exit
    #if "--apply-update" in sys.argv:
    #    run_updater()
    #    sys.exit(0)

    # CLI options
    args = sys.argv[1:]
    if args:
        if args[0] in ("--version", "-v", "version"):
            print(f"lentbuddy v{VERSION} (by Urban-Elf)")
            return
        elif args[0] in ("--help", "-h", "help"):
            print("Usage: lentbuddy [options]")
            print("Options:\n  --version, -v, version   Show version\n  --help, -h, help        Show help")
            return

    # Self-update
    #if self_update():
    #    return

    # Start main app
    main()

if __name__ == "__main__":
    _init_app()