class escola():
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


class modalidade():
    def __init__(self, nome,turmas=[]):
        self.nome=nome
        self.turmas=turmas

class turma():
    def __init__(self, nome, vagas=-1):
        self.nome=nome
        self.vagas=vagas
        
