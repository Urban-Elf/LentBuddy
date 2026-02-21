import json

class LocalStorage:
    def __init__(self, file):
        self.file = file
        self.data = {}
    
    def set_property(self, key, value):
        self.data[key] = value

    def get_property(self, key, default=None):
        return self.data.get(key, default)

    def load(self):
        try:
            with open(self.file, "r") as f:
                self.data = json.load(f)
        except:
            self.data = {}

    def serialize(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file, "w") as f:
            json.dump(self.data, f)


__FILE__ = "storage/settings.json"
__INSTANCE__ = None

def get_instance():
    global __INSTANCE__
    if __INSTANCE__ is None:
        __INSTANCE__ = LocalStorage(__FILE__)
    return __INSTANCE__
