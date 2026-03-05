import curses
from datetime import datetime, date
import calendar
import time
import os
import random

from . import localstorage as ls
from . import util
from . import dialogue
from . import file_tree

WINDOW_WIDTH = 59
EVERDAY_LIST = file_tree.ROOT_PATH / "everyday.txt"
DAILY_LIST_TEMPLATE = "%s.txt"
DAILY_LISTS = file_tree.ROOT_PATH / "daily"

TODAY = date.today()
RNG = random.Random(TODAY.isoformat())

dialogue.init(RNG)
from .dialogue import MANAGER as D_MANAGER

INITIALIZED_COLORS = False

def daily_file(weekday: int) -> str:
    return DAILY_LISTS / (DAILY_LIST_TEMPLATE % calendar.day_name[weekday])

WELCOME_LINES = [
    "#4Welcome to LentBuddy (by Urban-Elf)!#",
    "",
    "This app allows you to organize your Lenten",
    "penances (of prayer, fasting, and almsgiving)",
    "into lists that you can customize, and then",
    "roll each day to select a number of them randomly!",
    "",
    "The advanage to this is that it encourages one",
    "to broaden the variety of their penances",
    "without the risk of becoming overwhelmed or",
    "losing consistency by the end of the season.",
    "",
    "_Inspired by a certain priest's idea of selecting_",
    "_six penances and rolling them daily with dice._"
]

NAV_ANNOYANCE_MESSAGES = [
    "Invalid option. Press any key.",
    "Bro, that's not even a valid option.",
    "Dude, are you even trying? Press any key.",
    "C'mon, it's not that hard. Press any key.",
    "Alright, last warning. Press any key.",
    "Fine, have it your way. Press any key.",
    "You know what? Just stop.",
]

LIST_ANNOYANCE_MESSAGES = [
    "Too small. Press any key.",
    "Come on, at least two characters. Press any key.",
    "Seriously? Press any key.",
    "Dude, not this again.",
    "I'm starting to think you don't want to add any penances at all.",
    "You know what, get out of here!",
]

# ---------- Helper functions ----------

def determine_penances(everyday_list, count, rng):
    # We load the lists each time we need them instead of just once at the start,
    # since user can edit them in the app and it should reflect immediately
    daily_list = util.load_list(daily_file(TODAY.weekday()))
    # Combine the lists and shuffle
    combined_list = everyday_list + daily_list
    rng.shuffle(combined_list)
    return combined_list[:count]

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

def roll_screen_curses(stdscr, everyday_list):
    should_tempt = D_MANAGER.should_do_temptation()

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
    util.ellipsis_effect(stdscr, start, 2, 0, rng=RNG, iterations=1)

    util.safe_sleep(stdscr, 1)

    # Lineage easter egg
    should_show_easter_egg_0 = RNG.random() < 0.9
    for i in range(RNG.randint(3, 4 if not should_show_easter_egg_0 else 3)):
        for j in range(3):
            if should_show_easter_egg_0 and i < 2:
                util.safe_move(stdscr, 4, 0)
                stdscr.clrtoeol()
            util.safe_addstr(stdscr, 4, (j*2) + 1, "o" if j % 2 == 0 else "O")  # Add some "rolling" animation
            stdscr.refresh()
            util.safe_sleep(stdscr, 0.6)
            if should_show_easter_egg_0 and i == 2 and j == 2:
                util.safe_sleep(stdscr, 0.7)
                util.safe_addstr(stdscr, 5, 0, "Lineage", curses.color_pair(1) | curses.A_ITALIC)
                stdscr.refresh()
                util.safe_sleep(stdscr, 1.3)
                util.safe_addstr(stdscr, 5, 9, "^ 100% legit", curses.A_ITALIC)
                stdscr.refresh()
                util.safe_sleep(stdscr, 1.3)
        util.safe_move(stdscr, 4, 0)
        stdscr.clrtoeol()
        stdscr.refresh()
        util.safe_sleep(stdscr, 0.6)

    if should_show_easter_egg_0:
        util.safe_move(stdscr, 5, 0)
        stdscr.clrtoeol()
        stdscr.refresh()

    util.safe_sleep(stdscr, 0.6)

    middle_options = [
        "And the penances for today are",
        "Drumroll please",
        "Almost done",
        "Oh, boy"
    ]
    middle = middle_options[text_index]

    util.ellipsis_effect(stdscr, middle, 4, 0, rng=RNG, iterations=RNG.randint(1, 3))
    util.safe_sleep(stdscr, 0.5)

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
                    util.safe_sleep(stdscr, 1.1)
                    continue
                elif new_count < 2:
                    util.safe_move(stdscr, 4, 0)
                    stdscr.clrtoeol()
                    util.safe_addstr(stdscr, 4, 0, "At least two, come on." if not insisted else "Alright, suit yourself.")
                    stdscr.refresh()
                    set_insisted = True
                    util.safe_sleep(stdscr, 1.1 if not insisted else 2)
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
                util.safe_sleep(stdscr, 1.4)
                continue

    selected = determine_penances(everyday_list, count, RNG)
    util.safe_move(stdscr, 4, 0)
    stdscr.clrtoeol()
    end = [
        "Your penances for today are:",
        "Today's penances are:"
    ]
    util.safe_addstr(stdscr, 4, 0, RNG.choice(end), curses.color_pair(4))
    util.safe_addstr(stdscr, 5, 0, "-" * WINDOW_WIDTH)
    _i = 6
    for i, penance in enumerate(selected, start=_i):
        util.safe_addstr(stdscr, i, 0, f" - {penance}")
        stdscr.refresh()
        util.safe_sleep(stdscr, 0.5)
        _i = i
    util.safe_addstr(stdscr, _i+1, 0, "-" * WINDOW_WIDTH)
    util.safe_addstr(stdscr, _i+2, 0, "Press any key to return to menu.")
    stdscr.refresh()
    util.f_getch(stdscr)

def edit_lists_curses(stdscr, everyday_list):
    am = dialogue.AnnoyanceManager(NAV_ANNOYANCE_MESSAGES)

    clear_set = dialogue.DialogueSet(D_MANAGER,
                                     good=[
                                        "All lists cleared. Fresh start!",
                                        "Lists cleared! Time for new penances! Press a key.",
                                        "A clean slate for your Lenten journey. Press a key."
                                     ],
                                     bad=[
                                        "Ha ha, good job. You cleared all your penances!",
                                        "Good, good. Now, you don't _really_ need to add them again, do you?"
                                        
                                     ],
                                     neutral=["Lists cleared. Press a key to return."])

    while True:
        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, "Edit penance lists", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr(stdscr, 2, 0, " 1) Edit everyday list")
        util.safe_addstr(stdscr, 3, 0, " 2) Edit daily lists")
        util.safe_addstr(stdscr, 4, 0, " 3) Clear all lists")
        util.safe_addstr(stdscr, 5, 0, " b) <- Back")
        util.safe_addstr(stdscr, 6, 0, "-" * WINDOW_WIDTH)
        choice = curses_input(stdscr, "> ", 7, 0)
        if choice == "1":
            util.clear_effect(stdscr)
            util.save_list(EVERDAY_LIST, edit_list_curses(stdscr, "EVERYDAY", everyday_list))
        elif choice == "2":
            edit_daily_lists_curses(stdscr)
        elif choice == "3":
            util.clear_effect(stdscr)
            util.safe_addstr(stdscr, 0, 0, "Are you sure you want to clear all lists? Type 'yes' to confirm.", curses.color_pair(4))
            util.safe_sleep(stdscr, 0.05)
            confirm = curses_input(stdscr, "> ", 1, 0)
            if confirm.lower() == "yes":
                everyday_list.clear()
                util.save_list(EVERDAY_LIST, everyday_list)
                for i in range(7):
                    util.save_list(daily_file(i), [])
                util.safe_addstr(stdscr, 1, 0, "Lists cleared. Press any key to return.")
                stdscr.refresh()
                util.f_getch(stdscr)
            else:
                util.safe_addstr(stdscr, 1, 0, "Phew, that was close! Press any key to return.")
                util.f_getch(stdscr)
            util.clear_effect(stdscr)
        elif choice == "b":
            util.clear_effect(stdscr)
            break # Returns to main menu
        elif choice == "__KEY_RESIZE__":
            continue # Refresh
        else:
            util.safe_addstr(stdscr, 7, 0, am.bother())
            stdscr.refresh()
            util.f_getch(stdscr)

def edit_list_curses(stdscr, title, list: list[str], first_time=False) -> list[str]:
    am = dialogue.AnnoyanceManager(LIST_ANNOYANCE_MESSAGES)
    
    while True:
        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, f"Editing {title} list", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr(stdscr, 2, 0, "Type your penances individually, pressing ENTER after each.", curses.A_ITALIC)
        util.safe_addstr(stdscr, 3, 0, "Type '-' to remove the most recent one, and 'd' to finish.", curses.A_ITALIC)
        y = 4
        if first_time:
            util.safe_addstr(stdscr, y, 0, "")
            y += 1
            util.safe_addstr(stdscr, y, 0, "You will be able to change these later.", curses.color_pair(4) | curses.A_ITALIC)
            y += 1
        util.safe_addstr(stdscr, y, 0, "-" * WINDOW_WIDTH)
        y += 1
        for i, penance in enumerate(list, start=y):
            util.safe_addstr(stdscr, y, 0, f" - {penance}")
            y += 1
        util.safe_addstr(stdscr, y, 0, "-" * WINDOW_WIDTH)
        y += 1
        choice = curses_input(stdscr, "> ", y, 0)
        clen = len(choice.strip())
        if choice == "d":
            util.clear_effect(stdscr)
            return list
        elif choice == "-":
            if list:
                list.pop()
        elif choice == "__KEY_RESIZE__":
            continue # Refresh
        elif clen > 0:
            if clen < 2:
                util.safe_addstr(stdscr, y, 0, am.bother())
                stdscr.refresh()
                util.safe_sleep(stdscr, 1.2)
                continue
            list.append(choice.strip())

def edit_daily_lists_curses(stdscr):
    am = dialogue.AnnoyanceManager(NAV_ANNOYANCE_MESSAGES)

    while True:
        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, "Choose a day to edit", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr(stdscr, 2, 0, " 1) Monday")
        util.safe_addstr(stdscr, 3, 0, " 2) Tuesday")
        util.safe_addstr(stdscr, 4, 0, " 3) Wednesday")
        util.safe_addstr(stdscr, 5, 0, " 4) Thursday")
        util.safe_addstr(stdscr, 6, 0, " 5) Friday")
        util.safe_addstr(stdscr, 7, 0, " 6) Saturday")
        util.safe_addstr(stdscr, 8, 0, " 7) Sunday")
        util.safe_addstr(stdscr, 9, 0, " b) <- Back")
        util.safe_addstr(stdscr, 10, 0, "-" * WINDOW_WIDTH)
        choice = curses_input(stdscr, "> ", 11, 0)
        if choice in [str(i) for i in range(1, 8)]:
            choice_num = int(choice) - 1
            path = daily_file(choice_num)
            daily_list = util.load_list(path)
            # Edit list and save
            util.save_list(path, edit_list_curses(stdscr, calendar.day_name[choice_num].upper(), daily_list))
        elif choice == "b":
            util.clear_effect(stdscr)
            break # Returns to edit_lists_curses
        elif choice == "__KEY_RESIZE__":
            continue # Refresh
        else:
            util.safe_addstr(stdscr, 11, 0, am.bother())
            stdscr.refresh()
            util.f_getch(stdscr)

def show_welcome_curses(stdscr, extra_lines: list[str]=None, line_delay=0.05):
    stdscr.clear()
    
    lines = WELCOME_LINES + (extra_lines if extra_lines else [])
    first_time = True

    while True:
        for i, line in enumerate(lines):
            util.safe_addstr_tokenized(stdscr, i, 0, line)

            if first_time and not len(line.strip()) == 0:
                stdscr.refresh()
                util.safe_sleep(stdscr, line_delay)
        
        if first_time:
            first_time = False
            stdscr.refresh()

        if not util.f_getch(stdscr) == curses.KEY_RESIZE:
            util.clear_effect(stdscr)
            break

def main_menu_curses(stdscr, everyday_list, show_welcome=False):

    ### Init color pairs ###
    if curses.has_colors() and curses.can_change_color() and not INITIALIZED_COLORS:
        # 1 - Good
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        # 2 - Evil
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        # 3 - Magenta
        curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        # 4 - Yellow
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    if show_welcome:
        show_welcome_curses(stdscr, [
            "-" * WINDOW_WIDTH,
            "",
            "Press any key to continue."], line_delay=0.08)
        
        edit_lists_curses(stdscr, everyday_list)

    am = dialogue.AnnoyanceManager(NAV_ANNOYANCE_MESSAGES)

    while True:
        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, "Welcome to LentBuddy (by Urban-Elf)! Choose an option.", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr(stdscr, 2, 0, " 1) Roll today's penances!", curses.color_pair(4))
        util.safe_addstr(stdscr, 3, 0, " 2) Edit penance lists")
        util.safe_addstr(stdscr, 4, 0, " 3) Settings")
        util.safe_addstr(stdscr, 5, 0, " 4) What even is this?")
        util.safe_addstr_tokenized(stdscr, 6, 0, " b) Quit")
        util.safe_addstr(stdscr, 7, 0, "-" * WINDOW_WIDTH)

        choice = curses_input(stdscr, "> ", 8, 0)

        if choice == "1":
            util.clear_effect(stdscr)
            roll_screen_curses(stdscr, everyday_list)
        elif choice == "2":
            util.clear_effect(stdscr)
            edit_lists_curses(stdscr, everyday_list)
        elif choice == "4":
            util.clear_effect(stdscr)
            show_welcome_curses(stdscr, [
            "-" * WINDOW_WIDTH,
            "",
            "Press any key to return to menu."])
        elif choice == "b":
            break
        elif choice == "__KEY_RESIZE__":
            continue
        else:
            util.safe_addstr(stdscr, 8, 0, am.bother())
            stdscr.refresh()
            util.f_getch(stdscr)

# ---------- Main ----------

def main():
    # NOTE: Always load daily list each time it gets queried instead of just once at the start,
    # since user can edit it in the app and it should reflect immediately

    everyday_list = []

    ls.get_instance().load()

    # load everyday list, or create it if it doesn't exist
    if util.path_exists(EVERDAY_LIST):
        everyday_list = util.load_list(EVERDAY_LIST)
    else:
        util.save_list(EVERDAY_LIST, everyday_list)

    first_time = ls.get_instance().get_property("first_time", True)
    if first_time:
        ls.get_instance().set_property("first_time", False)

    curses.wrapper(main_menu_curses, everyday_list, show_welcome=first_time)

if __name__ == "__main__":
    main()