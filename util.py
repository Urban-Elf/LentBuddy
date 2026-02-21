import os
import sys

active_lines = 0

def label(s: str="", noend=False):
    global active_lines
    print(s, end="" if noend else "\n")
    if not noend:
        active_lines = active_lines + 1

def clear(offset=0):
    global active_lines
    if active_lines > 0:
        active_lines += offset
        # Move up
        sys.stdout.write(f"\033[{active_lines}A")
        
        # Clear each line
        for _ in range(active_lines):
            sys.stdout.write("\033[2K")  # Clear entire line
            sys.stdout.write("\033[1B")  # Move down
        
        # Move back up again
        sys.stdout.write(f"\033[{active_lines}A")
        
        sys.stdout.flush()
        active_lines = 0

def path_exists(path: str):
    return os.path.exists(path)

def load_list(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return f.read().splitlines()
    
def save_list(path: str, l: list[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(l))