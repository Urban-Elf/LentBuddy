import curses

from src import util

def main(stdscr):
    stdscr.keypad(True)

    curses.curs_set(0)
    util.safe_addstr_dialogue(
        stdscr, 0, 0,
        "Hmm, #0# you don't seem like the rest of them. #1# Maybe you're=0...= different?",
        spec={"word_delays":[0.10], "br_delays": [0.8, 2], "char_delays":[0.3]}
    )

    #util.safe_addstr(stdscr, 1, 0, str(util.f_getch(stdscr)))

    while util.f_getch(stdscr) == 10:
        util.shake_effect(stdscr, 2, 0, "A sprite is stopping you from submitting these changes!", intensity=2, delay=0.03, iterations=10)
        util.safe_sleep(stdscr, 0.3)

curses.wrapper(main)