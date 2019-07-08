import persistent
class Config(persistent.Persistent):
    def __init__(self):
        self.map=0
        self.text="what?"
        self.text2="whatwhat?"
        self.isApplied=False
        self.lng, self.lat = -46.30973, -19.00009 

    def apply(self):
        self.isApplied=True
    def disclaim(self):
        self.isApplied=False
    def setInitialPos(self, lat, lng):
        self.lat=lat
        self.lng=lng

    def __eq__(self, value):        
        return self.map==value.map and self.text==value.text and self.text2==value.text2
