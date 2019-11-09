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
    def __init__(self, nome="", endereco="", modalidade= "", lat=0, long = 0, series = "", id = 0):
        self.nomeEscola = nome
        self.endereco = endereco
        self.lat = lat
        self.long = long
        self.series = series
        self.id = id
        self.listaDeDados=[nome, self.endereco, lat, long]
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
        coordenadas = self.latLongEscola()
        self.lat = coordenadas[0]
        self.long = coordenadas[1]
        dicionarioDeDados = self.montarDicionario()
        id=self.DB.salvarDado(dicionarioDeDados)
        return coordenadas, id
    
    def editar(self, id):
        coordenadas = True
        if self.DB.getDadoComId(id)['endereco'] != self.endereco:
            coordenadas = self.latLongEscola()
        if coordenadas != False:
            if coordenadas != True:
                print("endereço mudou")
                self.lat = coordenadas[0]
                self.long = coordenadas[1]
                print(self.lat)
                print(self.long)
            else:
                print("endereço não mudou")
                self.lat = self.DB.getDadoComId(id)['lat']
                self.long = self.DB.getDadoComId(id)['long']
            dicionarioDeDados = self.montarDicionario()
            it=self.DB.update(id, dicionarioDeDados)
            return True, id
        else:
            self.lat = 0
            self.long = 0
            dicionarioDeDados = self.montarDicionario()
            id=self.DB.update(id, dicionarioDeDados)
            return False, id
    
    def salvarCoordenada(self):
        self.DB.update(self.id, {'lat':self.lat, 'long':self.long})
    
    def dados(self, listaIds):
        return  self.DB.getDados(listaIds)


    def latLongEscola(self):
        try:
            coordenadas = GeoCoder().geocode(self.endereco, API_KEY)
            return coordenadas
        except:
            return False

    def montarDicionario(self):
        for i in self.series:
            print(i)
        series = SEPARADOR_SERIES.join(self.series)
        self.listaDeDados=[self.nomeEscola, self.endereco, self.lat, self.long, series]
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
        self.escola=str(escola)
        self.nomeEscola = str(escola)
        self.dbSeries=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
        self.dbEscola=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola']) 
        self.series=self.createDb() 

        if self.series:
            self.serie=[serie for serie in self.series if serie['serie']==nome]
            if len(self.serie)!=0:
                self.serie=self.serie[-1]
            else:
                print("Serie não encontrada:  Escola "+self.escola["nome"]+" ", self.series[0]["serie"])
                self.serie=False      

    def createDb(self):
        self.id=self.dbEscola.acharDadoExato('nome',self.nomeEscola)
        if len(self.id)>0:
            self.escola=self.dbEscola.getDadoComId(self.id[-1])
            return self.dbSeries.getDadosComId(self.dbSeries.acharDadoExato('idDaEscola',self.escola['id']))    
        else:
            print("Falhar ao achar escola")
            return False

    def _update(self, dicte):
        if hasattr(self, 'serie') and self.serie:
            self.dbSeries.update(self.serie["id"], dicte)
        else:
            self.idEscola=self.dbEscola.acharDado('nome', self.nomeEscola)[0]
            d={'vagas': 0,'nDeAlunos': 0}
            d.update(dicte)
            self.dbSeries.salvarDado({
            'idDaEscola': self.idEscola,
            'serie':  self.nome, 
            'vagas':  d['vagas'], 
            'nDeAlunos': d['nDeAlunos']
            })
    
    def _atualizar(self, dict):
        self.idEscola=self.dbEscola.acharDado('nome', self.nomeEscola)[0]
        d={'serie': "", 'vagas': 0,'nDeAlunos': 0}
        d.update(dict)
        self.dbSeries.salvarDado({
        'idDaEscola': self.escola['id'],
        'serie':  d['serie'], 
        'vagas':  d['vagas'], 
        'nDeAlunos': d['nDeAlunos']
        })

    def _increment(self, n=1):
        '''
        serie: nome da série (string)
        escola: nome da escola (string)
        n: número a incrementar, adicionar (int)
        '''
        if self.series:
            if self.series['nDeAlunos']+n>self.series['vagas']:
                return False
            else:
                self.dbSeries.update(self.series['id'], {'nDeAlunos': self.series['nDeAlunos']+n})
                return self.series['vagas']

    def _decrement(self, n=1):
        '''
        serie: nome da série (string)
        escola: nome da escola (string)
        n: número a decrescer, tirar (int)
        '''
        if self.series:
            if self.series['nDeAlunos']-n<0:
                self.dbSeries.update(self.series['id'], {'nDeAlunos': 0})               
            else:
                self.dbSeries.update(self.series['id'], {'nDeAlunos': self.series['nDeAlunos']-n})

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
    def update(cls, serie, escola, dicte):
        t=Turma(serie, escola)
        t._update(dicte)


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
    def __init__(self, item=[Modalidade(nome="", turmas=[])]):                    
        self.modalidades=item
    def append(self,modalidade:Modalidade=Modalidade(nome="", turmas=[])):
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
