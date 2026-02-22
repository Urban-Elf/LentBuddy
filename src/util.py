import os
import sys
import curses

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

################## NEW ##################

def f_getch(stdscr):
    while True:
        key = stdscr.getch()
        if key not in (curses.KEY_DOWN, curses.KEY_UP, curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_REFRESH):
            return key
        
def safe_addstr(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    if y >= h or x >= w:
        return
    stdscr.addstr(y, x, text[:w - x], attr)

def safe_move(stdscr, y, x):
    """
    Move the cursor to (y, x) safely.
    If the coordinates are outside the window, clamp them to the edge.
    """
    max_y, max_x = stdscr.getmaxyx()

    # Clamp y and x to valid range
    safe_y = max(0, min(y, max_y - 1))
    safe_x = max(0, min(x, max_x - 1))

    try:
        stdscr.move(safe_y, safe_x)
    except curses.error:
        pass  # Ignore if curses still complains (rare)