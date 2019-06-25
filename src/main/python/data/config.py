import persistent
class Config(persistent.Persistent):
    def __init__(self):
        self.map=0
        self.text="what?"
    def setmap(self,map):
        self.map=map
