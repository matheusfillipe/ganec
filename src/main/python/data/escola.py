import sqlite3

import datetime

from datetime import date
import persistent
from lib.constants import *
from lib.hidden.constants import API_KEY
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt
from sqlitedb import *

from lib.osm import MapWidget
from lib.gmaps import *
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
        enderecoo = rua + numero + bairro + cidade
        self.listaDeDados=[nome, enderecoo, lat, long]
        self.DB = DB(CAMINHO['escola'], TABLE_NAME['escola'], ATRIBUTOS['escola'])

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
    def removeByIndex(self,i):
        del self.modalidades[i]
        
class ListaEscolas(persistent.Persistent):
    def __init__(self, item=[]):
        self.escolas=item
    def get(self,i):
        return self.escolas[i]
