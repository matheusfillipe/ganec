from collections import OrderedDict
import datetime
from datetime import date
import persistent
from lib.constants import *
from lib.hidden.constants import API_KEY
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt
from sqlitedb import *

from lib.osm import MapWidget
from lib.gmaps import *
from customWidgets import *

#
class Escola(persistent.Persistent):
    def __init__(self, nome="", rua="", numero="", bairro= "", modalidade= "", lat=0, long = 0, id = 0):
        self.nomeEscola = nome
        self.ruaEscola = rua
        self.numeroEscola = numero
        self.nomeBairro = bairro
        self.lat = lat
        self.long = long
        self.id = id
        enderecoo = rua + numero + bairro 
        self.listaDeDados=[nome, enderecoo, lat, long]
        self.DB = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        self.DBSerie=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
        
    @classmethod  
    def todasAsSeries(cls):
        db = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])       
        return list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in db.todosOsDados()], [])))      
    
    @classmethod  
    def todasAsEscolas(cls):
        db = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])       
        return [escola['nome'] for escola in db.todosOsDados()] 

    def salvar(self):
        coordenadas = self.latLongAluno()
        self.lat = coordenadas[0]
        self.long = coordenadas[1]
        self.escola = self.definirEscola()
        dicionarioDeDados = self.montarDicionario()
        self.DB.salvarDado(dicionarioDeDados)
        return coordenadas
    
    def editar(self, id):
        coordenadas = self.latLongAluno()
        if coordenadas != False:
            self.lat = coordenadas[0]
            self.long = coordenadas[1]
            self.escola = self.definirEscola()
            dicionarioDeDados = self.montarDicionario()
            self.DB.update(id, dicionarioDeDados)
            return True
        else:
            self.lat = 0
            self.long = 0
            self.escola = 0
            dicionarioDeDados = self.montarDicionario()
            self.DB.update(id, dicionarioDeDados)
            return False
    
    def dados(self, listaIds):
        return  self.DB.getDados(listaIds)


    def latLongEscola(self):
        try:
            coordenadas = GeoCoder().geocode(self.endereco, API_KEY)
            return coordenadas
        except:
            return False

    def montarDicionario(self):
        enderecoEscola = self.nomeEscola.text() + self.ruaEscola.text() + self.numeroEscola.text() + self.nomeBairro.text()
        self.listaDeDados=[self.nomeEscola, self.enderecoEscola, self.lat, self.long]
        dicionario = {}
        j=0
        for i in ATRIBUTOS['escola']:
            dicionario[i] = self.listaDeDados[j]
            j+=1
        return dicionario

    def buscar(self, busca):
        resultado = []
        return resultado


class Turma(persistent.Persistent):
    def __init__(self, nome:str="", escola=""):
        self.nome=nome
        self.vagas=0
        self.alunos=0
        self.escola=escola
        self.series=self.createDb()
        if self.series:
            self.serie=[serie for serie in self.series if serie['serie']==nome]
            if len(self.serie)!=0:
                self.serie=self.serie[-1]
            else:
                print("Serie não encontrada:  Escola"+self.escola+" ", self.series)
                self.serie=False        

    def createDb(self):
        self.dbSeries=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
        self.dbEscola = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])  
        id=self.dbEscola.acharDadoExato('nome',self.escola)
        if len(id)>0:
            self.escola=self.dbEscola.getDadoComId(id[-1])
            return self.dbSeries.getDadosComId(self.dbSeries.acharDadoExato('idDaEscola',self.escola['id']))    
        else:
            print("Falhar ao achar escola")
            return False

    def _update(self, dict):
        if hasattr(self, 'serie'):
            self.dbSeries.update(self.serie["id"], dict)
        else:
            d={'vagas': 0,'nDeAlunos': 0}
            d.update(dict)
            self.dbSeries.salvarDado({
             'idDaEscola': self.escola['id'],
			  'serie':  self.nome, 
			  'vagas':  d['vagas'], 
			  'nDeAlunos': d['nDeAlunos']
            })

    def _increment(self, n=1):
        '''
        serie: nome da série (string)
        escola: nome da escola (string)
        n: número a incrementar, adicionar (int)
        '''
        if self.serie:
            if self.serie['nDeAlunos']+n>self.serie['vagas']:
                return False
            else:
                self.dbSeries.update(self.serie['id'], {'nDeAlunos': self.serie['nDeAlunos']+n})
                return self.serie['vagas']

    def _decrement(self, n=1):
        '''
        serie: nome da série (string)
        escola: nome da escola (string)
        n: número a decrescer, tirar (int)
        '''
        if self.serie:
            if self.serie['nDeAlunos']-n<0:
                self.dbSeries.update(self.serie['id'], {'nDeAlunos': 0})               
            else:
                self.dbSeries.update(self.serie['id'], {'nDeAlunos': self.serie['nDeAlunos']-n})

    @classmethod
    def increment(cls, serie, escola, n=1):
        '''
        serie: nome da série (string)
        escola: nome da escola (string)
        n: número a incrementar, adicionar (int)
        '''
        t=Turma(serie, escola)
        t._increment(n)        

    @classmethod
    def decrement(cls, serie, escola, n=1):
        '''
        serie: nome da série (string)
        escola: nome da escola (string)
        n: número a decrescer, tirar (int)
        '''
        t=Turma(serie, escola)
        t._decrement(n)

    @classmethod
    def update(cls, serie, escola, dict):
        t=Turma(serie, escola)
        t._update(dict)


    @classmethod
    def instance(cls, serie, escola):
        return Turma(serie, escola)


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
    def removeByIndex(self,i):
        del self.modalidades[i]
        
class ListaEscolas(persistent.Persistent):
    def __init__(self, item=[]):
        self.escolas=item
    def get(self,i):
        return self.escolas[i]
