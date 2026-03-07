import os
from pathlib import Path
from typing import Union
import sys
import curses
import time
import random
import re


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

def is_name_silly(name):
    if re.search(r'[^A-Za-z]', name):
        return True
    return False

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

def shake_effect(stdscr, y, x, s, intensity=2, delay=0.03, iterations=10):
    """
    Shake a text string in place on the screen.

    Args:
        stdscr: curses screen object
        s (str): text to shake
        y, x (int): starting position
        intensity (int): max offset in characters (horizontal)
        delay (float): delay between shake frames
        iterations (int): how many shake cycles to perform
    """
    base_y, base_x = y, x

    for _ in range(iterations):
        # Random horizontal displacement in [-intensity, intensity]
        dx = random.randint(-intensity, intensity)
        dy = 0  # could be random.randint(-intensity, intensity) if vertical shake wanted

        # Clear previous position
        safe_move(stdscr, base_y, 0)
        stdscr.clrtoeol()

        # Draw at new offset
        safe_addstr(stdscr, base_y + dy, base_x + dx, s)
        stdscr.refresh()
        safe_sleep(stdscr, delay)

    # Clear previous position
    safe_move(stdscr, base_y, 0)
    stdscr.clrtoeol()
    # Finally, draw text in original position
    safe_addstr(stdscr, base_y, base_x, s)
    stdscr.refresh()

### HELPER ###


def curses_input(stdscr, prompt, y, x):
    curses.curs_set(1)
    safe_addstr(stdscr, y, x, prompt)
    stdscr.refresh()

    buffer = []
    pos = 0

    while True:
        key = f_getch(stdscr)

        if key in (10, 13):  # Enter
            break
        elif key in (curses.KEY_BACKSPACE, 127):
            if buffer:
                buffer.pop()
                pos -= 1
                safe_addstr(stdscr, y, x + len(prompt), " " * (len(buffer)+1))
        elif key == curses.KEY_DOWN:
            return "__KEY_DOWN__"
        elif key == curses.KEY_RESIZE:
            return "__KEY_RESIZE__"
        elif 32 <= key <= 126:
            buffer.append(chr(key))
            pos += 1

        safe_addstr(stdscr, y, x + len(prompt), "".join(buffer))
        safe_move(stdscr, y, x + len(prompt) + pos)
        stdscr.refresh()

    return "".join(buffer)

def f_getch(stdscr, filter_custom=[]):
    while True:
        key = stdscr.getch()
        if key not in (curses.KEY_DOWN, curses.KEY_UP, curses.KEY_LEFT, curses.KEY_RIGHT) and key not in filter_custom:
            return key
        
def safe_addstr(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        # Shift text to start at 0 if x is negative
        text = text[-x:]
        x = 0
    max_len = max(0, w - x)
    stdscr.addstr(y, x, text[:max_len], attr)

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

def safe_addstr_dialogue(stdscr, y, x, text, attr=0, spec=None):
    """
    -------------------------------------------------------------------------
    Token Reference Table (for future-you):
    -------------------------------------------------------------------------
    1. Default words (no token)
       - Delay: spec['word_delays'][0] (after first word)
       - Whitespace is printed immediately
       
    2. #i#           → Pause only, no text printed
       - Delay: spec['br_delays'][i]
       - Leading whitespace before token is skipped
       - Example: "Hello#1#World" → delays 1 then prints "World"
       
    3. #i TEXT#      → Word block, delay per word
       - Delay: spec['word_delays'][i] for each word
       - Whitespace between words is printed immediately (no delay)
       - Escaping: "\#" to include literal #
       - Example: "#2This is fast#" → delays per word using word_delays[2]
       
    4. =i TEXT=      → Char block, letter by letter
       - Delay: spec['char_delays'][i] per character
       - Escaping: "\=" to include literal =
       - Example: "=0Hello=" → prints each letter with char_delays[0]
       
    5. Escaping
       - Prefix \ to print token characters literally
       - Example: "\#1\#" → prints "#1#" literally
       
    -------------------------------------------------------------------------
    Notes:
    - All delays are optional; defaults used if spec keys missing.
    - All token parsing handles escape sequences to prevent accidental delay.
    -------------------------------------------------------------------------
    """

    if spec is None:
        spec = {
            "word_delays": [0.05],
            "char_delays": [0.015],
            "br_delays": [0.05]  # for pause-only #i# tokens
        }

    pos_x = x
    pos_y = y
    i = 0
    first_word = True
    skip_space_once = False

    def word_delay(idx):
        delays = spec["word_delays"]
        return delays[idx] if idx < len(delays) else delays[0]

    def char_delay(idx):
        delays = spec["char_delays"]
        return delays[idx] if idx < len(delays) else delays[0]

    def br_delay(idx):
        delays = spec.get("br_delays", spec["word_delays"])
        return delays[idx] if idx < len(delays) else delays[0]

    while i < len(text):
        c = text[i]

        # ---------------------------
        # Escape sequence: print literally
        # ---------------------------
        if c == "\\" and i+1 < len(text):
            i += 1
            stdscr.addstr(pos_y, pos_x, text[i], attr)
            pos_x += 1
            i += 1
            continue

        # ---------------------------
        # Pause token: #i#
        # ---------------------------
        if c == "#" and i+2 < len(text) and text[i+1].isdigit() and text[i+2] == "#":
            idx = int(text[i+1])
            safe_sleep(stdscr, br_delay(idx))
            i += 3
            skip_space_once = True
            continue

        # ---------------------------
        # Word block: #i TEXT#
        # ---------------------------
        if c == "#" and i+1 < len(text) and text[i+1].isdigit():
            idx = int(text[i+1])
            i += 2

            block = ""
            while i < len(text) and text[i] != "#":
                # handle escaped #
                if text[i] == "\\" and i+1 < len(text) and text[i+1] == "#":
                    block += "#"
                    i += 2
                else:
                    block += text[i]
                    i += 1
            i += 1  # skip closing #

            bi = 0
            while bi < len(block):
                if block[bi].isspace():
                    stdscr.addstr(pos_y, pos_x, block[bi], attr)
                    pos_x += 1
                    bi += 1
                    continue

                word = ""
                while bi < len(block) and not block[bi].isspace():
                    word += block[bi]
                    bi += 1

                safe_sleep(stdscr, word_delay(idx))
                stdscr.addstr(pos_y, pos_x, word, attr)
                pos_x += len(word)
                stdscr.refresh()

            first_word = False
            continue

        # ---------------------------
        # Char block: =i TEXT=
        # ---------------------------
        if c == "=" and i+1 < len(text) and text[i+1].isdigit():
            idx = int(text[i+1])
            i += 2

            block = ""
            while i < len(text) and text[i] != "=":
                # handle escaped =
                if text[i] == "\\" and i+1 < len(text) and text[i+1] == "=":
                    block += "="
                    i += 2
                else:
                    block += text[i]
                    i += 1
            i += 1  # skip closing =

            for ch in block:
                stdscr.addstr(pos_y, pos_x, ch, attr)
                pos_x += 1
                stdscr.refresh()
                safe_sleep(stdscr, char_delay(idx))
            continue

        # ---------------------------
        # Whitespace
        # ---------------------------
        if c.isspace():
            if skip_space_once:
                skip_space_once = False
                i += 1
                continue
            stdscr.addstr(pos_y, pos_x, c, attr)
            pos_x += 1
            i += 1
            continue

        # ---------------------------
        # Default word
        # ---------------------------
        word = ""
        while i < len(text) and not text[i].isspace() and not text[i] in "#=":
            if text[i] == "\\" and i+1 < len(text) and text[i+1] in "#=":
                i += 1
            word += text[i]
            i += 1

        if not first_word:
            safe_sleep(stdscr, word_delay(0))

        stdscr.addstr(pos_y, pos_x, word, attr)
        pos_x += len(word)
        stdscr.refresh()
        first_word = False
    
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

def safe_clear_line(stdscr, y, x=0):
    safe_move(stdscr, y, x)
    stdscr.clrtoeol()

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