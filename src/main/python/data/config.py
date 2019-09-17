import persistent
from sqlitedb import DB
from customWidgets import *
from pathlib import Path

class Config(persistent.Persistent):
    def __init__(self):
        self.map=0
        self.isApplied=False
        self.lng, self.lat = -46.30973, -19.00009 
        self.osmPath=''
        self.text=''
        self.text2=''

    def apply(self):
        self.isApplied=True
    def disclaim(self):
        self.isApplied=False
    def setInitialPos(self, lat, lng):
        self.lat=lat
        self.lng=lng
        
    @classmethod 
    def cidade(cls):
        db=DB(str(confPath()/Path('settings.db')),"strings", ['nome', 'string'])
        return db.getDado(db.acharDado('nome','cidade')[-1])['string']

    def __eq__(self, value):        
        return self.map==value.map and self.text==value.text and self.text2==value.text2
