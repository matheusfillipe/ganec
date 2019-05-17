import datetime

class aluno():
    def __init__(self, name: str, birthDate=None, endereco=None, cl=None, matricula="", additional="", nomePai="", nomeMae=""):
        self.name=name    
        self.birthDate=birthDate
        self.endereco=endereco
        self.cl=cl
        self.additional=additional
        self.matricula=matricula
        self.nomePai=nomePai
        self.nomeMae=nomeMae
        self.escolasDestino=[]

    def addClass(self):
        self.cl+=1
    
    def computeCoordenadas():
        pass

    def computeEscola(self):
        pass
    
    def age(self):
        pass
        