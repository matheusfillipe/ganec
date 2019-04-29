import persistent

class listaEscolas(persistent.Persistent):
    def __init__(self, escolas):
        self.escolas=escolas
 
class listaAlunos(persistent.Persistent):
    def __init__(self, escolas):
        self.escolas=escolas
        