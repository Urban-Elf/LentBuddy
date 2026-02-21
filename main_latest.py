import curses
from datetime import datetime, date
import calendar
import time
import os
import random

import localstorage as ls

WINDOW_WIDTH = 50
EVERDAY_LIST = "storage/everyday.txt"
DAILY_LISTS = "storage/daily/%s-%s.txt"
COUNT_FILE = "storage/count.txt"

WELCOME_LINES = [
    "Welcome to LentBuddy (by Urban-Elf)!",
    "",
    "This app allows you to add penances of your choosing",
    "to universal/daily lists, which can then be rolled",
    "each day to randomly select a number of them.",
    "",
    "Inspired by a priest's approach of choosing six penances",
    "for Lent and choosing one randomly to perform each day.",
    "-" * WINDOW_WIDTH,
    "Press any key to return.",
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
        stdscr.move(y, x)
        stdscr.clrtoeol()
        stdscr.addstr(y, x, s)
        stdscr.refresh()
        time.sleep(delay)

        for j in range(3):
            stdscr.addstr(y, x + len(s) + j, ".")
            stdscr.refresh()
            time.sleep(delay)

# ---------- Curses UI functions ----------

def curses_input(stdscr, prompt, y, x):
    curses.echo()
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()
    s = stdscr.getstr(y, x + len(prompt)).decode()
    curses.noecho()
    return s.strip()

def roll_screen_curses(stdscr, everyday_list, daily_list):
    stdscr.clear()
    stdscr.addstr(0, 0, "Roll today's penances!", curses.A_BOLD)
    stdscr.addstr(1, 0, "-" * WINDOW_WIDTH)

    # TODO: Stop it later with today.isoformat() check with stored ls one so you can only roll once a day

    start_options = [
        "Alright, get ready",
        "Let's see what you can do",
        "Processing",
        "Here goes"
    ]
    start = RNG.choice(start_options)
    ellipsis_effect(stdscr, start, 2, 0, iterations=1)

    time.sleep(1)

    # Lineage easter egg
    should_show_easter_egg_0 = RNG.random() < 0.9
    for i in range(RNG.randint(3, 4 if not should_show_easter_egg_0 else 3)):
        for j in range(3):
            if should_show_easter_egg_0 and i < 2:
                stdscr.move(4, 0)
                stdscr.clrtoeol()
            stdscr.addstr(4, (j*2) + 1, "o" if j % 2 == 0 else "O")  # Add some "rolling" animation
            stdscr.refresh()
            time.sleep(0.6)
            if should_show_easter_egg_0 and i == 2 and j == 2:
                time.sleep(0.7)
                stdscr.addstr(5, 0, "Lineage", curses.A_ITALIC)
                stdscr.refresh()
                time.sleep(1)
        stdscr.move(4, 0)
        stdscr.clrtoeol()
        stdscr.refresh()
        time.sleep(0.6)

    if should_show_easter_egg_0:
        stdscr.move(5, 0)
        stdscr.clrtoeol()
        stdscr.refresh()

    time.sleep(0.6)

    middle_options = [
        "And the penances for today are",
        "Drumroll please",
        "Almost done",
        "Oh, boy"
    ]
    middle = RNG.choice(middle_options)

    ellipsis_effect(stdscr, middle, 4, 0, iterations=RNG.randint(1, 3))

    count = ls.get_instance().get_property("count", -1)

    if RNG.random() < 0.3:
        while True:
            s = curses_input(stdscr, "Wait, how many penances did you want?" if count != -1 else f"Still cool with {count}? ['d' to continue].", 4, 0)
            if s == "n":
                break
            try:
                new_count = int(s)
                if new_count < 2:
                    stdscr.addstr(4, 0, "At least two, come on.")
                    stdscr.refresh()
                    time.sleep(1)
                    stdscr.move(4, 0)
                    stdscr.clrtoeol()
                    continue
                count = new_count
                ls.get_instance().set_property("count", count)
                ls.get_instance().serialize()
                break
            except ValueError:
                stdscr.addstr(4, 0, "Give me a valid number.")
                stdscr.refresh()
                time.sleep(1)
                stdscr.move(4, 0)
                stdscr.clrtoeol()

    selected = determine_penances(everyday_list, daily_list, count, RNG)
    stdscr.clear()
    stdscr.addstr(0, 0, "Your penances for today:")
    for i, penance in enumerate(selected, start=1):
        stdscr.addstr(i, 0, f"{i}) {penance}")
    stdscr.addstr(len(selected) + 2, 0, "Press any key to return to menu.")
    stdscr.refresh()
    stdscr.getch()

def main_menu_curses(stdscr, everyday_list, daily_list):
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Welcome to LentBuddy (by Urban-Elf)! Choose an option.", curses.A_BOLD)
        stdscr.addstr(1, 0, "-" * WINDOW_WIDTH)
        stdscr.addstr(2, 0, " 1) Roll today's penances!")
        stdscr.addstr(3, 0, " 2) Edit penance lists")
        stdscr.addstr(4, 0, " 3) Settings")
        stdscr.addstr(5, 0, " 4) What even is this?")
        stdscr.addstr(6, 0, " 5) Quit")
        stdscr.addstr(7, 0, "-" * WINDOW_WIDTH)

        choice = curses_input(stdscr, "> ", 8, 0)

        if choice == "1":
            roll_screen_curses(stdscr, everyday_list, daily_list)
        elif choice == "4":
            stdscr.clear()
            for i, line in enumerate(WELCOME_LINES):
                stdscr.addstr(i, 0, line)
                stdscr.refresh()
                if not len(line.strip()) == 0:
                    time.sleep(0.05)
            stdscr.getch()
        elif choice == "5":
            break
        else:
            stdscr.addstr(8, 0, "Invalid choice. Press any key.")
            stdscr.refresh()
            stdscr.getch()

# ---------- Main ----------

def main():
    everyday_list = ["Pray", "Read Scripture", "Help someone"]
    daily_list = ["Extra fast", "Charity act"]

    curses.wrapper(main_menu_curses, everyday_list, daily_list)

if __name__ == "__main__":
    main()