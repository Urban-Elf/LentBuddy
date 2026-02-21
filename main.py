from datetime import datetime, date
import calendar
import util
import time
import os
import random
import sys

WINDOW_WIDTH = 50

EVERDAY_LIST = "penances/everyday.txt"
DAILY_LISTS = "penances/daily/%s-%s.txt"
COUNT_FILE = "penances/count.txt"

ENABLE_TEMPTATIONS = True

EVIL_MESSAGES = [
    "Hey, you know that penance you have to do today? Yeah, you can just skip it. No one will know.",
    "Eh, like, don't worry about it. You can just do it tomorrow, or maybe the day after. It’s not like it’s important or anything.",
    "You know, you could just do something else instead. Like, maybe watch a movie or something. That would be way more fun.",
]

# Create a seed based on today's date
today_seed = date.today().isoformat()   # e.g. "2026-02-20"

rng = random.Random(today_seed)
today = datetime.today()

def main():
    # Load list
    daily_list_name = DAILY_LISTS % (today.weekday(), today.strftime("%A"))

    # Main loop
    if not util.path_exists(daily_list_name) or not util.path_exists(EVERDAY_LIST):
        everyday_list = util.load_list(EVERDAY_LIST)
        daily_list = util.load_list(daily_list_name)

        welcome_screen()

        # Set up lists
        util.save_list(EVERDAY_LIST, edit_everday_screen(everyday_list, allow_cancel=False))
        edit_daily_screen()

        util.clear(2)
        main_screen(everyday_list=everyday_list, daily_list=daily_list, clear=False)
    else:
        everyday_list = util.load_list(EVERDAY_LIST)
        daily_list = util.load_list(daily_list_name)

        main_screen(everyday_list=everyday_list, daily_list=daily_list)

def welcome_screen():
    util.label("Welcome to LentBuddy (by Urban-Elf)!")
    util.label()
    util.label("This app allows you to add penances of your choosing")
    util.label("to universal/daily lists, which can then be rolled")
    util.label("each day to randomly select a number of them.")
    util.label()
    util.label("Inspired by a priest's approach of choosing six penances")
    util.label("for Lent and choosing one randomly to perform each day.")
    util.label("-" * WINDOW_WIDTH)
    util.label("Press [Return] to continue...")
    input()

def main_screen(everyday_list: list[str], daily_list: list[str], clear=True):
    input_string = ""
    offset = 1

    if clear:
        util.clear()
    util.label("Welcome to LentBuddy (by Urban-Elf)! Choose an option.")
    util.label("-" * WINDOW_WIDTH)
    util.label(" 1) Roll today's penances!")
    util.label(" 2) Edit penance lists")
    util.label(" 3) What is this monstrosity?")
    util.label(" 4) Quit")
    util.label("-" * WINDOW_WIDTH)

    input_string = input("> ")
    input_string = input_string.strip()

    if input_string == "1":
        util.clear(1)
        roll_screen(everyday_list=everyday_list, daily_list=daily_list)
        
    elif input_string == "2":
        # Set up lists
        util.save_list(EVERDAY_LIST, edit_everday_screen(everyday_list, allow_cancel=False))
        edit_daily_screen()

        util.clear(2)
        main_screen(everyday_list=everyday_list, daily_list=daily_list, clear=False)
    elif input_string == "3":
        util.clear(1)
        welcome_screen()
        util.clear(2)
        main_screen(everyday_list=everyday_list, daily_list=daily_list, clear=False)
    elif input_string == "4":
        return

def determine_penances(everyday_list: list[str], daily_list: list[str], count: int, rng: random.Random):
    # Combine lists and shuffle
    combined_list = everyday_list + daily_list
    rng.shuffle(combined_list)

    # Select 6 penances (or fewer if not enough)
    selected_penances = combined_list[:count]

    return selected_penances

def roll_screen(everyday_list: list[str], daily_list: list[str]):
    global rng

    input_string = ""
    offset = 1

    start = [
        "Alright, get ready...",
        "Let's see what you should do today...",
        "Here goes..."
    ]

    time.sleep(random.random() * 0.5 + 0.4)
    util.label(random.choice(start))
    time.sleep(random.random() * 0.5 + 0.3)
    util.label()

    for i in range(1, 4):
        util.label(" ", noend=True)
        for j in range(3):
            util.label("o " if j % 2 == 0 else "O ", noend=True)
            sys.stdout.flush()
            time.sleep(1)
        util.label("\r", noend=True)
        sys.stdout.write("\033[2K")  # Clear entire line
        sys.stdout.flush()
        time.sleep(1)

    util.label("Your penances for today are", noend=True)
    for j in range(7):
        util.label(".", noend=True)
        sys.stdout.flush()
        time.sleep(0.7)

    time.sleep(1)

    count = 6
    loaded = False

    try:
        with open(COUNT_FILE, "r") as f:
            count = int(f.read().strip())
            loaded = True
    except:
        pass

    if not loaded or rng.random() < 0.3:
        util.label("\r", noend=True)
        sys.stdout.write("\033[2K")  # Clear entire line
        sys.stdout.flush()

        default_label_text = "Wait, how many did you want?" if not loaded else f"Still cool with {count}, or do you want to change it? ['n' to cancel]"
        label_text = default_label_text

        while True:
            util.label(label_text)
        
            input_string = input("> ")
            input_string_stripped = input_string.strip()
            
            if loaded and input_string_stripped == "n":
                break

            try:
                new_count = int(input_string_stripped)
                if new_count > 0:
                    if new_count < 2:
                        for _ in range(3):
                            sys.stdout.write("\033[2K")  # Clear line
                            if _ < 2:
                                sys.stdout.write("\033[1A")  # Move up
                        sys.stdout.flush()
                        label_text = "At least two, come on."
                        continue
                    count = new_count
                    with open(COUNT_FILE, "w") as f:
                        f.write(str(count))
                    break
                else:
                    for _ in range(4):
                        sys.stdout.write("\033[2K")  # Clear line
                        if _ < 2:
                            sys.stdout.write("\033[1A")  # Move up
                    sys.stdout.flush()
                    util.label("Dude, seriously. Positive numbers only.")
                    continue
            except ValueError:
                for _ in range(4):
                    sys.stdout.write("\033[2K")  # Clear line
                    if _ < 2:
                        sys.stdout.write("\033[1A")  # Move up
                sys.stdout.flush()
                util.label("Stop pulling my leg, bro. Just give me a number.")
                continue

    util.label(count)

    #determine_penances(everyday_list, daily_list, , rng)



def pop_list_item(l: list[str]) -> int:
    if len(l) > 0:
        l.pop()
        if len(l) == 0:
            return 3
        else:
            return 2
    return 1

def edit_everday_screen(everyday_list_serial: list[str], allow_cancel=True):
    everyday_list = everyday_list_serial.copy()

    ret_values = []
    if allow_cancel:
        ret_values.append("save")
        ret_values.append("cancel")
    else:
        ret_values.append("d")

    input_string = ""
    offset = 1 # Default to 1 for input() prompt

    while input_string.lower() not in ret_values:
        util.clear(offset)
        offset = 1
        util.label("Add all your general penances one by one.")
        util.label("(i.e. able to be rolled on ANY day of the week)")
        util.label("You will be able to change these later.")
        util.label("-" * WINDOW_WIDTH)
        util.label("Type '-1' to remove the last added.")
        if allow_cancel:
            util.label("Type 'save' or 'cancel' to finish.")
        else:
            util.label("Type 'd' to continue.")
        if len(everyday_list) > 0:
            util.label("-" * WINDOW_WIDTH)
            for penance in everyday_list:
                util.label(penance)
        util.label("-" * WINDOW_WIDTH)

        input_string = input("> ")
        input_string = input_string.strip()

        if len(input_string) == 0:
            continue

        if input_string == "-1":
            offset = pop_list_item(everyday_list)
            continue

        if input_string.lower() not in ret_values:
            everyday_list.append(input_string)
    
    if input_string == "save":
        return everyday_list
    
    return everyday_list_serial

def edit_daily_screen():
    input_string = ""
    offset = 1

    for i in range(len(calendar.day_name)):
        list = daily_loop(calendar.day_name[i], input_string, offset)
        util.save_list(DAILY_LISTS % (i, calendar.day_name[i]), list)

def daily_loop(day_name, input_string: str, offset: int):
    list = []

    while input_string.lower() != "d":
        util.clear(offset)
        offset = 1
        util.label(f"Any special penances specific to {day_name}?")
        util.label()
        util.label("These will be mixed with the everyday ones when rolling.")
        util.label("You will be able to change these later.")
        util.label("-" * WINDOW_WIDTH)
        util.label("Type '-1' to remove the last added.")
        util.label("Type 'd' to continue.")
        if len(list) > 0:
            util.label("-" * WINDOW_WIDTH)
            for penance in list:
                util.label(penance)
        util.label("-" * WINDOW_WIDTH)

        input_string = input("> ")
        input_string = input_string.strip()

        if len(input_string) == 0:
            continue

        if input_string == "-1":
            offset = pop_list_item(list)
            continue

        if input_string.lower() != "d":
            list.append(input_string)

    return list


def angelic_drop():
    input_string = ""
    offset = 1

def temptation_screen():
    input_string = ""
    offset = 1

if __name__ == "__main__":
    main()
