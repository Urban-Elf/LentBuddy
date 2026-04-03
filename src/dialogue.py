import curses
import time
import enum

from . import util
from . import localstorage as ls

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
    "Eh, like, don't worry about it. You can just do it tomorrow, or maybe the day after. It's not like it's important or anything.",
    "You know, you could just do something else instead. Like, maybe watch a movie or something. That would be way more fun.",
]


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

NON_INTEGRAL_ANNOYANCE_MESSEGES = [
    "Invalid value. Press a key.",
    "Dude, that's not a number.",
    "I literally just said...",
    "Bro.",
    "Not this again.",
    "Okay, I'm just going to wait until you quit."
]


INTERMISSION_WARNINGS = [
    "=0Hey!= #0# =0Something is going on with the angels and demons!=",
    "=0A battle is happening,= #1 =0and it's affecting the program!=",
    "=0Yo,= #1# =0something went wrong and the program is acting weird!= #0# =0It's a battle!=",
    "=0Wait,= #1# =0something isn't right.= #0# =0It's #1#=1...= #0# =0a battle!="
]

class Gender(enum.Enum):
    MALE = {"pos":"his","obj":"he","sub":"him"}
    FEMALE = {"pos":"her","obj":"she","sub":"her"}

class DialogueState(enum.Enum):
    GOOD = (1, 1)
    BAD = (2, 2)
    NEUTRAL = (0, 3)

    def __init__(self, color_id, id):
        self.color_id = color_id
        self.id = id

class DialogueManager():
    """
    Manages the dialogue state of the app, which can be GOOD, BAD, or NEUTRAL.
    The state changes based on the user's choices and the RNG,
    and affects the dialogue that is shown to the user.

    State can change every now and then via the call `roll_state()`.

    <b id="state_tree">State Tree:</b>

    ```
    __Neutral__
    |         |
    Good      Bad
    |         |
    Neutral   Good
              |
              Neutral
    ```

    Once `state` is `DialogueState.GOOD` or `DialogueState.BAD`, then
    `max_manifest_count` is set to a random value, which controls how many
    times a behavior can be performed on that state. `manifest_count` is
    incremented after each of these to keep track of these.

    When `manifest_count` == `max_manifest_count`, the state progresses
    as indicated in the <b>State Tree</b>.

    State gets serialized and reloaded on app shutdown/startup in the form:
    - `dialogue_state`: `DialogueState`
    - `dialogue_manifest_count`: `int`
    - `dialogue_max_manifest_count`: `int`

    """
    def __init__(self, rng):
        self.rng = rng
        self.gd = Gender.MALE
        self.state = DialogueState.NEUTRAL
        self.manifest_count = 0
        self.max_manifest_count = 0
    
    def set_gender(self, gender: str):
        if gender == "female":
            self.gd = Gender.FEMALE
        else:
            self.gd = Gender.MALE

    def set_state(self, state: DialogueState):
        self.state = state

    def get_state(self):
        if ls.get_instance().get_property("do_dialogue", False):
            return DialogueState.NEUTRAL
        return self.state

    def should_do_temptation(self):
        return self.rng.random() < 0.3
    
    def roll_state(self):
        roll = self.rng.random()
        if roll < 0.3:
            self.state = DialogueState.GOOD
        # Don't want these happening very frequently at all.
        elif roll < 0.1:
            self.state = DialogueState.BAD
        else:
            self.state = DialogueState.NEUTRAL

    # Ending:
    # "Remember, son, God always prevails."
    # "Plus, it's hardcoded. Doesn't change the facts, though."

    def angelic_drop(self, stdscr, x, y):
        """ Gets rid of the bad guys. """
        warning_spec = {"word_delays":[0.1], "char_delays":[0.02, 0.07], "br_delays":[1.1, 0.9]}

        if ls.get_instance().get_property("do_dialogue", False) and self.state == DialogueState.BAD:
            warning = self.rng.choice(INTERMISSION_WARNINGS)
            util.safe_addstr_dialogue(stdscr, y, x, warning, spec=warning_spec)

class DialogueSet():
    def __init__(self, manager: DialogueManager, good: list[str], bad: list[str], neutral: list[str]=[]):
        self.manager = manager
        self.good = good
        self.bad = bad
        self.neutral = neutral

    def get_color(self):
        return curses.color_pair(self.manager.state.color_id)
    
    def get_message(self):
        if self.manager.state == DialogueState.GOOD or (self.manager.state == DialogueState.NEUTRAL and len(self.neutral) < 1):
            return self.manager.rng.choice(self.good)
        elif self.manager.state == DialogueState.BAD:
            return self.manager.rng.choice(self.bad)
        return self.manager.rng.choice(self.neutral)
    
    def get_state(self):
        return self.manager.state

class AnnoyanceManager():
    """
    Manages the annoyance level of certain messages when user chooses invalid options.
        - Starts at 0, and increases by 1 each time the user chooses an invalid option, up to a maximum of len(messages).
        - Stays the same if 3 seconds have passed since the last invalid option.
        - Resets to 0 if 7 seconds have passed since the last invalid option.
    """
    def __init__(self, messages):
        self.messages = messages
        self.annoyance_level = -1
        self.last_bothered = time.time()
    
    def bother(self) -> str:
        elapsed = time.time() - self.last_bothered
        if elapsed < 3:
            self.annoyance_level = self.annoyance_level + 1
        elif elapsed >= 7:
            self.annoyance_level = -1
        self.last_bothered = time.time()
        return self.messages[min(max(0, self.annoyance_level), len(self.messages) - 1)]
    
MANAGER = None

def init(rng):
    global MANAGER
    MANAGER = DialogueManager(rng)
