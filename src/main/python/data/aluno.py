import datetime

from datetime import date
import persistent
from lib.constants import *
from lib.hidden.constants import API_KEY
from PyQt5 import QtCore
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt
from sqlitedb import *
import os

from data.config import Config
from lib.database import VariableManager
from lib.osm import MapWidget
from lib.gmaps import *
from pathlib import Path
import customWidgets

from data.config import *
#cidade=Config.cidade()

def nogui(func):
    from functools import wraps
    @wraps(func)
    def async_func(*args, **kwargs):
        runner = Runner(func, *args, **kwargs)
        # Keep the runner somewhere or it will be destroyed
        func.__runner = runner
        runner.start()

    return async_func
 
class Aluno(persistent.Persistent):
    def __init__(self, name="", matricula="", dataDeNascimento="", RG = "", CPF = "", nomeMae="", nomePai="", telefone = "", endereco = "", serie = "", escola = "", idade = 0, lat=0, long = 0, id = 0):
        self.nome=name 
        self.matricula=matricula   
        self.dataDeNascimento=dataDeNascimento
        self.RG=RG
        self.CPF=CPF
        self.nomeMae=nomeMae
        self.nomePai=nomePai
        self.telefone=telefone
        self.endereco=endereco
        self.serie=serie
        self.escola=escola
        self.idade = self.calcularIdade(dataDeNascimento)
        self.lat=lat
        self.long=long
        self.id = id
        self.listaDeDados=[name, matricula, dataDeNascimento, RG, CPF, nomeMae, nomePai, telefone, endereco, serie, escola, self.idade, lat, long]
        self.DB = DB(str(customWidgets.confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        self.DBSeries=DB(str(customWidgets.confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
        self.DBSettings=DB(str(customWidgets.confPath()/Path('settings.db')),"strings", ['nome', 'string'])
    
    def salvar(self):
        coordenadas = self.latLongAluno()
        if not coordenadas:
            if not hasattr(self,"center"):
                self.varManager=VariableManager(os.path.dirname(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)))
                self.config=self.varManager.read(Config(),DB_CONFIG)  
                self.center=[self.config.get().lat, self.config.get().lng]     
            coordenadas = self.center
        self.lat = coordenadas[0]
        self.long = coordenadas[1]
        dicionarioDeDados = self.montarDicionario()
        self.id=self.DB.salvarDado(dicionarioDeDados)
        return coordenadas, self.id

    def salvarCoordenada(self):
        self.DB.update(self.id, {'lat':self.lat, 'long':self.long})
    
    def editar(self, id):
        coordenadas = True
        if self.DB.getDadoComId(id)['endereco'] != self.endereco:
            print("endereço mudou")
            coordenadas = self.latLongAluno()
        else:
            print("endereço nao mudou")
        if coordenadas != False:
            if coordenadas != True:
                self.lat = coordenadas[0]
                self.long = coordenadas[1]
            else:
                self.lat = self.DB.getDadoComId(id)['lat']
                self.long = self.DB.getDadoComId(id)['long']
            dicionarioDeDados = self.montarDicionario()
            print(dicionarioDeDados['escola'])
            self.DB.update(id, dicionarioDeDados)
            return True
        else:
            self.lat = 0
            self.long = 0
            self.escola = 0
            dicionarioDeDados = self.montarDicionario()
            self.DB.update(id, dicionarioDeDados)
            return False

    def subirSerie(self):
        pass

    def descerSerie(self):
        pass
    
    def dados(self, listaIds):
        return  self.DB.getDados(listaIds)

    def calcularIdade(self, nascido):
        nascimento_ = nascido
        nascimento = nascimento_.split(' ')
        data_atual = date.today()
        dataAtual = {'dia':data_atual.day, 'mes':data_atual.month, 'ano':data_atual.year}
        if len(nascimento) > 3:
            try:
                mes=int(nascimento[1])
                idadeAluno = {'dia':int(nascimento[2]), 'mes':mes, 'ano':int(nascimento[3])}
            except:
                idadeAluno = {'dia':int(nascimento[2]), 'mes':dataEmNumero[nascimento[1]], 'ano':int(nascimento[3])}

            dataAtualDias = dataAtual['dia'] + dataAtual['mes']*30 + dataAtual['ano']*365
            nascimentoDias = idadeAluno['dia'] + idadeAluno['mes']*30 + idadeAluno['ano']*365
            idade = round((dataAtualDias - nascimentoDias)/365)
        else:
            nascimento = nascimento[0].split("/")
            if len(nascimento) >= 2:
                try:
                    mes=int(nascimento[1])
                    idadeAluno = {'dia':int(nascimento[0]), 'mes':mes, 'ano':int(nascimento[2])}
                except:
                    idadeAluno = {'dia':int(nascimento[0]), 'mes':dataEmNumero[nascimento[1]], 'ano':int(nascimento[2])}
                dataAtualDias = dataAtual['dia'] + dataAtual['mes']*30 + dataAtual['ano']*365
                nascimentoDias = idadeAluno['dia'] + idadeAluno['mes']*30 + idadeAluno['ano']*365
                idade = round((dataAtualDias - nascimentoDias)/365)
            else:
                idade = 0
        return idade

    def latLongAluno(self):
        try:
            coordenadas = GeoCoder().geocode(self.endereco, API_KEY)
            return coordenadas
        except:
            return False
            
    @classmethod 
    def getLatLong(cls, endereco):
        try:
            DBSettings=DB(str(customWidgets.confPath()/Path('settings.db')),"strings", ['nome', 'string'])
            coordenadas = GeoCoder().geocode(endereco+" - "+DBSettings.getDado(DBSettings.acharDado('nome','cidade')[0])['string'], API_KEY)
            return coordenadas
        except:
            return False

       

    def montarDicionario(self):
        self.listaDeDados=[self.nome, self.matricula, self.dataDeNascimento, self.RG, self.CPF, self.nomeMae, self.nomePai, self.telefone, self.endereco, self.serie, self.escola, self.idade, self.lat, self.long]
        dicionario = {}
        j=0
        for i in ATRIBUTOS['aluno']:
            dicionario[i] = self.listaDeDados[j]
            j+=1
        return dicionario

    def buscar(self, busca):
        resultado = []
        return resultado










    


 

       