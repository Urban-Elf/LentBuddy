import curses
from src import util, vscreen as virtscreen

def main(stdscr):
    # Hide cursor
    curses.curs_set(0)

    vscreen = virtscreen.VirtualScreen(stdscr)

    # Example messages
    messages = [
        "Hello world! This is a minimal virtual screen demo.",
        "Each message is displayed fully in buffer, truncated on view.",
        "Resize your terminal and you can see previously truncated text.",
        "Lines exceeding the screen height will scroll automatically.",
        "Timing simulation works with optional delays.",
    ]

    # Add messages with a small delay
    for msg in messages:
        vscreen.addstr(len(vscreen.buffer), 0, msg)
        util.safe_sleep(stdscr, 0.5)

    # Example: using safe_addstr_dialogue to print timed text
    util.safe_addstr_dialogue(
        vscreen, len(vscreen.buffer), 0,
        "Hello world! #1This is fast# normal text =0slowly=.", 
        spec={"word_delays":[1, 0.5], "char_delays":[0.05], "br_delays":[0.7]}
    )

    vscreen.addstr(len(vscreen.buffer), 1, "Press any key to exit...")

    # Wait for Enter key
    while stdscr.getch() != 10:
        pass


if __name__ == "__main__":
    curses.wrapper(main)