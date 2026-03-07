import curses

class VirtualScreen:
    """Minimal virtual screen wrapper with line buffer and optional top/bottom margins."""

    def __init__(self, stdscr, max_lines=None, top_margin=0, bottom_margin=0):
        self.stdscr = stdscr
        self.buffer = []  # list of (full_line, attr)
        self.max_lines = max_lines or curses.LINES
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.width = curses.COLS
        self.height = curses.LINES

    def addstr(self, y, x, text, attr=0):
        """Add text to buffer at specified line index, expanding buffer if needed."""
        while len(self.buffer) <= y:
            self.buffer.append(("", 0))
        full_line, _ = self.buffer[y]
        new_line = full_line[:x] + text
        if x + len(text) < len(full_line):
            new_line += full_line[x + len(text):]
        self.buffer[y] = (new_line, attr)
        self.render()

    def addstr_append(self, text, attr=0):
        """Append text to the end of the buffer."""
        self.addstr(len(self.buffer), 0, text, attr)

    def render(self):
        """Render buffer within the defined view boundaries, respecting margins."""
        self.height, self.width = self.stdscr.getmaxyx()
        view_height = self.height - self.top_margin - self.bottom_margin

        # Only clear the view area (not top/bottom margins)
        for y in range(self.top_margin, self.height - self.bottom_margin):
            try:
                self.stdscr.move(y, 0)
                self.stdscr.clrtoeol()
            except curses.error:
                pass

        # Determine which lines to render in the view
        start_line = max(0, len(self.buffer) - view_height)
        for idx, (line, attr) in enumerate(self.buffer[start_line:]):
            screen_y = self.top_margin + idx
            if screen_y >= self.height - self.bottom_margin:
                break  # stay inside view
            try:
                self.stdscr.addstr(screen_y, 0, line[:self.width], attr)
            except curses.error:
                pass

        self.refresh()

    def refresh(self):
        self.stdscr.refresh()

    def nodelay(self, nodelay: bool):
        self.stdscr.nodelay(nodelay)

    def getch(self):
        return self.stdscr.getch()



import curses

def main(stdscr):
    curses.curs_set(0)

    # Initialize virtual screen with 2-line top margin, 2-line bottom margin
    vscreen = VirtualScreen(stdscr, top_margin=2, bottom_margin=2)

    # Draw static header/footer outside the VirtualScreen
    height, width = stdscr.getmaxyx()
    try:
        stdscr.addstr(0, 0, "------ HEADER ------".ljust(width))
        stdscr.addstr(1, 0, "".ljust(width))  # optional spacer
        stdscr.addstr(height - 2, 0, "".ljust(width))  # optional spacer
        stdscr.addstr(height - 1, 0, "------ FOOTER ------".ljust(width))
    except curses.error:
        pass
    stdscr.refresh()

    # Add messages to the virtual chat
    messages = [
        "Hello! This is the chat area.",
        "Messages appear below the header.",
        "Old messages scroll up automatically.",
        "Lines exceeding the view height stay within the margins.",
        "You can resize the terminal safely!"
    ]

    for msg in messages:
        vscreen.addstr_append(msg)
        curses.napms(200)  # small delay to simulate timing

    vscreen.addstr_append("Press Enter to exit...")

    # Wait for Enter key
    while vscreen.getch() != 10:
        pass

if __name__ == "__main__":
    curses.wrapper(main)