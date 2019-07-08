import datetime
import persistent

class Aluno(persistent.Persistent):
    def __init__(self, name="", birthDate=None, rua="", numero="", bairro="",complemento="", matricula="", additional="", nomePai="", nomeMae="", RG = "", CPF = "", telefone = "", escolas = [], series = []):
        self.name=name    
        self.birthDate=birthDate
        self.rua=rua
        self.numero = numero
        self.bairro = bairro
        self.complemento = complemento
        self.RG=RG
        self.CPF=CPF
        self.telefone=telefone
        self.complemento=complemento
        self.matricula=matricula
        self.nomePai=nomePai
        self.nomeMae=nomeMae
        self.escolas=[]
        self.series=[]

    def escolherEscolaMaisProxima(self):
        print("Escolher escola")
 
class ListaAlunos(persistent.Persistent):
    def __init__(self, item=[]):
        self.alunos=item
    def get(self,i):
        return self.item[i]
 

       