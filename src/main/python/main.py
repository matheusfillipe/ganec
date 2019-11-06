# -*- coding: utf-8 -*-

"""

/**********************************************************************************
GANEC = Gestor de Alunos Nas Escolas do Carmo 
    
        
        begin                : 2019-15-097
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Felipe, Lucas e Matheus
        email                : matheusfillipeag@gmail.com
**********************************************************************************/

/**********************************************************************************
*  LICENSE: "Zero Clause BSD"
*
* Copyright (C) 2019 by Matheus Fillipe <matheusfillipeag@gmail.com>
* Permission to use, copy, modify, and/or distribute this software for any 
* purpose with or without fee is hereby granted.
* 
* THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH 
* REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND 
* FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, 
* OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE6,
* DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS 
* ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE. 
*                                                                         
****************************************************************************************/

! Many important values can be changed at src/main/python/lib/constants.py !

"""

import PyQt5
from PyQt5 import QtWidgets, QtGui, uic, Qt, QtCore
from fbs_runtime.application_context import ApplicationContext
import os, sys, traceback
from copy import deepcopy
import zipfile
import shutil
from PyQt5.QtCore import pyqtSignal

from data.config import *
from lib.osm import MapWidget
from lib.gmaps import QGoogleMap 
from lib.database import VariableManager, QInterface
from lib.constants import *
from threads import *
from customWidgets import *
from escolasWidgets import *
from alunosWidgets import *
from customWidgets import *

try: 
    I=0
    MAIN_WINDOW, _ = uic.loadUiType(BASEPATHS[I]+"ui/mainWindow.ui")
    SETTINGS_DIALOG,_ = uic.loadUiType(BASEPATHS[I]+"ui/dialogs/settingsDialog.ui")
except:
    I=1
    MAIN_WINDOW, _ = uic.loadUiType(BASEPATHS[I]+"ui/mainWindow.ui")
    SETTINGS_DIALOG,_ = uic.loadUiType(BASEPATHS[I]+"ui/dialogs/settingsDialog.ui")
   

RESET=0   

class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    def __init__(self,iface):
        QtWidgets.QWidget.__init__(self)
        SETTINGS_DIALOG.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)

        self.comboBox : QtWidgets.QComboBox 
        self.lineEdit : QtWidgets.QLineEdit
        self.lineEdit_2 : QtWidgets.QLineEdit
        self.buttonBox : QtWidgets.QDialogButtonBox
        self.setOsmBtn : QtWidgets.QPushButton
        self.backupBtn : QtWidgets.QPushButton
        self.restaurarBtn : QtWidgets.QPushButton
        self.lineEdit_2 : QtWidgets.QLineEdit

        self.backupBtn.clicked.connect(self.backup)
        self.restaurarBtn.clicked.connect(self.importar)
        
        self.comboBox.addItem("Google")    
        self.comboBox.addItem("OSM")
        self.comboBox.addItem("Here")
        self.comboBox.addItem("Arquivo")

        iface.config.setup(self,
        signals=[self.buttonBox.accepted, self.comboBox.currentIndexChanged, self.aplicarBtn.clicked, self.cleanDbButton.clicked],
        slots=[iface.saveConfig,                lambda: 0,                         iface.saveConfig,           self.reset],
        properties=["map"],
        readers=[self.comboBox.currentIndex],
        writers=[self.comboBox.setCurrentIndex])    

        self.setOsmBtn.clicked.connect(self.setOsm)
        db=DB(str(confPath()/Path('settings.db')),"strings", ['nome', 'string'])
        self.db=db

        try:
            self.lineEdit.setText(db.getDado(db.acharDado('nome','osmPath')[-1])['string'])
        except:
            self.db.salvarDado({'nome': 'osmPath', 'string': ''})
            self.lineEdit.setText("")

        try:
            self.lineEdit_2.setText(db.getDado(db.acharDado('nome','cidade')[-1])['string'])
        except:
            self.db.salvarDado({'nome': 'cidade', 'string': ''})
            self.lineEdit_2.setText("")

    def setOsm(self):
        db=self.db
        filename = QtWidgets.QFileDialog.getOpenFileName(filter="Arquivo de mapa (*.osm)")[0]
        if filename in ['', None]: return
        self.db.update(db.acharDado('nome','osmPath')[0], {'string': filename})    
        self.lineEdit.setText(db.getDado(db.acharDado('nome','osmPath')[-1])['string'])

    def backup(self):
        db=self.db
        filename : str
        filename = QtWidgets.QFileDialog.getSaveFileName(filter="Arquivo de backup (*.zip *.ZIP)")[0]
        if filename in ['', None]: return
        filename= filename if filename.endswith(".zip") else filename+".zip"
        zip_file = zipfile.ZipFile(filename, 'w')
        for path in confPath().rglob('*'):
            path: Path
            zip_file.write(str(path), str(Path(NAME)/path.relative_to(confPath())), zipfile.ZIP_DEFLATED)
        zip_file.close()

    def importar(self):
        db=self.db
        filename = QtWidgets.QFileDialog.getOpenFileName(filter="Arquivo de backup (*.zip)")[0]
        if filename in ['', None]: return
        if yesNoDialog(title="Atenção!", message='Isso irá juntar seus dados atuais com os do backup. Tem certeza disso?'):
            z = zipfile.ZipFile(filename, "r")
            tmp=tmpPath() 
            z.extractall(str(tmp))
            print("Extracting to: ", str(tmp))                        
            z.close()

            #Juntar dois bancos de dados
            dbA= DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
            dbE=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
            dbS=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
 
            dbAR= DB(str(tmpPath() / Path(NAME)/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
            dbER=DB(str(tmpPath() / Path(NAME)/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
            dbSR=DB(str(tmpPath() / Path(NAME)/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
            dbSettings=DB(str(tmpPath()/Path('settings.db')),"strings", ['nome', 'string'])

            dbA.salvarDados(dbAR.todosOsDados())
            dbE.salvarDados(dbER.todosOsDados())
            dbS.salvarDados(dbSR.todosOsDados())
            self.db.salvarDados(dbSettings.todosOsDados())

            os.rmdir(str(tmpPath()))


    def restore(self):
        reply = yesNoDialog(iface=self, message="Tem certeza que deseja remover todos os dados cadastrados?", 
        info="Esta operação irá remover todos os arquivos de configuração e de banco de dados. Isso não é reversível.")     
        if reply:
            filename = QtWidgets.QFileDialog.getOpenFileName(filter="Arquivo de backup (*.zip)")[0]
            if not filename: return
            try:
                self.iface.varManager.removeDatabase()
            except:
                pass
            try:
                os.rmdir(str(confPath()))
            except:
                pass

            z = zipfile.ZipFile(filename, "r") 
            z.extractall(QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.ConfigLocation)[0])
            messageDialog(self, message="O programa irá reiniciar")
            self.close()
            self.iface.restartProgram()                

                 

        
    def reset(self):        
        reply = yesNoDialog(iface=self, message="Tem certeza que deseja remover todos os dados cadastrados?", 
        info="Esta operação irá remover todos os arquivos de configuração e de banco de dados. Isso não é reversível.")
        if reply:
            try:
                self.iface.varManager.removeDatabase()
            except:
                pass
            #try:
            shutil.rmtree(str(confPath()), ignore_errors=True)
            #except:
            #   pass
            messageDialog(self, message="O programa irá reiniciar")
            self.close()
            self.iface.restartProgram()                


class MainWindow(QtWidgets.QMainWindow, MAIN_WINDOW):

    def __init__(self, app):         
        QtWidgets.QMainWindow.__init__(self)
        MAIN_WINDOW.__init__(self)
        self.app : QtWidgets.QApplication
        self.app=app 
        self.varManager=VariableManager(os.path.dirname(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)))
        self.listaBusca=[]
        if RESET:
            #self.varManager.removeDatabase()
            self.close()

        self.dbAluno = DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        self.dbEscola = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])  
        self.dbSeries =  DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
        self.dbAno = DB(str(confPath()/Path(CAMINHO['ano'])), TABLE_NAME['ano'], ATRIBUTOS['ano'])
        
        self.atualizarAno()

        self.setupUi(self)
        self.actionSair.triggered.connect(self.close)
        self.actionModalidades.triggered.connect(self.modalidadesDialog)
        self.actionAlunos.triggered.connect(self.newAlunoDialog)    
        self.actionConfigura_es.triggered.connect(self.settingDialog)               
        self.actionEscolas.triggered.connect(self.newEscolaDialog)
        self.config=self.varManager.read(Config(),DB_CONFIG)  
        self.config.modified.connect(lambda: self.config.customSlot("disclaim"))   
        self.config.notModified.connect(lambda: self.config.customSlot("apply"))
        self.pushButtonBusca.clicked.connect(self.buscarAluno)
        self.actionExportarBusca.triggered.connect(self.exportarBusca)
        self.listViewBusca.itemClicked.connect(self.setarEndereco)
        self.idEscola = 0

        self.latLongAns = ["a"]
        self.spinBoxIdadeMaxima.setValue(50)
        self.spinBoxIdadeMinima.setValue(0)
        self.comboBoxBusca.addItems(ATRIBUTOS['aluno'][:-2])        
        self.lineEditAluno.textChanged.connect(self.buscarAluno)
        self.scrollAreaTeste : QtWidgets.QScrollArea
        self.addMap()
        self.dialog=[]
        self.actionAlunos_3.triggered.connect(self.imporAlunoCsv)
        self.actionEscolar.triggered.connect(self.imporEscolaCsv)
        self.actionCalcular_Rotas_2.triggered.connect(self.calcularRotas)
        self.actionRecalcular_endere_os_de_alunos.triggered.connect(self.recalcularAlunos)
        self.actionRecalcular_endere_os_de_escolas.triggered.connect(self.recalcularEscolas)
        self.actionExportar_imagem.triggered.connect(self.exportImg)
        self.actionAvan_ar_todos_os_alunos_em_um_ano.triggered.connect(lambda: pular(1))
        self.actionRetornar_todos_os_alunoes_um_ano.triggered.connect(lambda: pular(-1))
        self.actionRemover_Escola.triggered.connect(self.SremoverEscola)
        self.actionAvan_ar_uma_turma.triggered.connect(self.SacanvaTurma)
        self.actionRetornar_uma_turma.triggered.connect(self.SretornaTurma)
        self.actionRemover.triggered.connect(self.SremoverAlunos)

        self.progressBar.hide() 

        self.escolaDropDownLayout : QtWidgets.QHBoxLayout
        self.serieDropDownLayout : QtWidgets.QHBoxLayout

        self.dropDownEscolas=dropDown([], self, "Escolas")    
        self.escolaDropDownLayout.addWidget(self.dropDownEscolas)    
        self.dropDownSeries=dropDown([], self, "Turmas")
        self.serieDropDownLayout.addWidget(self.dropDownSeries)

        from collections import OrderedDict
        self.dropDownEscolas.selected.connect(lambda indices:
         self.dropDownSeries.repopulate(list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) 
         for i,escola in enumerate(self.dbEscola.todosOsDados()) if i in indices],[])))))

        self.update()


        self.addMarkerEscolas()


    def SremoverEscola(self):
        for aluno in self.listaBusca:
            if aluno['escola']:
                self.dbAluno.update(aluno['id'], {"escola": ""})
            
    def SacanvaTurma(self):
        for aluno in self.listaBusca:
            if aluno['escola']:
                from collections import OrderedDict
                escola=self.dbEscola.getDadoComId(aluno['escola'])
                series=list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in self.dbEscola.todosOsDados()],[])))
                serieId=[id for id in self.dbSeries.acharDadoExato("idDaEscola", aluno['escola']) if id in self.dbSeries.acharDadoExato("serie", aluno['serie'])][-1]
                serie=self.dbSeries.getDadoComId(serieId)
                self.dbSeries.update(serieId, {"nDeAlunos": serie["nDeAlunos"]-1})  #Achei a serie e remove a vaga
                if aluno["serie"]=="FORMADO":
                    nextSerieName=series[-1]
                else:
                    n=series.index(serie)+1
                    nextSerieName = "FORMADO" if n > len(series)-1 else series[n] #proxima serie
                self.dbAluno.update(aluno['id'], {"serie": nextSerieName})
              

    def SretornaTurma(self):
        for aluno in self.listaBusca:
            if aluno['escola']:
                from collections import OrderedDict
                escola=self.dbEscola.getDadoComId(aluno['escola'])
                series=list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in self.dbEscola.todosOsDados()],[])))
                serieId=[id for id in self.dbSeries.acharDadoExato("idDaEscola", aluno['escola']) if id in self.dbSeries.acharDadoExato("serie", aluno['serie'])][-1]
                serie=self.dbSeries.getDadoComId(serieId)
                self.dbSeries.update(serieId, {"nDeAlunos": serie["nDeAlunos"]-1})  #Achei a serie e remove a vaga
                if aluno["serie"]=="FORMADO":
                    nextSerieName=series[-1]
                else: 
                    n=series.index(serie)-1
                    nextSerieName = series[0] if n <=0  else series[n] #proxima serie
                self.dbAluno.update(aluno['id'], {"serie": nextSerieName})

    
    def SremoverAlunos(self):
        for aluno in self.listaBusca:
            self.dbEscola.apagarDado(aluno['id'])

    
    def atualizarAno(self):
        anoAtual=date.today().year
        if len(self.dbAno.todosOsDados())==0:
            self.dbAno.salvarDado({'ano': anoAtual})
        anoAnterior = self.dbAno.getDado(1)['ano']
        if(anoAtual > anoAnterior):
            self.dbAno.update(1, {'ano':self.anoAtual})
            pular(1)
            #print(list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for i,escola in  enumerate(self.dbEscola.todosOsDados())],[]))))

    def closeEvent(self, event):
        [d.close() for d in self.dialog]
        super().closeEvent(event)       

    def restartProgram(self):
        self.app.restart=True
        self.close()
        self.app.quit()
    
    def updateCenter(self, lat, lng):       
            self.config.get().setInitialPos(lat,lng)
            self.config.save(DB_CONFIG)

    def addMarkerEscolas(self):
        #self.idEscolasMarker = []
        for i in self.dbEscola.todosOsDados():
            #self.idEscolasMarker.append(self.dbEscola.acharDado('nome', i['nome'])[0])
            #print("Latitude: " + str(i['lat']) + " Longitude: " + str(i['long']))
            self.mapWidget.centerAt(i['lat'], i['long'])
            self.mapWidget.addMarker(i['nome'], i['lat'], i['long'], **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_blue.png",
            draggable=True,
            title=i['nome']
            ))

    def addMap(self):
        if self.config.get().map==3:
            w=QtWidgets.QLabel("shapefile não está disponível, por favor mude para google ou osm nas configurações")
        elif self.config.get().map==2:
            #TODO implement here maps
            w=QtWidgets.QLabel("Here Maps não está disponível, por favor mude para google ou osm nas configurações")
        elif self.config.get().map==1:
            w=MapWidget()
        elif self.config.get().map==0:
            w=QGoogleMap(lat=self.config.get().lat, lng=self.config.get().lng)
            w.markerMoved.connect(self.markerMovido)
        else:
            w=QtWidgets.QLabel("Problema no banco de dados! Tente limpar as configurações")
        self.mapWidget=w
        self.horizontalLayout_4.addWidget(w)
        w.show()
   
 
    def centro(self):
        return [self.config.get().lat, self.config.get().lng]

    def exportImg(self):
        filename=QFileDialog.getSaveFileName(filter="Salvar Imagem (*.jpg)")[0]
        filename=filename if filename.endswith(".jpg") else filename+",jpg"        
        self.calc = imageThread(self, filename)
        self.calc.start()   
 

    def calcularRotas(self):
        self.calc = calcularRotasThread()
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.error.connect(lambda: messageDialog(title="Erro", message="Por favor escolha o arquivo osm no menu configurações"))
        self.calc.start()   
        self.loadingLabel.setText("Computando rotas ")   
        self.calc.finished.connect(self.cleanProgress)   
        self.update()
   
    def recalcularAlunos(self):
        db= self.dbAluno
        for aluno in db.todosOsDadosComId():
            aluno['lat']=''
            aluno['long']=''
            db.update(aluno['id'], aluno)
        
        self.calc = calcularAlunosThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()   
        self.loadingLabel.setText("Computando localização dos alunos")   
        self.calc.finished.connect(self.cleanProgress)   
        self.update()


    def recalcularEscolas(self):
        db= self.dbEscola
        for aluno in db.todosOsDadosComId():
            aluno['lat']=''
            aluno['long']=''
            db.update(aluno['id'], aluno)
 
        self.calc = calcularEscolasThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()         
        self.calc.finished.connect(self.cleanProgress)       
        self.loadingLabel.setText("Computando localização das Escolas")     
        self.update()


    def imporAlunoCsv(self):
        dialog=csvDialog(CSV_ALUNOS)
        dialog.exec_()
        res=dialog.result
        if not res: return
        try:
            dados=deepcopy(res)
            a=Aluno()
            for i, r in enumerate(res):            
                dados[i].update({"idade": a.calcularIdade(r['dataNasc'])})            
            db = self.dbAluno
            newDados=[]
            for dado in dados:
                dado[CSV_ALUNOS[8]]+=", "+Config.cidade()
                ids=self.dbEscola.acharDado("nome", dado["escola"])
                if dado['escola']:
                    if len(ids)==0:
                        if yesNoDialog(message="A escola com nome: "+str(dado['escola']+" não está cadastrada, deseja cadastrar?")):
                            eid=self.dbEscola.salvarDado({"nome": dado['escola'], "series": dado["serie"]})
                            self.dbSeries.salvarDado({"serie": dado["serie"], "vagas":100, "nDeAlunos": 1, "idDaEscola": eid})
                    else:
                        eid=ids[-1]
                        try:
                            serieId=[id for id in self.dbSeries.acharDadoExato("idDaEscola", eid) if id in self.dbSeries.acharDadoExato("serie", dado['serie'])][-1]
                            serie=self.dbSeries.getDado(serieId)
                            if int(serie[SERIES_ATTR[3]]) < int(serie[SERIES_ATTR[2]]):
                                self.dbSeries.update(serieId,{"nDeAlunos": serie["nDeAlunos"]+1})
                            else:
                                eid=""
                        except:
                            if yesNoDialog(message="Escola " + str(dado["escola"])+" não possui a serie "+str(dado["serie"]+ " \nDeseja criar?")):
                                eid=ids[-1]
                                self.dbSeries.salvarDado({"serie": dado["serie"], "vagas":100, "nDeAlunos": 1, "idDaEscola": eid})
                            else:
                                eid=""
                    dado['escola']=eid
                else:
                    dado['escola']=""
                newDados.append(dado)

            db.salvarDados(newDados)   

        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
    
        self.calc = calcularAlunosThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()   
        self.loadingLabel.setText("Computando localização dos alunos")   
        self.calc.finished.connect(self.cleanProgress)         


    def onCountChanged(self, value):
        self.progressBar.show()
        self.progressBar.setValue(value)


    def imporEscolaCsv(self):
        dialog=csvDialog(CSV_ESCOLAS)
        dialog.exec_()
        res=dialog.result
        if not res: return
        try:          
            db = self.dbEscola
            dbs= self.dbSeries
            for r in res:
                r[CSV_ESCOLAS[1]]+=", "+Config.cidade()
                ide=db.salvarDado(r)
                for s in r['series'].split(","): 
                 # dbs.salvarDado(dbs.toDict([id,s,0,0]))    
                  # Turma.update(s,r['nome'],{'vagas': 10})        
                    self.dbSeries.salvarDado({"idDaEscola":ide,
                    'serie': s, 
			        'vagas':100 , 
			        'nDeAlunos': 0,
                    })

        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1])

        self.calc = calcularEscolasThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()         
        self.calc.finished.connect(self.cleanProgress)       
        self.loadingLabel.setText("Computando localização das Escolas")              
       
    def cleanProgress(self):
        self.progressBar.setValue(0)
        self.loadingLabel.setText("")
        self.progressBar.hide()
        self.update()

    def buscarAluno(self): 

        self.addMarkerEscolas()

        self.idadeMinima = self.spinBoxIdadeMinima.value()
        self.idadeMaxima = self.spinBoxIdadeMaxima.value()
        self.listViewBusca.clear()
        busca = self.lineEditAluno.text()
        self.listaParaExportar=self.listaBusca=[]
        
        try:
            listaDeIdsBusca = self.dbAluno.acharDado(self.comboBoxBusca.currentText(), busca)
            listaDeIdsSeries = sum([self.dbAluno.acharDadoExato('serie', serie) for serie in self.dropDownSeries.selectedTexts()], [])     
            listaDeIdsIdade =[i for i in self.dbAluno.acharMaiorQue('idade', self.spinBoxIdadeMinima.value()) if i in self.dbAluno.acharMenorQue('idade', self.spinBoxIdadeMaxima.value())]
            ids=[i for i in listaDeIdsBusca if i in listaDeIdsSeries and i in listaDeIdsIdade]
            resultado=self.dbAluno.getDadosComId(ids)                
            self.buscaResultado=resultado
            self.resultado=resultado            

            j = 0
            for i in resultado:
                itemN = QtWidgets.QListWidgetItem() 
                widget = alunoBusca(self, i)                   
                itemN.setSizeHint(widget.sizeHint())  
                self.listViewBusca.addItem(itemN)                    
                self.listViewBusca.setItemWidget(itemN, widget)
                d=deepcopy(i)  #remover coisas inúteis para csv
                self.listaBusca.append(d)
                d.pop("id")  # ... ?                
                self.listaParaExportar.append(d)
                j += 1

            if j==0:
                self.listViewBusca.addItem("Nenhum aluno foi encontrado")
                
        except Exception as e:
            print(str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
            self.listViewBusca.addItem("Nenhum aluno foi cadastrado até o momento")

            
    def exportarBusca(self):
        if len(self.listaParaExportar) > 0:
            exportCsv(self.listaParaExportar)
        else:
            messageDialog(self, "Problema ao salvar arquivo", "", "Nenhum aluno corresponde a busca")

    def setarEndereco(self):       
        self.mapWidget.deleteMarker("aluno")
        aluno=self.resultado[self.listViewBusca.currentRow()]
        self.mapWidget.centerAt(aluno['lat'], aluno['long'])
        self.mapWidget.addMarker("aluno", aluno['lat'], aluno['long'], **dict(
        icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
        draggable=True,
        title=aluno['nome']
        ))
        self.latLongAns = [aluno['lat'], aluno['long']]
        if self.checkBox.isChecked():
            self.adicionarTodosCaminhos(aluno)
        else:
            self.adicionarCaminho(aluno)
    

    def markerMovido(self, n, lat, long):
        if n=="Centro":
            self.updateCenter(lat, long)
        elif n=="aluno":
            id = self.buscaResultado[self.listViewBusca.currentRow()]['id']        
            v = Aluno("", "", "", "", "", "", "", "", "", 0, 0, 0, lat, long, id)
            v.salvarCoordenada()          
            self.listViewBusca.clear()

            self.mapWidget.deleteMarker("aluno")
            aluno=self.resultado[self.listViewBusca.currentRow()]
            self.mapWidget.centerAt(lat, long)
            self.mapWidget.addMarker("aluno", lat, long, **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
            draggable=True,
            title=aluno['nome']
            ))

            self.buscarAluno()  
        elif n=="alunoNovo":
            v = Aluno("", "", "", "", "", "", "", "", "", 0, 0, 0, lat, long, self.alunoId)
            v.salvarCoordenada()           
            self.listViewBusca.clear()

            self.mapWidget.deleteMarker("alunoNovo")
            aluno=self.resultado[self.listViewBusca.currentRow()]
            self.mapWidget.centerAt(lat, long)
            self.mapWidget.addMarker("alunoNovo", lat, long, **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
            draggable=True,
            title=aluno['nome']
            ))

            self.buscarAluno()              
        elif n=="escola":
            #self.dbEscola.update(self.escolaId, {'lat':lat, 'long':long})
            self.mapWidget.centerAt(lat, long)
            self.mapWidget.addMarker("alunoNovo", lat, long, **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
            draggable=True,
            title=aluno['nome']
            ))
        else:
            print(n)
            idEscola = self.dbEscola.acharDado('nome', n)
            print(idEscola)
            print(self.dbEscola.getDadoComId(idEscola[0]))
            v = Escola(lat = lat, long = long, id=idEscola[0])
            v.salvarCoordenada()
   
    def newAlunoDialog(self): 
        self.aluno=self.varManager.read(Aluno(), DB_ADD_ALUNO) 
        dialog=NewAlunoDialog(self)             
        #dialog.setModal(True)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()
        self.update()


    def newEscolaDialog(self):  
        self.escola=self.varManager.read(Escola(), DB_ADD_ESCOLA) 
        dialog=NewEscolaDialog(self)             
        #dialog.setModal(True)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()
        self.update()

    def settingDialog(self):
        dialog=SettingsDialog(self)
       # dialog.setModal(True)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()
        self.update()

    def saveConfig(self):  
        self.dialog[-1].db.update(self.dialog[-1].db.acharDado('nome', 'cidade')[0], {'string': self.dialog[-1].lineEdit_2.text()})   
        cfg=self.config.get()
        if not cfg.isApplied:      
            self.config.get().apply()
            self.config.save("config")
            self.mapWidget.hide()
            self.horizontalLayout_4.removeWidget(self.mapWidget)
            self.addMap()
        self.update()
           
    def modalidadesDialog(self):
        self.modalidades=self.varManager.read(ListaModalidades(),DB_MODALIDADES_BASE)    
        dialog=ModalidadesDialog(self)
        #dialog.setModal(True)
        dialog.accepted.connect(self.modalidades.save)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()
        self.update()

    def adicionarCaminho(self, aluno):
        self.mapWidget.clearPaths()
        f=confPath()/ Path(PASTA_ALUNOS) / Path(str(aluno['id']))  
        if f.is_dir():
            f=f/Path(str(aluno['escola'])+".geojson")
            if f.is_file():
                with open(f, 'r') as file:
                    geo = file.read().replace("\"","\'")    
                self.mapWidget.addPath(geo)

    def adicionarTodosCaminhos(self,aluno):
        self.mapWidget.clearPaths()
        f=confPath()/ Path(PASTA_ALUNOS) / Path(str(aluno['id']))  
        if f.is_dir():
            for file in f.rglob("*.geojson"):
                if file.is_file():
                    with open(str(file), 'r') as fp:
                        geo = fp.read().replace("\"","\'")
                    self.mapWidget.addPath(geo, self.dbEscola.getDado(file.stem)['nome'])

    def update(self):
        self.dropDownEscolas.repopulate(Escola.todasAsEscolas())    
        #self.dropDownEscolas.todos.setChecked(True)
        indices=self.dropDownEscolas.selectedIndexes()
        self.dropDownSeries.repopulate(list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) 
        for i,escola in enumerate(self.dbEscola.todosOsDados()) if i in indices],[]))))       
        #self.dropDownSeries.todos.setChecked(True)
        self.addMarkerEscolas()


def main(*args):
    global CONF_PATH
    while True:
        try:
            app = QtWidgets.QApplication(*args)
            app.restart=False
            win=MainWindow(app)
            from pathlib import Path
            path=QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.ConfigLocation)[0] / Path(NAME)
            path.mkdir(parents=True, exist_ok=True)  
            CONF_PATH=str(path)
            print(CONF_PATH)
            win.showMaximized()
            currentExitCode=app.exec_()          
            if not app.restart:
                break        
        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1], info="O programa irá reiniciar")
            print(str(traceback.format_exception(None, e, e.__traceback__)))
            currentExitCode=-13
    return currentExitCode   

if __name__ == '__main__':
    currentExitCode=main(sys.argv)
    sys.exit(currentExitCode)
