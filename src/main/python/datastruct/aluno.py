import datetime

class aluno():
    def __init__(self, name: str, birthDate=None, address=None, cl=None, additional=""):
        self.name=name    
        self.birthDate=birthDate
        self.address=address
        self.cl=cl
        self.additional=additional

    def addClass(self):
        self.cl+=1
    
    def age(self):
        pass
        