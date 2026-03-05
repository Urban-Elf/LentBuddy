import os
from pathlib import Path
from typing import Union
import sys
import curses
import time

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

PathLike = Union[str, Path]

def path_exists(path: PathLike) -> bool:
    return Path(path).exists()

def load_list(path: PathLike) -> list[str]:
    path = Path(path)
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()

def save_list(path: PathLike, items: list[str]) -> None:
    path = Path(path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(items), encoding="utf-8")

################## NEW ##################

### EFFECTS ###


def ellipsis_effect(stdscr, s, y, x, rng, maxwidth=3, iterations=1, delay=0.5):
    for i in range(rng.randint(1, iterations)):
        safe_move(stdscr, y, x)
        stdscr.clrtoeol()
        safe_addstr(stdscr, y, x, s)
        stdscr.refresh()
        safe_sleep(stdscr, delay)

        for j in range(maxwidth):
            safe_addstr(stdscr, y, x + len(s) + j, ".")
            stdscr.refresh()
            safe_sleep(stdscr, delay)

def clear_effect(stdscr, delay=0.05):
    max_y, max_x = stdscr.getmaxyx()
    for i in range(max_y):
        safe_move(stdscr, i, 0)
        line = stdscr.instr(i, 0).decode("utf-8").rstrip()
        stdscr.clrtoeol()
        stdscr.refresh()
        if not len(line) == 0:
            safe_sleep(stdscr, delay)

### HELPER ###

def f_getch(stdscr, filter_custom=[]):
    while True:
        key = stdscr.getch()
        if key not in (curses.KEY_DOWN, curses.KEY_UP, curses.KEY_LEFT, curses.KEY_RIGHT) and key not in filter_custom:
            return key
        
def safe_addstr(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    if y >= h or x >= w:
        return
    stdscr.addstr(y, x, text[:w - x], attr)

def safe_addstr_tokenized(stdscr, y, x, text, attr=0):
    pos = x
    i = 0
    bold = False
    ital = False
    color = 0

    while i < len(text):
        c = text[i]

        # ESCAPE SEQUENCE: backslash prints next char literally
        if c == "\\" and i + 1 < len(text):
            i += 1
            c = text[i]  # take the next char literally
            cur_attr = attr
            if bold:
                cur_attr |= curses.A_BOLD
            if ital and hasattr(curses, "A_ITALIC"):
                cur_attr |= curses.A_ITALIC
            if color:
                cur_attr |= curses.color_pair(color)
            safe_addstr(stdscr, y, pos, c, cur_attr)
            pos += 1
            i += 1
            continue

        # toggle bold
        if c == "*":
            bold = not bold
            i += 1
            continue

        # toggle italics
        if c == "_":
            ital = not ital
            i += 1
            continue

        # color token #x
        if c == "#" and i + 1 < len(text) and text[i+1].isdigit():
            color = int(text[i+1])
            i += 2
            continue

        # reset color
        if c == "#":
            color = 0
            i += 1
            continue

        cur_attr = attr
        if bold:
            cur_attr |= curses.A_BOLD
        if ital and hasattr(curses, "A_ITALIC"):
            cur_attr |= curses.A_ITALIC
        if color:
            cur_attr |= curses.color_pair(color)

        safe_addstr(stdscr, y, pos, c, cur_attr)
        pos += 1
        i += 1

def safe_addstr_dialogue(stdscr, x, y, text, spec=None):
    """
    Slowly prints text to stdscr.
    
    Modes:
    - Default: word by word, delay spec['word_delays'][0]
    - #i TEXT #: word block with delay spec['word_delays'][i]
    - =i TEXT =: letter by letter with delay spec['char_delays'][i]
    
    text: str
    x, y: start positions
    spec: dict with 'word_delays' and 'char_delays'
    """
    if spec is None:
        spec = {"word_delays":[0.05], "char_delays":[0.015]}

    pos_x = x
    pos_y = y
    i = 0
    while i < len(text):
        c = text[i]

        # Word block token: #i ... #
        if c == "#" and i+1 < len(text) and text[i+1].isdigit():
            idx = int(text[i+1])
            i += 2
            block = ""
            while i < len(text) and text[i] != "#":
                block += text[i]
                i += 1
            i += 1  # skip closing #
            words = block.split(" ")
            for word in words:
                stdscr.addstr(pos_y, pos_x, word + " ")
                pos_x += len(word) + 1
                stdscr.refresh()
            time.sleep(spec["word_delays"][idx] if idx < len(spec["word_delays"]) else spec["word_delays"][0])
            continue

        # Char block token: =i ... =
        if c == "=" and i+1 < len(text) and text[i+1].isdigit():
            idx = int(text[i+1])
            i += 2
            block = ""
            while i < len(text) and text[i] != "=":
                block += text[i]
                i += 1
            i += 1  # skip closing =
            for ch in block:
                stdscr.addstr(pos_y, pos_x, ch)
                pos_x += 1
                stdscr.refresh()
                time.sleep(spec["char_delays"][idx] if idx < len(spec["char_delays"]) else spec["char_delays"][0])
            continue

        # Default: print one word at a time
        if c.isspace():
            stdscr.addstr(pos_y, pos_x, c)
            pos_x += 1
            i += 1
            continue

        # Grab full word
        word = ""
        while i < len(text) and not text[i].isspace():
            word += text[i]
            i += 1
        stdscr.addstr(pos_y, pos_x, word)
        pos_x += len(word)
        stdscr.refresh()
        time.sleep(spec["word_delays"][0])

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

def safe_sleep(stdscr, seconds):
    """
    Sleeps for `seconds` while flushing any keypresses in the buffer.
    """
    stdscr.nodelay(True)  # make getch non-blocking
    end_time = time.time() + seconds
    while time.time() < end_time:
        try:
            while stdscr.getch() != -1:  # flush all keys
                pass
        except curses.error:
            pass
        time.sleep(0.01)  # small sleep to avoid busy loop
    stdscr.nodelay(False)  # restore blocking getch