import curses

from src import util

"""
Implement this function:

safe_addstr_dialogue(stdscr, x, y, text, spec={"word_delays":[0.05, 0.02], "char_delays": ["0.015"]}):

- Slowly print out each word/letter of the var 'text' depending on next rule
- Default mode is printing one word per iteration and delaying spec["word_delays"][0] as a default  
   - However, inside the text, one can use the token #i TEXT # to have TEXT printed at spec["word_delays"][i].  Similarly, =i TEXT = for letter by letter printing.

Does that make sense?
"""

def main(stdscr):
    curses.curs_set(0)
    util.safe_addstr_dialogue(
        stdscr, 0, 0,
        "Hello world! #0 This is fast # normal text =0 slowly=.",
        spec={"word_delays":[0.2, 0.05], "char_delays":[0.05]}
    )
    stdscr.getch()

curses.wrapper(main)