import json
import os
from pathlib import Path
from . import file_tree

class LocalStorage:
    def __init__(self, file):
        self.path = file
        self.data = {}
    
    def set_property(self, key, value, serialize=True):
        self.data[key] = value
        if serialize:
            self.serialize()

    def get_property(self, key, default=None):
        return self.data.get(key, default)

    def load(self):
        with open(self.path, "r") as f:
            self.data = json.load(f)

    def serialize(self):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f)

__FILE__ = file_tree.ROOT_PATH / "settings.json"
__INSTANCE__ = None

def get_instance():
    global __INSTANCE__
    if __INSTANCE__ is None:
        __INSTANCE__ = LocalStorage(__FILE__)
    return __INSTANCE__
