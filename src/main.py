import curses
from datetime import datetime, date
import calendar
import time
import os
import random

from . import localstorage as ls
from . import util
from . import dialogue

WINDOW_WIDTH = 50
EVERDAY_LIST = "everyday.txt"
DAILY_LISTS = "daily/%s-%s.txt"

WELCOME_LINES = [
    "Welcome to LentBuddy (by Urban-Elf)!",
    "",
    "This app allows you to add penances of your choosing",
    "to universal/daily lists, which can then be rolled",
    "each day to randomly select a number of them.",
    "",
    "Inspired by a priest's approach of choosing six penances",
    "for Lent and choosing one randomly to perform each day.",
]

TODAY = date.today().isoformat()
RNG = random.Random(TODAY)

# ---------- Helper functions ----------

def determine_penances(everyday_list, daily_list, count, rng):
    combined_list = everyday_list + daily_list
    rng.shuffle(combined_list)
    return combined_list[:count]

def ellipsis_effect(stdscr, s, y, x, maxwidth=3, iterations=1, delay=0.5):
    for i in range(RNG.randint(1, iterations)):
        util.safe_move(stdscr, y, x)
        stdscr.clrtoeol()
        util.safe_addstr(stdscr, y, x, s)
        stdscr.refresh()
        time.sleep(delay)

        for j in range(maxwidth):
            util.safe_addstr(stdscr, y, x + len(s) + j, ".")
            stdscr.refresh()
            time.sleep(delay)

# ---------- Curses UI functions ----------

def curses_input(stdscr, prompt, y, x):
    curses.curs_set(1)
    util.safe_addstr(stdscr, y, x, prompt)
    stdscr.refresh()

    buffer = []
    pos = 0

    while True:
        key = util.f_getch(stdscr)

        if key in (10, 13):  # Enter
            break
        elif key in (curses.KEY_BACKSPACE, 127):
            if buffer:
                buffer.pop()
                pos -= 1
                util.safe_addstr(stdscr, y, x + len(prompt), " " * (len(buffer)+1))
        elif key == curses.KEY_DOWN:
            return "__KEY_DOWN__"
        elif key == curses.KEY_RESIZE:
            return "__KEY_RESIZE__"
        elif 32 <= key <= 126:
            buffer.append(chr(key))
            pos += 1

        util.safe_addstr(stdscr, y, x + len(prompt), "".join(buffer))
        util.safe_move(stdscr, y, x + len(prompt) + pos)
        stdscr.refresh()

    return "".join(buffer)

#def curses_input(stdscr, prompt, y, x):
#    curses.echo()
#    util.safe_addstr(stdscr, y, x, prompt)
#    stdscr.refresh()
#    s = stdscr.getstr(y, x + len(prompt)).decode()
#    curses.noecho()
#    return s.strip()

def roll_screen_curses(stdscr, everyday_list, daily_list):
    should_tempt = dialogue.should_do_temptation(RNG)

    stdscr.clear()
    util.safe_addstr(stdscr, 0, 0, "Roll today's penances!", curses.color_pair(3) | curses.A_BOLD)
    util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)

    # TODO: Stop it later with today.isoformat() check with stored ls one so you can only roll once a day

    start_options = [
        "Alright, get ready",
        "Let's see what you can do",
        "Processing",
        "Here goes"
    ]

    text_index = RNG.randint(0, len(start_options) - 1)
    start = start_options[text_index]
    ellipsis_effect(stdscr, start, 2, 0, iterations=1)

    time.sleep(1)

    # Lineage easter egg
    should_show_easter_egg_0 = RNG.random() < 0.9
    for i in range(RNG.randint(3, 4 if not should_show_easter_egg_0 else 3)):
        for j in range(3):
            if should_show_easter_egg_0 and i < 2:
                util.safe_move(stdscr, 4, 0)
                stdscr.clrtoeol()
            util.safe_addstr(stdscr, 4, (j*2) + 1, "o" if j % 2 == 0 else "O")  # Add some "rolling" animation
            stdscr.refresh()
            time.sleep(0.6)
            if should_show_easter_egg_0 and i == 2 and j == 2:
                time.sleep(0.7)
                util.safe_addstr(stdscr, 5, 0, "Lineage", curses.color_pair(1) | curses.A_ITALIC)
                stdscr.refresh()
                time.sleep(1.3)
                util.safe_addstr(stdscr, 5, 9, "^ 100% legit", curses.A_ITALIC)
                stdscr.refresh()
                time.sleep(1.3)
        util.safe_move(stdscr, 4, 0)
        stdscr.clrtoeol()
        stdscr.refresh()
        time.sleep(0.6)

    if should_show_easter_egg_0:
        util.safe_move(stdscr, 5, 0)
        stdscr.clrtoeol()
        stdscr.refresh()

    time.sleep(0.6)

    middle_options = [
        "And the penances for today are",
        "Drumroll please",
        "Almost done",
        "Oh, boy"
    ]
    middle = middle_options[text_index]

    ellipsis_effect(stdscr, middle, 4, 0, iterations=RNG.randint(1, 3))
    time.sleep(0.5)

    count = ls.get_instance().get_property("count", -1)

    if count == -1 or RNG.random() < 0.3:
        insisted = False
        set_insisted = False
        while True:
            if set_insisted:
                insisted = True
            util.safe_move(stdscr, 4, 0)
            stdscr.clrtoeol()
            util.safe_addstr(stdscr, 4, 0, "Wait, how many penances did you want?" if count == -1 else f"Still cool with {count} penances? ['d' to continue].")
            util.safe_move(stdscr, 5, 0)
            stdscr.clrtoeol()
            s = curses_input(stdscr, "> ", 5, 0)
            if s == "d" and count != -1:
                break
            try:
                new_count = int(s)
                if new_count < 1:
                    util.safe_move(stdscr, 4, 0)
                    stdscr.clrtoeol()
                    util.safe_addstr(stdscr, 4, 0,"You're worse than us")
                    stdscr.refresh()
                    time.sleep(1.1)
                    continue
                elif new_count < 2:
                    util.safe_move(stdscr, 4, 0)
                    stdscr.clrtoeol()
                    util.safe_addstr(stdscr, 4, 0, "At least two, come on." if not insisted else "Alright, suit yourself.")
                    stdscr.refresh()
                    set_insisted = True
                    time.sleep(1.1 if not insisted else 2)
                    if not insisted:
                        continue
                count = new_count
                ls.get_instance().set_property("count", count)
                break
            except ValueError:
                util.safe_move(stdscr, 4, 0)
                stdscr.clrtoeol()
                util.safe_addstr(stdscr, 4, 0, "Dude, you can't be serious right now.")
                stdscr.refresh()
                time.sleep(1.4)
                continue

    selected = determine_penances(everyday_list, daily_list, count, RNG)
    util.safe_addstr(stdscr, 4, 0, "Your penances for today:")
    util.safe_addstr(stdscr, 5, 0, "-" * WINDOW_WIDTH)
    for i, penance in enumerate(selected, start=6):
        util.safe_addstr(stdscr, i, 0, f"{i}) {penance}")
    util.safe_addstr(stdscr, len(selected), 0, "-" * WINDOW_WIDTH)
    util.safe_addstr(stdscr, len(selected) + 2, 0, "Press any key to return to menu.")
    stdscr.refresh()
    util.f_getch(stdscr)

def edit_lists_curses(stdscr, everyday_list, daily_list):
    pass

def show_welcome_curses(stdscr, extra_lines: list[str]=None, line_delay=0.05):
    stdscr.clear()
    _i = 0
    for i, line in enumerate(WELCOME_LINES):
        util.safe_addstr(stdscr, i, 0, line)
        stdscr.refresh()
        if not len(line.strip()) == 0:
            time.sleep(line_delay)
        _i = i
    if extra_lines:
        for i, line in enumerate(extra_lines):
            util.safe_addstr(stdscr, _i + 1 + i, 0, line)
            stdscr.refresh()
            if not len(line.strip()) == 0:
                time.sleep(line_delay)
            # Finale
            if i == len(extra_lines) - 1:
                _i = _i + 1 + i
    util.f_getch(stdscr)
    for i in range(_i + 1):
        util.safe_move(stdscr, i, 0)
        stdscr.clrtoeol()
        stdscr.refresh()
        list = WELCOME_LINES + (extra_lines if extra_lines else [])
        if not len(list[i].strip()) == 0:
            time.sleep(line_delay)

def main_menu_curses(stdscr, everyday_list, daily_list, show_welcome=False):
    ### Init color pairs ###

    # Good
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    # Evil
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    # Magenta
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    if show_welcome:
        show_welcome_curses(stdscr, [
            "-" * WINDOW_WIDTH,
            "",
            "Press any key to continue."], line_delay=0.08)

    while True:
        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, "Welcome to LentBuddy (by Urban-Elf)! Choose an option.", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr(stdscr, 2, 0, " 1) Roll today's penances!")
        util.safe_addstr(stdscr, 3, 0, " 2) Edit penance lists")
        util.safe_addstr(stdscr, 4, 0, " 3) Settings", curses.color_pair(1))
        util.safe_addstr(stdscr, 5, 0, " 4) What even is this?")
        util.safe_addstr(stdscr, 6, 0, " 5) Quit")
        util.safe_addstr(stdscr, 7, 0, "-" * WINDOW_WIDTH)

        choice = curses_input(stdscr, "> ", 8, 0)

        if choice == "1":
            roll_screen_curses(stdscr, everyday_list, daily_list)
        elif choice == "4":
            show_welcome_curses(stdscr, [
            "-" * WINDOW_WIDTH,
            "",
            "Press any key to return."])
        elif choice == "5":
            break
        elif choice == "__KEY_RESIZE__":
            continue
        else:
            util.safe_addstr(stdscr, 8, 0, "Invalid choice. Press any key.")
            stdscr.refresh()
            util.f_getch(stdscr)

# ---------- Main ----------

def main():
    everyday_list = ["Pray", "Read Scripture", "Help someone"]
    daily_list = ["Extra fast", "Charity act"]

    curses.wrapper(main_menu_curses, everyday_list, daily_list, show_welcome=True)

if __name__ == "__main__":
    main()