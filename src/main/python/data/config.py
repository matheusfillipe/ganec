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

    def __eq__(self, value):        
        return self.map==value.map and self.text==value.text and self.text2==value.text2
