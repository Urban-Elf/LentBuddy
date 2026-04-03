import curses
from datetime import date
import calendar
import hashlib
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

TODAY.strftime("%Y-%m-%d")

dialogue.init(RNG)
from .dialogue import MANAGER as D_MANAGER

INITIALIZED_COLORS = False

def daily_file(weekday: int) -> str:
    return DAILY_LISTS / (DAILY_LIST_TEMPLATE % calendar.day_name[weekday])

# ---------- Helper functions ----------
def determine_penances(everyday_list, count):
    penance_freq = ls.get_instance().get_property("penance_freq", 0)

    if penance_freq == 1:
        iso = TODAY.isocalendar()
        seed_str = f"{iso.year}-{iso.week}"
    elif penance_freq == 2:
        seed_str = TODAY.strftime("%Y-%m")
    else:
        seed_str = TODAY.isoformat()

    daily_list = util.load_list(daily_file(TODAY.weekday())) if penance_freq == 0 else []
    combined_list = everyday_list + daily_list

    def score(item):
        h = hashlib.sha256(
            (seed_str + repr(item)).encode()
        ).hexdigest()
        return int(h, 16)

    combined_list.sort(key=score)
    return combined_list[:count]

# ---------- Curses UI functions ----------

def roll_screen_curses(stdscr, everyday_list):
    init_spec = {"word_delays":[0.1], "char_delays":[0.01, 0.07], "br_delays":[1.1, 0.9]}

    stdscr.clear()
    util.safe_addstr(stdscr, 0, 0, "Roll today's penances!", curses.color_pair(3) | curses.A_BOLD)
    util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)

    if len(everyday_list) == 0:
        util.safe_addstr_dialogue(stdscr, 3, 0, "=0No penances have been added to the lists!= #1# =0Do you want to add some now?= [y/n]", spec=init_spec)
        choice = util.curses_input(stdscr, "> ", 4, 0)
        if choice.lower() == "y":
            util.clear_effect(stdscr)
            edit_lists_curses(stdscr, everyday_list)
            if len(everyday_list) == 0:
                util.safe_addstr_dialogue(stdscr, 1, 0, "=0Still no penances have been added!= #1# =0Press a key to return to menu.=", spec=init_spec)
                stdscr.refresh()
                util.f_getch(stdscr)
                util.clear_effect(stdscr)
                return
            else:
                roll_screen_curses(stdscr, everyday_list)
                return
        else:
            util.safe_addstr_dialogue(stdscr, 5, 0, "=0You can add penances via option (2) in the menu.= #1# =0Press a key to return.=", spec=init_spec)
            stdscr.refresh()
            util.f_getch(stdscr)
            util.clear_effect(stdscr)
            return

    # TODO: Stop it later with today.isoformat() check with stored ls one so you can only get roll anims once a day

    start_text_options = [
        "Alright, get ready",
        "Processing",
        "Here goes",
        "Rolling the computer dice",
        "Getting Grant out of bed"
    ]

    t_index = RNG.randint(0, len(start_text_options) - 1)
    start_text = start_text_options[t_index]
    util.ellipsis_effect(stdscr, start_text, 2, 0, rng=RNG, iterations=RNG.randint(1, 2))
    #util.safe_addstr_dialogue(stdscr, 2, 0, start_text, spec=init_spec)

    util.safe_sleep(stdscr, 0.5 + RNG.random() * 0.5)

    ####### Lineage easter egg #######
    should_show_easter_egg_0 = RNG.random() < 0.1
    for i in range(RNG.randint(3, 4 if not should_show_easter_egg_0 else 3)):
        for j in range(3):
            if should_show_easter_egg_0 and i < 2:
                util.safe_clear_line(stdscr, 4, 0)
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
        util.safe_clear_line(stdscr, 4, 0)
        stdscr.refresh()
        util.safe_sleep(stdscr, 0.6)

    if should_show_easter_egg_0:
        util.safe_clear_line(stdscr, 5, 0)
        stdscr.refresh()
    ###################################

    util.safe_sleep(stdscr, 0.6)

    middle_text_options = [
        "And the penances for today are",
        "Almost done",
        "Drumroll please",
        "Checking the faces",
        "Okay, that was a terrible idea"
    ]
    middle_text = middle_text_options[t_index]
    #util.safe_addstr_dialogue(stdscr, 4, 0, middle_text, spec=init_spec)
    util.ellipsis_effect(stdscr, middle_text, 4, 0, rng=RNG, iterations=RNG.randint(1, 3))
    util.safe_sleep(stdscr, 0.4 + RNG.random() * 0.2)

    low_bound_set = dialogue.DialogueSet(D_MANAGER,
                                         good=[
                                             "You can do better than that!",
                                         ],
                                         bad=[
                                             "You're worse than us.",
                                         ],
                                         neutral=[
                                             "Has to be at least 1!"
                                         ])

    count = ls.get_instance().get_property("penance_count", -1)

    if count < 1 or (count == 1 and RNG.random() < 0.15):
        insisted = False
        set_insisted = False
        while True:
            if set_insisted:
                insisted = True
            util.safe_clear_line(stdscr, 4, 0)
            util.safe_addstr(stdscr, 4, 0, "Wait, how many penances did you want?" if count < 1 else f"Still alright with {count} penance? ['y' to skip]")
            util.safe_clear_line(stdscr, 5, 0)
            s = util.curses_input(stdscr, "> ", 5, 0)
            if s == "d" and not count < 1:
                break
            try:
                new_count = int(s)
                if new_count < 1:
                    util.safe_clear_line(stdscr, 4, 0)
                    util.safe_addstr(stdscr, 4, 0, low_bound_set.get_message(), low_bound_set.get_color())
                    stdscr.refresh()
                    util.safe_sleep(stdscr, 1.1)
                    continue
                elif new_count < 2:
                    util.safe_clear_line(stdscr, 4, 0)
                    util.safe_addstr(stdscr, 4, 0, "At least two, come on." if not insisted else "Alright, suit yourself.")
                    stdscr.refresh()
                    set_insisted = True
                    util.safe_sleep(stdscr, 1.1 if not insisted else 2)
                    if not insisted:
                        continue
                ls.get_instance().set_property("penance_count", new_count)
                count = new_count
                break
            except ValueError:
                util.safe_clear_line(stdscr, 4, 0)
                util.safe_addstr(stdscr, 4, 0, "Dude, you can't be serious right now.")
                stdscr.refresh()
                util.safe_sleep(stdscr, 1.4)
                continue

    penance_screen_curses(stdscr, everyday_list, count)

def penance_screen_curses(stdscr, everyday_list, count, view=False):
    spec = {"word_delays":[0.05], "char_delays":[0.01, 0.007, 0.004], "br_delays":[0.4, 0.8]}

    stdscr.clear()
    util.safe_addstr(stdscr, 0, 0, "Roll today's penances!" if not view else "View today's penances", curses.color_pair(3) | curses.A_BOLD)
    util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)

    penance_list = determine_penances(everyday_list, count)

    y = 3
    util.safe_clear_line(stdscr, y, 0)
    end_text_options = [
        "=0Your penances for today are=:",
        "=0Today's penances are=:"
    ]
    util.safe_addstr_dialogue(stdscr, y, 0, RNG.choice(end_text_options), curses.color_pair(4), spec=spec)
    y += 1
    util.safe_addstr(stdscr, y, 0, "-" * WINDOW_WIDTH)
    y += 1
    _i = y
    if len(penance_list) != 0:
        for i, penance in enumerate(penance_list, start=_i):
            util.safe_addstr_dialogue(stdscr, i, 0, f"=1 - {penance}=", spec=spec)
            stdscr.refresh()
            util.safe_sleep(stdscr, 0.3)
            _i = i
    else:
        util.safe_addstr_dialogue(stdscr, _i, 0, " =1- None! =#0# =1(How did we even get here?)=#1#", curses.A_ITALIC, spec=spec)
        util.safe_sleep(stdscr, 0.4)
    util.safe_addstr(stdscr, _i+1, 0, "-" * WINDOW_WIDTH)
    util.safe_addstr_dialogue(stdscr, _i+2, 0, "=1Press any key to return to the menu.=", spec=spec)
    stdscr.refresh()
    util.f_getch(stdscr)

    ls.get_instance().set_property("last_roll", TODAY.isoformat())

    util.clear_effect(stdscr)

def edit_lists_curses(stdscr, everyday_list, first_time=False):
    am = dialogue.AnnoyanceManager(dialogue.NAV_ANNOYANCE_MESSAGES)

    clear_set = dialogue.DialogueSet(D_MANAGER,
                                     good=[
                                        "All lists cleared. Fresh start!",
                                        "Lists cleared! Time for new penances! Press a key.",
                                        "A clean slate for your Lenten journey. Press a key."
                                     ],
                                     bad=[
                                        "Ha ha, good job. You cleared all your penances.",
                                        "Good, good. Now, you don't _really_ need to add them again, do you?",
                                        "Well, _that_ was a holy move. You cleared all penances. Press a key."
                                     ],
                                     neutral=["Lists cleared. Press a key to return."])
    
    cancel_set = dialogue.DialogueSet(D_MANAGER,
                                      good=[
                                        "Don't want to? That's okay too.",
                                        "May you grow closer to God during this holy season!",
                                        "Hey, wrong menu, completely understandable. This program is a labyrinth."
                                      ],
                                      bad=[
                                        "You're, backing out now? Oh...",
                                        "Blast it--I mean, lists _not_ cleared! Press a key...",
                                        "Dude, seriously. Getting my hopes up for nothing."
                                      ],
                                      neutral=[
                                          "Canceled. Press a key to return."
                                      ])

    changed = False

    while True:
        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, "Edit penance lists", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr(stdscr, 2, 0, " 1) Edit everyday list")
        util.safe_addstr(stdscr, 3, 0, " 2) Edit daily lists")
        y = 4
        if not first_time:
            util.safe_addstr(stdscr, y, 0, " 3) Clear all lists")
            y += 2
        util.safe_addstr(stdscr, y, 0, " d) -> Finish setup! ->" if first_time else " b) <- Back <-")
        y += 1
        util.safe_addstr(stdscr, y, 0, "-" * WINDOW_WIDTH)
        y += 1
        choice = util.curses_input(stdscr, "> ", y, 0)
        if choice == "1":
            result = edit_list_curses(stdscr, "EVERYDAY", "These penances are _always able_ to be rolled.", everyday_list)
            util.save_list(EVERDAY_LIST, result[0])
            if not changed:
                changed = result[1]
        elif choice == "2":
            result = edit_daily_lists_curses(stdscr)
            if not changed:
                changed = result
        elif (not first_time and choice == "3"):
            util.clear_effect(stdscr)
            util.safe_addstr(stdscr, 0, 0, "Are you sure you want to clear all lists? Type 'yes' to confirm.", curses.color_pair(4))
            util.safe_sleep(stdscr, 0.05)
            confirm = util.curses_input(stdscr, "> ", 1, 0)
            if confirm.lower() == "yes":
                everyday_list.clear()
                util.save_list(EVERDAY_LIST, everyday_list)
                for i in range(7):
                    util.save_list(daily_file(i), [])
                util.safe_addstr_tokenized(stdscr, 2, 0, clear_set.get_message(), clear_set.get_color())
                stdscr.refresh()
                util.f_getch(stdscr)
            else:
                util.safe_addstr(stdscr, 2, 0, cancel_set.get_message(), cancel_set.get_color())
                util.f_getch(stdscr)
            util.clear_effect(stdscr)
        elif (first_time and choice == "d") or (not first_time and choice == "b"):
            util.clear_effect(stdscr)
            if changed:
                ls.get_instance().set_property("last_roll", "")
                ls.get_instance().set_property("reroll", True)
            break # Returns to main menu
        elif choice == "__KEY_RESIZE__":
            continue # Refresh
        else:
            util.safe_addstr(stdscr, y, 0, am.bother())
            stdscr.refresh()
            util.f_getch(stdscr)

def edit_list_curses(stdscr, title, desc, list: list[str], first_time=False) -> list[str]:
    am = dialogue.AnnoyanceManager(dialogue.LIST_ANNOYANCE_MESSAGES)
    
    new_list = list.copy()

    def list_changed() -> bool:
        if len(new_list) != len(list):
            return True
        for a, b in zip(new_list, list):
            if a != b:
                return True
        return False

    while True:
        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, f"Editing {title} list", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr_tokenized(stdscr, 2, 0, desc)
        util.safe_addstr(stdscr, 3, 0, " ")
        util.safe_addstr(stdscr, 4, 0, "Type your penances individually, pressing ENTER after each.", curses.A_ITALIC)
        util.safe_addstr(stdscr, 5, 0, "Type '-' to remove the most recent one, and 'b' to finish.", curses.A_ITALIC)
        y = 6
        if first_time:
            util.safe_addstr(stdscr, y, 0, "")
            y += 1
            util.safe_addstr(stdscr, y, 0, "You will be able to change these later.", curses.color_pair(4) | curses.A_ITALIC)
            y += 1
        util.safe_addstr(stdscr, y, 0, "-" * WINDOW_WIDTH)
        y += 1
        for i, penance in enumerate(new_list, start=y):
            util.safe_addstr(stdscr, y, 0, f" - {penance}")
            y += 1
        util.safe_addstr(stdscr, y, 0, "-" * WINDOW_WIDTH)
        y += 1
        choice = util.curses_input(stdscr, "> ", y, 0)
        clen = len(choice.strip())
        if choice == "b":
            util.clear_effect(stdscr)
            return (new_list, list_changed())
        elif choice == "-":
            if new_list:
                new_list.pop()
        elif choice == "__KEY_RESIZE__":
            continue # Refresh
        elif clen > 0:
            if clen < 2:
                util.safe_clear_line(stdscr, y)
                util.safe_addstr(stdscr, y, 0, am.bother())
                stdscr.refresh()
                util.f_getch(stdscr)
                continue
            new_list.append(choice.strip())

def edit_daily_lists_curses(stdscr):
    am = dialogue.AnnoyanceManager(dialogue.NAV_ANNOYANCE_MESSAGES)

    changed = False

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
        util.safe_addstr(stdscr, 9, 0, " b) <- Back <-")
        util.safe_addstr(stdscr, 10, 0, "-" * WINDOW_WIDTH)
        choice = util.curses_input(stdscr, "> ", 11, 0)
        if choice in [str(i) for i in range(1, 8)]:
            choice_num = int(choice) - 1
            path = daily_file(choice_num)
            daily_list = util.load_list(path)
            # Edit list and save
            day_name = calendar.day_name[choice_num]
            result = edit_list_curses(stdscr, day_name.upper(), f"These penances can only be rolled on {day_name}.", daily_list)
            util.save_list(path, result[0])
            if not changed:
                changed = result[1]
        elif choice == "b":
            util.clear_effect(stdscr)
            break # Returns to edit_lists_curses
        elif choice == "__KEY_RESIZE__":
            continue # Refresh
        else:
            util.safe_addstr(stdscr, 11, 0, am.bother())
            stdscr.refresh()
            util.f_getch(stdscr)

    return changed

def settings_curses(stdscr):
    am = dialogue.AnnoyanceManager(dialogue.NAV_ANNOYANCE_MESSAGES)
    int_am = dialogue.AnnoyanceManager(dialogue.NON_INTEGRAL_ANNOYANCE_MESSEGES)

    penance_freq_changed = False

    while True:
        do_dialogue = ls.get_instance().get_property("do_dialogue", False)
        penance_count = ls.get_instance().get_property("penance_count", -1)

        penance_freq = ls.get_instance().get_property("penance_freq", 0)
        freq_value_count = 3
        # bound it
        penance_freq = max(min(penance_freq, freq_value_count - 1), 0)
        penance_freq_options = ["#2DAILY# (default)", "#4WEEKLY#", "#1MONTHLY#"]
        penance_freq_str = penance_freq_options[penance_freq]

        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, "Settings", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr(stdscr, 2, 0, " 0) Edit name & gender (for dialogue)")
        util.safe_addstr_tokenized(stdscr, 3, 0, f" 1) Set daily penance count" + (f" (current: #4{penance_count}#)" if penance_count > 0 else ""))
        util.safe_addstr_tokenized(stdscr, 4, 0, " 2) Randomize penances: " + penance_freq_str)
        util.safe_addstr_tokenized(stdscr, 5, 0, " 3) Enable dialogue:    " + ("#2ON# (not yet implemented)" if do_dialogue else "#1OFF#"))
        util.safe_addstr(stdscr, 7, 0, " r) Reset to defaults")
        util.safe_addstr(stdscr, 8, 0, " b) <- Back <-")
        util.safe_addstr(stdscr, 9, 0, "-" * WINDOW_WIDTH)
        y = 10
        choice = util.curses_input(stdscr, "> ", y, 0)
        if choice == "0":
            util.clear_effect(stdscr)
            personal_stuff_curses(stdscr)
        elif choice == "1":
            util.safe_clear_line(stdscr, y)
            util.safe_addstr(stdscr, y, 0, "Type new daily penance count: ", curses.color_pair(4))
            y += 1
            choice_2 = util.curses_input(stdscr, "> ", y, 0)
            try:
                new_count = int(choice_2)
                if new_count < 1:
                    util.safe_clear_line(stdscr, y)
                    util.safe_addstr(stdscr, y, 0, "That's ridiculous!")
                    util.f_getch(stdscr)
                    continue
                ls.get_instance().set_property("penance_count", new_count)
                # continue loop
            except ValueError:
                util.safe_clear_line(stdscr, y)
                util.safe_addstr(stdscr, y, 0, int_am.bother())
                util.f_getch(stdscr)
        elif choice == "2":
            ls.get_instance().set_property("penance_freq", (penance_freq + 1) % freq_value_count)
            penance_freq_changed = True
        elif choice == "3":
            ls.get_instance().set_property("do_dialogue", not do_dialogue)
        elif choice == "r":
            util.safe_clear_line(stdscr, y)
            util.safe_addstr(stdscr, y, 0, "Really reset all settings? Type 'yes' to confirm.", curses.color_pair(4))
            y += 1
            choice_2 = util.curses_input(stdscr, "> ", y, 0)
            if choice_2 == "yes":
                ls.get_instance().reset()
                # Make sure welcome doesn't get shown again
                ls.get_instance().set_property("first_time", False)
                util.safe_clear_line(stdscr, y)
                util.safe_addstr(stdscr, y, 0, "All settings reset. Press a key to continue.")
                util.f_getch(stdscr)
                # Go to PI setup
                util.clear_effect(stdscr)
                personal_stuff_curses(stdscr)
                # Then back to main menu
                break
            else:
                util.safe_clear_line(stdscr, y)
                util.safe_addstr(stdscr, y, 0, "Canceled. Press a key to continue.")
                util.f_getch(stdscr)
                # continue loop
        elif choice == "b":
            if penance_freq_changed and penance_freq > 0:
                # Require re-roll
                ls.get_instance().set_property("last_roll", "")
                ls.get_instance().set_property("reroll", True)
                # Warn of effects
                util.safe_addstr_tokenized(stdscr, y+1, 0, "Because (2) is " + penance_freq_options[penance_freq] + ", daily lists will be *ignored*! Press any key.")
                stdscr.refresh()
                util.f_getch(stdscr)
            util.clear_effect(stdscr)
            break # Returns to edit_lists_curses
        elif choice == "__KEY_RESIZE__":
            continue # Refresh
        else:
            util.safe_clear_line(stdscr, y)
            util.safe_addstr(stdscr, y, 0, am.bother())
            stdscr.refresh()
            util.f_getch(stdscr)

def show_welcome_curses(stdscr, extra_lines: list[str]=None, line_delay=0.05):
    stdscr.clear()
    
    lines = dialogue.WELCOME_LINES + (extra_lines if extra_lines else [])
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

def personal_stuff_curses(stdscr, q_offset=0):
    am = dialogue.AnnoyanceManager(dialogue.NAV_ANNOYANCE_MESSAGES)

    questions = [
        {
            "prompt": "What's your name?",
            "ls_key": "name",
            "type": "input",
            "filter": lambda s: not util.is_name_silly(s) and len(s) <= 20 and len(s) >= 2,
            "error": "That's a silly name!",
            "success": "=0Welcome to LentBuddy,= #0# =0%s!= #1# =0Press any key to continue.="
        },
        {
            "prompt": "What's your gender?",
            "ls_key": "gender",
            "type": "choice",
            "options": [
                {"id": "male", "text": "Male"},
                {"id": "female", "text": "Female"},
                {"id": "abstain", "text": "Ain't no way I'm answering random questions in a program I got off GitHub."}
            ],
            "success": {
                "2": {"text": "=0Welp.= #1# =0Press any key to continue.=", "good": False, "bad_text": "=1Ha,= #2# =0did you really think I was going to let you off that easily?= #1#"},
                "default": {"text": "=0Choice saved!= #1# =0Press any key to continue.=", "good": True}
            }
        }
    ]

    spec = {"word_delays":[0.05], "char_delays":[0.02, 0.01], "br_delays":[0.09, 0.9, 0.15]}

    q_index = 0 + q_offset

    while q_index < len(questions):
        stdscr.clear()
        q_data = questions[q_index]

        util.safe_addstr(stdscr, 0, 0, "Introduce yourself!", curses.color_pair(4))
        util.safe_addstr(stdscr, 1, 0, " ")
        util.safe_addstr(stdscr, 2, 0, "(This is stored locally on your computer and is only used", curses.A_ITALIC)
        util.safe_addstr(stdscr, 3, 0, "to personalize dialogue in the app, so you can opt out!)", curses.A_ITALIC)
        util.safe_addstr(stdscr, 4, 0, "-" * WINDOW_WIDTH)
        # Uses __NULL__ since the user can't use special chars in actual values
        c_name = ls.get_instance().get_property(q_data["ls_key"], "__NULL__")
        util.safe_addstr(stdscr, 5, 0, q_data["prompt"] + (" (Currently %s)" % c_name if q_data["type"] == "input" and c_name != "__NULL__" else ""))
        stdscr.refresh()
        # last y used was 5, so start at 6
        y = 6
        if q_data["type"] == "choice":
            util.safe_addstr(stdscr, y, 0, " ") # Blank line
            y += 1
            for i, option in enumerate(q_data["options"]):
                util.safe_addstr(stdscr, y, 0, f" {i+1}) {option['text']}")
                y += 1
            util.safe_addstr(stdscr, y, 0, " ") # Blank line
            y += 1
        choice = util.curses_input(stdscr, "> ", y, 0)
        if choice == "__KEY_RESIZE__":
            continue # Refresh
        else:
            if q_data["type"] == "choice":
                try:
                    choice_num = int(choice) - 1
                    if choice_num < 0 or choice_num >= len(q_data["options"]):
                        raise ValueError()
                    choice_id = q_data["options"][choice_num]["id"]
                    ls.get_instance().set_property(q_data["ls_key"], choice_id)

                    success_key = "default"
                    for key in q_data["success"]:
                        if key == "default":
                            continue

                        if "-" in key:
                            lo, hi = map(int, key.split("-"))
                            if lo <= choice_num <= hi:
                                success_key = key
                                break
                        else:
                            if choice_num == int(key):
                                success_key = key
                                break
                    success_data = q_data["success"][success_key]
                    util.safe_clear_line(stdscr, y)
                    util.safe_addstr_dialogue(stdscr, y, 0, success_data["text"], spec=spec)
                    util.f_getch(stdscr)
                    if not success_data["good"]:
                        util.safe_sleep(stdscr, 1)
                        util.safe_clear_line(stdscr, y)
                        util.safe_addstr_dialogue(stdscr, y, 0, success_data["bad_text"], spec=spec)
                        y += 1
                        util.safe_addstr_dialogue(stdscr, y, 0, "=1Press a key to retry.=", spec=spec)
                        util.f_getch(stdscr)
                        continue
                    q_index += 1
                except ValueError:
                    util.safe_clear_line(stdscr, y)
                    util.safe_addstr(stdscr, y, 0, am.bother())
                    y += 1
                    stdscr.refresh()
                    util.f_getch(stdscr)
                    continue
            elif q_data["type"] == "input":
                choice_stripped = choice.strip()
                if not q_data["filter"](choice_stripped):
                    util.safe_clear_line(stdscr, y)
                    util.safe_addstr(stdscr, y, 0, q_data["error"])
                    y += 1
                    stdscr.refresh()
                    util.safe_sleep(stdscr, 1.2)
                    continue
                ls.get_instance().set_property(q_data["ls_key"], choice_stripped)
                util.safe_clear_line(stdscr, y)
                util.safe_addstr_dialogue(stdscr, y, 0, q_data["success"] % choice_stripped, spec=spec)
                util.f_getch(stdscr)
                q_index += 1
    
    util.clear_effect(stdscr)

def main_menu_curses(stdscr, everyday_list, show_welcome=False):

    ### Init color pairs ###
    if curses.has_colors() and curses.can_change_color() and not INITIALIZED_COLORS:
        # 1 - Good
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        # 2 - Bad
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        # 3 - Magenta
        curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        # 4 - Yellow
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    stdscr.keypad(True)

    if show_welcome:
        show_welcome_curses(stdscr, [
            "-" * WINDOW_WIDTH,
            "",
            "Press any key to continue."], line_delay=0.08)
    
    gd = ls.get_instance().get_property("gender", "abstain")
    if not ls.get_instance().get_property("submitted_personal_stuff", False) or gd == "abstain":
        personal_stuff_curses(stdscr, q_offset=1 if gd == "abstain" else 0)
        ls.get_instance().set_property("submitted_personal_stuff", True)

    D_MANAGER.set_gender(ls.get_instance().get_property("gender", "male"))

    if show_welcome:
        edit_lists_curses(stdscr, everyday_list, first_time=True)

    am = dialogue.AnnoyanceManager(dialogue.NAV_ANNOYANCE_MESSAGES)

    while True:
        penances_rolled = ls.get_instance().get_property("last_roll", "") == TODAY.isoformat()
        reroll = ls.get_instance().get_property("reroll", False)

        stdscr.clear()
        util.safe_addstr(stdscr, 0, 0, "Welcome to LentBuddy (by Urban-Elf)! Choose an option.", curses.color_pair(3) | curses.A_BOLD)
        util.safe_addstr(stdscr, 1, 0, "-" * WINDOW_WIDTH)
        util.safe_addstr_tokenized(stdscr, 2, 0, "#4 1) " + ("Re-roll" if reroll else "Roll") + " today's penances!#" if not penances_rolled else " 1) View today's penances")
        util.safe_addstr(stdscr, 3, 0, " 2) Edit penance lists")
        util.safe_addstr(stdscr, 4, 0, " 3) Settings")
        util.safe_addstr(stdscr, 5, 0, " 4) What even is this?")
        util.safe_addstr_tokenized(stdscr, 7, 0, " b) <- Quit <-")
        util.safe_addstr(stdscr, 8, 0, "-" * WINDOW_WIDTH)

        y = 9
        choice = util.curses_input(stdscr, "> ", y, 0)

        if choice == "1":
            util.clear_effect(stdscr)
            if penances_rolled:
                penance_screen_curses(stdscr, everyday_list, ls.get_instance().get_property("penance_count", -1), view=True)
            else:
                roll_screen_curses(stdscr, everyday_list)
        elif choice == "2":
            util.clear_effect(stdscr)
            edit_lists_curses(stdscr, everyday_list)
        elif choice == "3":
            util.clear_effect(stdscr)
            settings_curses(stdscr)
        elif choice == "4":
            util.clear_effect(stdscr)
            show_welcome_curses(stdscr, [
            "-" * WINDOW_WIDTH,
            "",
            "Press any key to return to menu."])
        elif choice == "b":
            did_joke = ls.get_instance().get_property("did_quit_joke", False)
            if not did_joke:
                util.safe_addstr(stdscr, y, 0, "Hey! Are you sure you want to quit? [y/n]")
                # next line refreshes screen so no direct call required
                choice_2 = util.curses_input(stdscr, "> ", y+1, 0)
                if len(choice_2) < 1 or (len(choice_2) > 0 and choice_2.lower()[0] != "y"):
                    util.safe_clear_line(stdscr, y)
                    util.safe_addstr(stdscr, y, 0, "Oh, that's a relief.")
                    stdscr.refresh()
                    util.safe_sleep(stdscr, 1.2)
                    continue
                # Yep, we straight up ignore it otherwise.
                util.safe_addstr_tokenized(stdscr, y+2, 0, "Are you _positive_? [Y/N]")
                choice_3 = util.curses_input(stdscr, "> ", y+3, 0)
                if len(choice_3) < 1 or (len(choice_3) > 0 and choice_3.lower()[0] != "y"):
                    util.safe_clear_line(stdscr, y+2)
                    util.safe_addstr(stdscr, y+2, 0, "I always knew you were joking.")
                    stdscr.refresh()
                    util.safe_sleep(stdscr, 1.2)
                    continue
                # Exit
                ls.get_instance().set_property("did_quit_joke", True)
                util.ellipsis_effect(stdscr, "Fine", y+4, 0, RNG, iterations=1)
                util.safe_sleep(stdscr, 0.3)
            break
        elif choice == "__KEY_RESIZE__":
            continue
        else:
            util.safe_clear_line(stdscr, y)
            util.safe_addstr(stdscr, y, 0, am.bother())
            stdscr.refresh()
            util.f_getch(stdscr)

# ---------- Main ----------

def main():
    # NOTE: Always load daily list each time it gets queried instead of just once at the start,
    # since user can edit it in the app and it should reflect immediately

    # TODO: Maybe add CLI flags (edit lists, roll lists) on a per-user basis for integrations
    # (like to allow for bots to run this as a backend of sorts)
    #   - Isolate files on a per-client basis (so .lentbuddy/Jim/)
    #   - Reserve .lentbuddy/__local__ for local runs of the full app (frontend as well)

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
