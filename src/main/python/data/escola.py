import persistent
class Escola(persistent.Persistent):
    def __init__(self, nome:str="", modalidades=[], endereco=None):
        self.nome=nome
        self.modalidades=modalidades
        self.endereco=endereco
        self.alunos=[]            

    def computeCoordenadas(self):
        pass

    def addAluno(self, aluno):
        self.alunos.append(aluno)

    def canContinue(self, aluno):
        if aluno in self.alunos:
            pass
        else:
            return False
class Turma(persistent.Persistent):
    def __init__(self, nome:str="", vagas=0):
        self.nome=nome
        self.vagas=vagas

class Modalidade(persistent.Persistent):
    def __init__(self, nome:str="",turmas=[]):
        self.nome=nome
        self.turmas=turmas        
    def getTurma(self,turmaName:str):
        for turma in self.turmas:
            if turma.nome==turmaName:
                return turma
        return None
    def addTurma(self, turma:Turma):
        self.turmas.append(turma)

class ListaModalidades(persistent.Persistent):
    def __init__(self, item=[Modalidade(nome="", turmas=[Turma(nome="")])]):                    
        self.modalidades=item
    def append(self,modalidade:Modalidade=Modalidade(nome="", turmas=[Turma(nome="")])):
        self.modalidades.append(modalidade)
    def get(self,i):
        return self.modalidades[i]
    def removebyIndex(self,i):
        del self.modalidades[i]
        
class ListaEscolas(persistent.Persistent):
    def __init__(self, item):
        self.escolas=item
    def get(self,i):
        return self.escolas[i]
