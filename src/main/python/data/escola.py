import persistent
class escola(persistent.Persistent):
    def __init__(self, nome:str, modalidades=[], endereco=None):
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


class modalidade(persistent.Persistent):
    def __init__(self, nome:str,turmas=[]):
        self.nome=nome
        self.turmas=turmas

class turma(persistent.Persistent):
    def __init__(self, nome:str, vagas=0):
        self.nome=nome
        self.vagas=vagas
        
class ListaEscolas(persistent.Persistent):
    def __init__(self, item):
        self.escolas=item
 