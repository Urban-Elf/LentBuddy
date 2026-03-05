import curses
import time
import enum

from . import util
from . import localstorage

ANGELIC = {
    "michael": {
        "name": "St. Michael the Archangel",
        "short_name": "St. Michael",
        "dialogue": {
            "rebukes": [
                ""
            ]
        }
    },
    "raphael": {
        
    }
}

EVIL_MESSAGES = [
    "Hey, you know that penance you have to do today? Yeah, you can just skip it. No one will know.",
    "Eh, like, don't worry about it. You can just do it tomorrow, or maybe the day after. It’s not like it’s important or anything.",
    "You know, you could just do something else instead. Like, maybe watch a movie or something. That would be way more fun.",
]

class DialogueState(enum.Enum):
    GOOD = 1
    BAD = 2
    NEUTRAL = 3

class DialogueManager():
    """
    Manages the dialogue state of the app, which can be good, bad, or neutral.
    The state changes based on the user's choices and the RNG,
    and affects the dialogue that is shown to the user.

    State can change every now and then via the call 
    """
    def __init__(self, rng):
        self.rng = rng
        self.state = DialogueState.NEUTRAL
    
    def set_state(self, state: DialogueState):
        self.state = state

    def should_do_temptation(self):
        return self.rng.random() < 0.3
    
    def roll_state(self):
        roll = self.rng.random()
        if roll < 0.3:
            self.state = DialogueState.GOOD
        elif roll < 0.1:
            self.state = DialogueState.BAD
        else:
            self.state = DialogueState.NEUTRAL

class DialogueSet():
    def __init__(self, manager: DialogueManager, good: list[str], bad: list[str], neutral: list[str]=[]):
        self.manager = manager
        self.good = good
        self.bad = bad
        self.neutral = neutral

    def get_color(self):
        if self.manager.state == DialogueState.GOOD:
            return curses.color_pair(1)
        elif self.manager.state == DialogueState.BAD:
            return curses.color_pair(2)
        return curses.color_pair(0)
    
    def get_dialogue(self):
        if self.manager.state == DialogueState.GOOD or (self.manager.state == DialogueState.NEUTRAL and len(self.neutral) < 1):
            return self.manager.rng.choice(self.good)
        elif self.manager.state == DialogueState.BAD:
            return self.manager.rng.choice(self.bad)
        return self.manager.rng.choice(self.neutral)
    
    def get_state(self):
        return self.manager.state

class AnnoyanceManager():
    """
    Manages the annoyance level of the app when user chooses invalid options.
        - Starts at 0, and increases by 1 each time the user chooses an invalid option, up to a maximum of len(messages).
        - Stays the same if 3 seconds have passed since the last invalid option.
        - Resets to 0 if 10 seconds have passed since the last invalid option.
    """
    def __init__(self, messages):
        self.messages = messages
        self.annoyance_level = -1
        self.last_bothered = time.time()
    
    def bother(self) -> str:
        elapsed = time.time() - self.last_bothered
        if elapsed < 3:
            self.annoyance_level = self.annoyance_level + 1
        elif elapsed >= 10:
            self.annoyance_level = -1
        self.last_bothered = time.time()
        return self.messages[min(max(0, self.annoyance_level), len(self.messages) - 1)]
    
MANAGER = None

def init(rng):
    global MANAGER
    MANAGER = DialogueManager(rng)

INTERMISSION_WARNINGS = [
    "Hey! Something is going on with the angels and demons!",
    "A spiritual battle is happening, and it's affecting the program!",
    "Yo, something went wrong and the program is acting weird! It's a battle!",
    "Wait, something isn't right. It's... a battle!"
]

# Ending:
# "Remember, son, God always prevails."
# "Plus, it's hardcoded. Doesn't change the facts, though."

def angelic_drop(stdscr, x, y, manager: DialogueManager, initial_message):
    if localstorage.get_instance().get_property("do_intermissions", True):
        warning = manager.rng.choice(INTERMISSION_WARNINGS).split(" ")
        x = 0
        for i in range(len(warning)):
            util.safe_addstr(stdscr, y, x, warning[i] + " ", manager.get_color())
            x += len(warning[i]) + 1
            time.sleep(0.05)


