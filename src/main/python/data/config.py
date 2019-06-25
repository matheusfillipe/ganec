import persistent
class Config(persistent.Persistent):
    def __init__(self):
        self.map=0
        self.text="what?"
        self.text2="whatwhat?"
        self.isApplied=False

    def apply(self):
        self.isApplied=True
    def disclaim(self):
        self.isApplied=False
