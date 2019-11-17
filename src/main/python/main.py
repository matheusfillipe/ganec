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
    SOBRE,_= uic.loadUiType(BASEPATHS[I]+"ui/dialogs/sobre.ui")

except:
    I=1
    MAIN_WINDOW, _ = uic.loadUiType(BASEPATHS[I]+"ui/mainWindow.ui")
    SETTINGS_DIALOG,_ = uic.loadUiType(BASEPATHS[I]+"ui/dialogs/settingsDialog.ui")
    SOBRE,_= uic.loadUiType(BASEPATHS[I]+"ui/dialogs/sobre.ui")
  

RESET=0   

class sobreDialog(QtWidgets.QDialog, SOBRE):
    def __init__(self,iface):
        QtWidgets.QWidget.__init__(self)
        SETTINGS_DIALOG.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)


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
        self.ceptxt : QtWidgets.QLineEdit

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

        try:
            self.ceptxt.setText(db.getDado(db.acharDado('nome','cep')[-1])['string'])
        except:
            self.db.salvarDado({'nome': 'cep', 'string': ''})
            self.ceptxt.setText("")


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

            shutil.rmtree(str(tmpPath()), ignore_errors=True)


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
                shutil.rmtree(str(confPath()), ignore_errors=True)
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
    operatonFinished=pyqtSignal()
    searchFinished=pyqtSignal(list, list)
    progLabel=pyqtSignal(str)
    countChanged=pyqtSignal(int)
    docxConvertionFinished=pyqtSignal(str)

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
        rmfile=lambda path: (path.unlink() and self.updateScreen()) or True if path.is_file() else 1
        self.actionApagar_todas_Escolas.triggered.connect(lambda: rmfile(confPath()/Path(CAMINHO['escola'])) 
        if yesNoDialog(message="Tem certeza que deseja apagar todos os escolas?") else lambda: 0)
        self.actionApagar_todos_Alunos.triggered.connect(lambda: rmfile(confPath()/Path(CAMINHO['aluno'])) 
        and shutil.rmtree(str(confPath()/Path("alunos")), ignore_errors=True)
        if yesNoDialog(message="Tem certeza que deseja apagar todos os alunos?") else lambda: 0)
        
        self.idEscola = 0

        self.latLongAns = ["a"]
        self.spinBoxIdadeMaxima.setValue(50)
        self.spinBoxIdadeMinima.setValue(0)
        self.comboBoxBusca.addItems(ATRIBUTOS['aluno'][:-2])        
        #self.lineEditAluno.textChanged.connect(self.buscarAluno) #aqui faz pesquisar os alunos sempre que digitar. 
        self.lineEditAluno.editingFinished.connect(self.buscarAluno) #aqui faz pesquisar os alunos sempre que enter 
        self.scrollAreaTeste : QtWidgets.QScrollArea
        self.addMap()
        self.dialog=[]
        self.actionAlunos_3.triggered.connect(lambda: self.imporAlunoCsv())
        self.actionEscolar.triggered.connect(self.imporEscolaCsv)
        self.actionCalcular_Rotas_2.triggered.connect(self.calcularRotas)
        self.actionRecalcular_endere_os_de_alunos.triggered.connect(self.recalcularAlunos)
        self.actionRecalcular_endere_os_de_escolas.triggered.connect(self.recalcularEscolas)
        self.actionExportar_imagem.triggered.connect(lambda: self.exportImg(self.mapWidget))
        self.actionAvan_ar_todos_os_alunos_em_um_ano.triggered.connect(lambda: self.pular(1))
        self.actionRetornar_todos_os_alunoes_um_ano.triggered.connect(lambda: self.pular(-1))
        self.actionRemover_todos.triggered.connect(self.SremoverAlunos)
        self.actionAvan_ar_uma_Turma.triggered.connect(self.SacanvaTurma)
        self.actionRetornar_uma_turma.triggered.connect(self.SretornaTurma)
        self.actionRemover_Escola.triggered.connect(self.SremoverEscola)
        self.actionRecalcular_Series.triggered.connect(self.serieRecalc)
        self.actionAjuda.triggered.connect(self.ajuda)
        self.actionSobre.triggered.connect(self.sobre)
        self.actionDist_ncia.triggered.connect(self.distTool)
        self.actionAlunos_n_o_localizados.triggered.connect(self.alunosNLocalizados)
        self.actionMostrar_Escolas.triggered.connect(self.hideEscolas)
        self.actionMostar_Alunos.triggered.connect(self.showAlunos)
        self.actionAlunos_4.triggered.connect(lambda: self.verificarOsm() and editarAlunoDialog(self).exec_())
        self.actionEscolas_2.triggered.connect(lambda: self.verificarOsm() and editarEscolaDialog(self).exec_())
        self.actionImportar_Alunos.triggered.connect(self.importWord)
        self.actionSalvar.triggered.connect(self.backup)
        self.actionCarregar.triggered.connect(self.carregar)
        self.actionDefinir_Turma.triggered.connect(self.definirTurma)
        self.actionDefinir_Escola.triggered.connect(self.definirEscola)

        self.countChanged.connect(self.onCountChanged)
        self.listViewBusca.overlay=Overlay(self.listViewBusca, "")
        

        self.searchFinished.connect(self.onSearchFinished)        
        self.docxConvertionFinished.connect(self.imporAlunoCsv)
        
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
        self.operatonFinished.connect(self.cleanProgress)
        self.progLabel.connect(lambda txt: self.blockBusca() or self.loadingLabel.setText(txt))
        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F5"), self)
        shortcut.activated.connect(self.updateScreen)
        self.updateScreen() 


    def carregar(self):
        reply = yesNoDialog(iface=self, message="Isso destruirá os dados atuais, faça um backup or salve-os.", 
        info="Tem certeza disso?")     
        if reply:
            filename = QtWidgets.QFileDialog.getOpenFileName(filter="Arquivo de backup (*.zip)")[0]
            if not filename: return
            try:
                self.iface.varManager.removeDatabase()
            except:
                pass
            try:
                shutil.rmtree(str(confPath()), ignore_errors=True)
            except:
                pass

            z = zipfile.ZipFile(filename, "r") 
            z.extractall(QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.ConfigLocation)[0])
           # messageDialog(self, message="O programa irá reiniciar")
           # self.close()
           # self.iface.restartProgram()               
        self.updateScreen() 

    def backup(self):
        filename : str
        filename = QtWidgets.QFileDialog.getSaveFileName(filter="Arquivo de backup (*.zip *.ZIP)")[0]
        if filename in ['', None]: return
        filename= filename if filename.endswith(".zip") else filename+".zip"
        zip_file = zipfile.ZipFile(filename, 'w')
        for path in confPath().rglob('*'):
            path: Path
            zip_file.write(str(path), str(Path(NAME)/path.relative_to(confPath())), zipfile.ZIP_DEFLATED)
        zip_file.close()
  
    
    def ajuda(self):
        import webbrowser
        webbrowser.open('https://github.com/matheusfillipe/ganec/wiki/Como-Usar')

    def sobre(self):
        sobreDialog(self).exec_()

    def showEscolas(self):
        self.actionMostrar_Escolas.triggered.disconnect()
        self.actionMostrar_Escolas.triggered.connect(self.hideEscolas)
        self.actionMostrar_Escolas.setText("Esconder Escolas")
        self.addMarkerEscolas()       


    def hideEscolas(self):
        self.actionMostrar_Escolas.triggered.disconnect()
        self.actionMostrar_Escolas.triggered.connect(self.showEscolas)     
        self.actionMostrar_Escolas.setText("Mostrar Escolas")
        for i in self.dbEscola.todosOsDados():
            self.mapWidget.deleteMarker(i['nome']) 

    def showAlunos(self):
        self.actionMostar_Alunos.triggered.disconnect()
        self.actionMostar_Alunos.triggered.connect(self.hideAlunos)
        self.actionMostar_Alunos.setText("Esconder Alunos")
        for i in self.dbAluno.todosOsDados():
            self.mapWidget.addMarker(i['nome'], i['lat'], i['long'], **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
            draggable=True,
            title=i['nome']
            ))

    def hideAlunos(self):
        self.actionMostar_Alunos.triggered.disconnect()
        self.actionMostar_Alunos.triggered.connect(self.showAlunos) 
        self.actionMostar_Alunos.setText("Mostrar Alunos")
        for i in self.dbAluno.todosOsDados():
            self.mapWidget.deleteMarker(i['nome']) 


    def distTool(self):
        if not self.verificarOsm(): return
        self.listViewBusca : QtWidgets.QListWidget
        selectedIndexes=self.listViewBusca.selectedIndexes()
        center=[self.config.get().lat, self.config.get().lng]
        if selectedIndexes:
            aluno=self.listaBusca[selectedIndexes[-1].row()]
            ptA=[aluno['lat'], aluno['long']]
            if aluno['escola']:
                i=self.dbEscola.getDado(aluno['escola'])
                ptB=[i['lat'], i['long']]
            else:
               ptB=deepcopy(center)                           
        else:
            ptA=deepcopy(center)            
            ptB=deepcopy(center)            
       
        w, net=basicWin(ptA, ptB, osmFilePath())
        for i in self.dbEscola.todosOsDados():                    
            w.addMarker(i['nome'], i['lat'], i['long'], **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_blue.png",
            draggable=False,
            title=i['nome']
            ))
        w : QtWebEngineWidgets.QWebEngineView
        try:
            self.actionImagem.triggered.disconnect()       
            self.separator.triggered.disconnect()       
            self.actionGoogle_Maps_KML.triggered.disconnect()       
            self.actionShapefile.triggered.disconnect()       
        except:
            pass
        self.menuMapa.setEnabled(True)        
        self.actionImagem.triggered.connect(lambda:  self.exportImg(w))
        self.actionGeojson.triggered.connect(lambda:  net.save_geojson(self.saveFile("geojson") if _ else lambda: 0))
        self.actionGoogle_Maps_KML.triggered.connect(lambda: net.save_kml(self.saveFile("kml")  if _ else lambda: 0))
        self.actionShapefile.triggered.connect(lambda: net.save_shp(self.saveFile("shp")  if _ else lambda: 0) )
        w.closed.connect(lambda: self.menuMapa.setEnabled(False))

    def saveFile(self, filter):
        file=QFileDialog.getSaveFileName(filter="Arquivo "+ filter +" (*."+filter+")")[0]
        file = file if file.endswith(filter) else file+"."+filter   
        return file if file else False
    
    def openFile(self, filter):
        file=QFileDialog.getOpenFileName(filter="Arquivo "+ filter +" (*."+filter+")")[0]      
        return file if file else False
 
    def serieRecalc(self):
        self.loadingLabel.setText("Recalculando número de alunos em cada série")   
        self.blockBusca()
        self.serieRecalcThread()

    @nogui
    def serieRecalcThread(self):
        correctSeries(self.countChanged)
        self.operatonFinished.emit()

    
    def definirTurma(self):
        novo, ok=QtWidgets.QInputDialog.getItem(self, "Definir Turmas", "Turmas", SERIES, 0, False)
        if not ok or not novo: return
        self.definirTurmasThread(novo)

    @nogui
    def definirTurmasThread(self, novo):
        self.progLabel.emit("Definindo Turmas ")       
        for i,aluno in enumerate(self.listaBusca):
            self.countChanged.emit(int(i/len(self.listaBusca)*100))           
            self.dbAluno.update(aluno['id'], {"serie": novo})
        self.operatonFinished.emit()

    def definirEscola(self):
        novo, ok=QtWidgets.QInputDialog.getItem(self, "Definir Escolas", "Escolas", 
        [e['nome'] for e in self.dbEscola.todosOsDados()], 0, False)
        novo=[e['id'] for e in self.dbEscola.todosOsDadosComId() if e['nome']==novo][-1]
        if not ok or not novo: return
        self.definirEscolaThread(novo)

    @nogui
    def definirEscolaThread(self, novo):
        self.progLabel.emit("Definindo Turmas ")       
        for i,aluno in enumerate(self.listaBusca):
            self.countChanged.emit(int(i/len(self.listaBusca)*100))           
            self.dbAluno.update(aluno['id'], {"escola": novo})
        self.operatonFinished.emit()

    @nogui
    def SremoverEscola(self, k=None):
        self.progLabel.emit("Removendo Escolas ")       
        for i,aluno in enumerate(self.listaBusca):
            self.countChanged.emit(int(i/len(self.listaBusca)*100))           
            if aluno['escola'] != "" or aluno['escola'] != None:
                self.dbAluno.update(self.dbAluno.acharDadoExato('nome',aluno['nome'])[0] , {"escola": ""})
        self.operatonFinished.emit()
      #  self.updateScreen()

    @nogui            
    def SacanvaTurma(self, k=None):
        self.progLabel.emit("Avançando Turmas ")
        for i,aluno in enumerate(self.listaBusca):
            self.countChanged.emit(int(i/len(self.listaBusca)*100))
            series=SERIES #list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in self.dbEscola.todosOsDados()],[])))
            if aluno['escola']:
                from collections import OrderedDict
                escola=self.dbEscola.getDadoComId(aluno['escola'])            
                serieId=[id for id in self.dbSeries.acharDadoExato("idDaEscola", aluno['escola']) if id in self.dbSeries.acharDadoExato("serie", aluno['serie'])]
                if serieId:                    
                    serie=self.dbSeries.getDadoComId(serieId[-1])
                    self.dbSeries.update(serieId[-1], {"nDeAlunos": int(serie["nDeAlunos"])-1})  #Achei a serie e remove a vaga
                    serie=serie['serie']
                else:
                    serie=aluno['serie']                   
                serie=aluno['serie']
            if aluno["serie"]=="FORMADO":
                nextSerieName="FORMADO"
            else:
                n=series.index(aluno['serie'])+1
                nextSerieName = "FORMADO" if n > len(series)-1 else series[n] #proxima serie
            if aluno['escola']:
                novaSerieId=[id for id in self.dbSeries.acharDadoExato("idDaEscola", aluno['escola']) if id in self.dbSeries.acharDadoExato("serie", nextSerieName)]
                if novaSerieId: #se a escola não tem a série, não muda
                    novaSerieDados=self.dbSeries.getDado(novaSerieId[-1])
                    self.dbSeries.update(novaSerieId[-1],{"vagas": int(novaSerieDados['vagas'])+1})  #Adiciona o aluno a nova vaga                                               else:

            self.dbAluno.update(aluno['id'], {"serie": nextSerieName})
        self.operatonFinished.emit()
           
    @nogui
    def SretornaTurma(self, k=None):
        self.progLabel.emit("Retornando Turmas ")
        for i,aluno in enumerate(self.listaBusca):
            self.countChanged.emit(int(i/len(self.listaBusca)*100))
            series=SERIES #list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in self.dbEscola.todosOsDados()],[])))
            if aluno['escola']:
                from collections import OrderedDict
                escola=self.dbEscola.getDadoComId(aluno['escola'])            
                serieId=[id for id in self.dbSeries.acharDadoExato("idDaEscola", aluno['escola']) if id in self.dbSeries.acharDadoExato("serie", aluno['serie'])]
                if serieId:
                    serie=self.dbSeries.getDadoComId(serieId[-1])
                    self.dbSeries.update(serieId[-1], {"nDeAlunos": int(serie["nDeAlunos"])-1})  #Achei a serie e remove a vaga
                    serie=serie['serie']
                else:
                    serie=aluno['serie']
            else:
                serie=aluno['serie']
            if aluno["serie"]=="FORMADO":
                nextSerieName=series[-1]
            elif aluno['serie']==series[0]:
                continue
            else: 
                n=series.index(aluno['serie'])-1
                nextSerieName = series[0] if n <=0  else series[n] #proxima serie
            if aluno['escola']:
                novaSerieId=[id for id in self.dbSeries.acharDadoExato("idDaEscola", aluno['escola']) if id in self.dbSeries.acharDadoExato("serie", nextSerieName)]
                if novaSerieId: #se a escola não tem a série, não muda
                    novaSerieDados=self.dbSeries.getDado(novaSerieId[-1])
                    self.dbSeries.update(novaSerieId[-1],{"vagas": int(novaSerieDados['vagas'])+1})  #Adiciona o aluno a nova vaga                                               else:

            self.dbAluno.update(aluno['id'], {"serie": nextSerieName})
        self.operatonFinished.emit()

    @nogui 
    def SremoverAlunos(self, k=None):
        self.progLabel.emit("Removendo Alunos ")
        for i,aluno in enumerate(self.listaBusca):
            if "id" in aluno:
                self.countChanged.emit(int(i/len(self.listaBusca)*100))
                self.dbAluno.apagarDado(aluno['id'])
                shutil.rmtree(str(confPath()/Path("alunos")/Path(str(aluno['id']))), ignore_errors=True)
        self.operatonFinished.emit()
    
    def atualizarAno(self):
        anoAtual=date.today().year
        if len(self.dbAno.todosOsDados())==0:
            self.dbAno.salvarDado({'ano': anoAtual})
        anoAnterior = self.dbAno.getDado(1)['ano']
        if(anoAtual > anoAnterior):
            self.dbAno.update(1, {'ano':self.anoAtual})
            self.pular(1)
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
        self.hideEscolas()
        for i in self.dbEscola.todosOsDados():
            self.mapWidget.addMarker(i['nome'], i['lat'], i['long'], **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_blue.png",
            draggable=True,
            title=i['nome']
            ))
    
    def verificarOsm(self):
        osmpath=osmFilePath()  #???
        if not Path(osmpath).is_file() or Path(osmpath).suffix!=".osm":
            messageDialog(self, message="Aruivo de mapa  (.osm) não foi configurado!")
            return False
        else:
            return True
 

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
            db=DB(str(confPath()/Path('settings.db')),"strings", ['nome', 'string'])
            try:
                w.setPostalCode(db.getDado(db.acharDado('nome','cep')[-1])['string'])
            except:
                pass
        else:
            w=QtWidgets.QLabel("Problema no banco de dados! Tente limpar as configurações")
        self.mapWidget=w
        self.horizontalLayout_4.addWidget(w)
        w.show()
   
 
    def centro(self):
        return [self.config.get().lat, self.config.get().lng]

    def raiseWindow(self, view):
        try:
            view.setWindowState(view.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            view.activateWindow() 
        except:
            pass
        
    def exportImg(self,w):
        self.raiseWindow(w)
        time.sleep(.5)
        import tempfile
        temp=tempfile.gettempdir() + "/" "temp"
        w.saveImage(temp)                
        filename=self.saveFile("jpg")
        if not filename: return      
        shutil.move(temp, filename)                
   
    def calcularRotas(self):
        self.blockBusca()
        self.calc = calcularRotasThread()
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.error.connect(lambda: messageDialog(title="Erro", message="Por favor escolha o arquivo osm no menu configurações"))
        self.calc.start()   
        self.loadingLabel.setText("Computando rotas ")   
        self.calc.finished.connect(self.cleanProgress)   
        self.updateScreen()
   
    def recalcularAlunos(self):
        self.blockBusca()
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
        self.updateScreen()


    def recalcularEscolas(self):
        self.blockBusca()
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
        self.updateScreen()

    def importWord(self):
        if not self.verificarOsm(): return
        fileapth=self.openFile("docx")
        if not fileapth: return
        self.cleanProgress()
        self.loadingLabel.setText("Convertendo arquivo  ")
        self.docx2csvThread(fileapth)
    
    @nogui
    def docx2csvThread(self,filepath, k=None):        
        path=""
        try:
            from docx import Document
            document = Document(filepath)                                         
            t=document.tables[0]
            import tempfile
            path=tempfile.gettempdir()+"/zoneacsv.csv"
            import csv
            with open(path,"w",newline='') as f:
                writer=csv.writer(f, delimiter=CSV_SEPARATOR)
                j=1
                for r in t.rows:
                    row=[]   
                    self.countChanged.emit(int(j/len(t.rows)*100))    
                    for c in r.cells:
                        row.append(c.text)
                    diff=len(CSV_ALUNOS)-len(row)
                    if diff>0:
                        [row.append("_") for i in range(diff)]
                    writer.writerow(row)
                    j+=1             
        except Exception as e:
            print(str(traceback.format_exception(None, e, e.__traceback__)))
        self.docxConvertionFinished.emit(path)
               

    def imporAlunoCsv(self, file=None):    
        if not file is None: 
            self.cleanProgress()    
        if not self.verificarOsm(): return
        if file=="": 
            messageDialog(message="Erro no arquivo") 
            return
        dialog=csvDialog(CSV_ALUNOS, file=file)
        dialog.exec_()
        res=dialog.result
        if not res: return
        self.listaBusca=[]
        self.listaParaExportar=[]
        IDS=[]
        self.listViewBusca.clear()
        try:
            dados=deepcopy(res)
            a=Aluno()
            for i, r in enumerate(res):            
                dados[i].update({"idade": a.calcularIdade(r['dataNasc'])})            
            db = self.dbAluno
            newDados=[]
            naoPerguntar=[]
            for dado in dados:
                if not dado['nome']:
                    continue
                dado[CSV_ALUNOS[8]]+=", "+Config.cidade()
                ids=self.dbEscola.acharDado("nome", dado["escola"])
                if dado['escola']:
                    if len(ids)==0:
                        if not dado['escola'] in naoPerguntar:
                            if yesNoDialog(message="A escola com nome: "+str(dado['escola']+" não está cadastrada, deseja cadastrar?")):
                                eid=self.dbEscola.salvarDado({"nome": dado['escola'], "series": dado["serie"]})
                                self.dbSeries.salvarDado({"serie": dado["serie"], "vagas":100, "nDeAlunos": 1, "idDaEscola": eid})
                            else:
                                eid=""
                                naoPerguntar.append(dado['escola'])
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
                          #  if yesNoDialog(message="Escola " + str(dado["escola"])+" não possui a serie "+str(dado["serie"]+ " \nDeseja criar?")):
                          #      eid=ids[-1]
                          #      self.dbSeries.salvarDado({"serie": dado["serie"], "vagas":100, "nDeAlunos": 1, "idDaEscola": eid})
                          #  else:
                            eid=ids[-1]
                                
                    dado['escola']=eid
                else:
                    dado['escola']=""
                newDados.append(dado)
            IDS=db.salvarDados(newDados)

        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
        self.addAlunosBusca(IDS)
        self.calc = calcularAlunosThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()   
        self.loadingLabel.setText("Computando localização dos alunos")   
        self.calc.finished.connect(self.cleanProgress)         


    def onCountChanged(self, value):
        self.progressBar.show()
        self.progressBar.setValue(value)
        self.menuComputar.setEnabled(False)
        self.menuCadastrar.setEnabled(False)
        self.actionRecalcular_Series.setEnabled(False)
        self.menuZoneamento.setEnabled(False)      
        if value>=99:
            self.menuComputar.setEnabled(True)
            self.menuCadastrar.setEnabled(True)
            self.actionRecalcular_Series.setEnabled(True)
            self.menuZoneamento.setEnabled(True)
    
    def blockBusca(self):       
        for i in range(self.listViewBusca.count()):
            w=self.listViewBusca.itemWidget(self.listViewBusca.item(i))
            w.editar=False

    def enableBusca(self):
        for i in range(self.listViewBusca.count()):
            w=self.listViewBusca.itemWidget(self.listViewBusca.item(i))
            w.editar=True

    def imporEscolaCsv(self):
        if not self.verificarOsm(): return
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
       #self.updateScreen()
        self.menuComputar.setEnabled(True)
        self.menuCadastrar.setEnabled(True)
        self.actionRecalcular_Series.setEnabled(True)
        self.menuZoneamento.setEnabled(True)
        self.enableBusca()

    def alunosNLocalizados(self):
        self.listViewBusca.clear()
        busca = self.lineEditAluno.text()
        self.listaParaExportar=[]
        self.listaBusca=[]         
        ids=[]
        center=[float(self.config.get().lat), float(self.config.get().lng)]
        for aluno in self.dbAluno.todosOsDadosComId():
            if [float(aluno['lat']), float(aluno['long'])] == center:
                ids.append(aluno['id'])
        self.addAlunosBusca(ids)

    def addAlunosBusca(self, ids):
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
            self.listaBusca.append(deepcopy(i))
            d.pop("id")            
            if d['escola']:
                d['escola']=self.dbEscola.getDado(d['escola'])['nome']
            self.listaParaExportar.append(d)
            j += 1

        if j==0:
            itemN = QtWidgets.QListWidgetItem("Nenhum aluno foi encontrado") 
            itemN.setFlags(itemN.flags() & ~QtCore.Qt.ItemIsEnabled);
            self.listViewBusca.addItem(itemN)             
        

    def buscarAluno(self): 
        self.idadeMinima = self.spinBoxIdadeMinima.value()
        self.idadeMaxima = self.spinBoxIdadeMaxima.value()
        self.listViewBusca.clear()
        self.listaParaExportar=[]
        self.listaBusca=[]   
        self.listViewBusca.overlay.resize(QtCore.QSize(self.listViewBusca.width(),500))
        self.buscarAlunosThread()
    
    @nogui
    def buscarAlunosThread(self, k=None):
        self.listViewBusca.overlay.started.emit()
        busca = self.lineEditAluno.text()
        try:
            listaDeIdsEscola = []
            ids = []
            semEscola = False
            series = self.dropDownSeries.selectedTexts()            
            escolas = []
            semEscola = False
            for i in self.dropDownEscolas.selectedTexts():
                if i == "Sem Escola":
                    semEscola = True
                escolas.append(str(i))
            
            escolas = list(set(escolas))
            series  = list(set(series ))
            
            listaDeIdsNome = self.dbAluno.acharDado(self.comboBoxBusca.currentText(), busca)
            for i in listaDeIdsNome:
                aluno = self.dbAluno.getDadoComId(i)
                if aluno['escola']:
                    for j in escolas:
                        if self.dbEscola.getDadoComId(aluno['escola'])['nome'] == j or self.dropDownEscolas.todos.isChecked():
                            for k in series:
                                if aluno['serie'] == k or self.dropDownSeries.todos.isChecked():
                                    for l in range(self.spinBoxIdadeMinima.value(), self.spinBoxIdadeMaxima.value()+1):
                                        if aluno['idade'] == l:
                                            ids.append(i)
                                            break
                                    break
                            break
                elif semEscola:
                    ids.append(i)
            resultado=self.dbAluno.getDadosComId(ids)  
            escolas=[]              
            for i in resultado:
                e=deepcopy(i)
                if i['escola']:         
                    e['escola']=self.dbEscola.getDado(i['escola'])['nome']                
                escolas.append(e)            
        except:           
            resultado=[-1]
            escolas=[]            

        self.searchFinished.emit(resultado, escolas)
        self.listViewBusca.overlay.stoped.emit()

    def onSearchFinished(self, resultado, escolas):
        self.listViewBusca.clear()
        if len(resultado)==1 and resultado[0]==-1:
            itemN = QtWidgets.QListWidgetItem("Nenhum aluno foi cadastrado até o momento ou houve um \nproblema com o banco de dados")
            itemN.setFlags(itemN.flags() & ~QtCore.Qt.ItemIsEnabled);
            self.listViewBusca.addItem(itemN)             
        else:            
            self.buscaResultado=resultado
            self.resultado=resultado
            j = 0
            for i, e in zip(resultado, escolas):
                itemN = QtWidgets.QListWidgetItem() 
                widget = alunoBusca(self, i) 
                itemN.setSizeHint(widget.sizeHint())  
                self.listViewBusca.addItem(itemN)                    
                self.listViewBusca.setItemWidget(itemN, widget)
                d=deepcopy(e)  #remover coisas inúteis para csv
                self.listaBusca.append(deepcopy(i))
                d.pop("id")  
                self.listaParaExportar.append({k:d[k] for k in ATRIBUTOS['aluno']})
                j += 1
            if j==0:
                itemN = QtWidgets.QListWidgetItem("Nenhum aluno foi encontrado.")            
                itemN.setFlags(itemN.flags() & ~QtCore.Qt.ItemIsEnabled);
                self.listViewBusca.addItem(itemN)         
        
        #self.updateScreen()
            
    def exportarBusca(self):
        if hasattr(self, "listaParaExportar") and len(self.listaParaExportar)>0:
            exportCsv(self.listaParaExportar)
        else:
            messageDialog(self, "Problema ao salvar arquivo", "", "Nenhum aluno encontrado na lista de busca")
        

    def setarEndereco(self): 
        try:      
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
        except:
            self.mapWidget.centerAt(self.config.get().lat, self.config.get().lng)
    

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
            #print(n)
            idEscola = self.dbEscola.acharDado('nome', n)
            #print(idEscola)
            #print(self.dbEscola.getDadoComId(idEscola[0]))
            if(len(idEscola)>0):
                v = Escola(lat = lat, long = long, id=idEscola[0])
                v.salvarCoordenada()
             
   
    def newAlunoDialog(self): 
        if not self.verificarOsm(): return
        if Config.cidade():
            #self.aluno=self.varManager.read(Aluno(), DB_ADD_ALUNO) 
            dialog=NewAlunoDialog(self)             
            #dialog.setModal(True)
            self.dialog.append(dialog)
            dialog.show()
            dialog.exec_()
            self.updateScreen()
        else:
            messageDialog(self, "Sem cidade", "Vá em Opcões>Configurações>Cidade", "Ainda não tem uma cidade selecionada")
        
    def newEscolaDialog(self):
        if not self.verificarOsm(): return
        if Config.cidade():
           # self.escola=self.varManager.read(Escola(), DB_ADD_ESCOLA) 
            dialog=NewEscolaDialog(self)             
            #dialog.setModal(True)
            self.dialog.append(dialog)
            dialog.show()
            dialog.exec_()
            self.updateScreen()
        else:
            messageDialog(self, "Sem cidade", "Vá em Opcões>Configurações>Cidade", "Ainda não tem uma cidade selecionada")

    def settingDialog(self):
        dialog=SettingsDialog(self)
       # dialog.setModal(True)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()
        self.updateScreen()

    def saveConfig(self):  
        self.dialog[-1].db.update(self.dialog[-1].db.acharDado('nome', 'cidade')[0], {'string': self.dialog[-1].lineEdit_2.text()})   
        self.dialog[-1].db.update(self.dialog[-1].db.acharDado('nome', 'cep')[0], {'string': self.dialog[-1].ceptxt.text()})             
        try:
            self.mapWidget.setPostalCode(self.dialog[-1].ceptxt.text())
        except:
            pass
        cfg=self.config.get()
        if not cfg.isApplied:      
            self.config.get().apply()
            self.config.save("config")
            self.mapWidget.hide()
            self.horizontalLayout_4.removeWidget(self.mapWidget)
            self.addMap()
        self.updateScreen()
           
    def modalidadesDialog(self):
        self.modalidades=self.varManager.read(ListaModalidades(),DB_MODALIDADES_BASE)    
        dialog=ModalidadesDialog(self)
        #dialog.setModal(True)
        dialog.accepted.connect(self.modalidades.save)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()
        self.updateScreen()

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

    def updateScreen(self):
        self.listViewBusca.clear()
        self.mapWidget.deleteMarker("aluno")       
        escolas = []
        for i in Escola.todasAsEscolas():
            escolas.append(i)
        escolas.append("Sem Escola")
        self.dropDownEscolas.repopulate(escolas)
        #indices=self.dropDownEscolas.selectedIndexes()
        series=SERIES #list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in self.dbEscola.todosOsDados()],[])))
        self.dropDownSeries.repopulate(series)
        self.addMarkerEscolas()
        self.dropDownEscolas.todos.setChecked(True)
        self.dropDownSeries.todos.setChecked(True)
        self.dropDownEscolas.todos.stateChanged.emit(2)
        self.dropDownSeries.todos.stateChanged.emit(2)        
        self.menuComputar.setEnabled(True)
        self.menuCadastrar.setEnabled(True)
        self.actionRecalcular_Series.setEnabled(True)
        self.menuZoneamento.setEnabled(True)
    
    @nogui
    def pular(self, PULO):
        self.progLabel.emit("Avançando Turmas...")
        from collections import OrderedDict
        dbEscola=self.dbEscola#DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        dbAlunos=self.dbAluno#DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        dbSeries=self.dbSeries #DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
        series=SERIES #list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in dbEscola.todosOsDados()],[])))
        print("Alunos: ",[aluno['serie'] for aluno in dbAlunos.todosOsDados()])
        print("Series: ",series)
        #PULO=1 #muda para -1 para descer de séries
        #return
        lista=dbAlunos.todosOsDadosComId()
        for ci,aluno in enumerate(lista):
            ## Move o aluno para a próxima serie
            self.countChanged.emit(int(ci/len(lista)*100))
            serie=aluno['serie']
            if serie=="FORMADO":
                continue
            elif serie==series[0]:        
                continue
            else:
                serieIndex=series.index(serie)
                nextSerieIndex=serieIndex+PULO
                if nextSerieIndex>len(series)-1: #ALUNO FORMOU
                    serie="FORMADO"  #Serie para todos que formaram (Como isso não existe em nenhuma escola vai ser ignorado)
                elif nextSerieIndex<=0: #or not serie in escola["series"].split(SEPARADOR_SERIES):  #Se a escola não te suporta mais
                    serie=series[0]
                else:
                    serie=series[nextSerieIndex]           
                if aluno['escola']:
                    escolaId=aluno['escola']
                    serieId=[id for id in dbSeries.acharDadoExato("idDaEscola", escolaId) if id in dbSeries.acharDadoExato("serie", aluno['serie'])]
                    if serieId:
                        serieDados=dbSeries.getDado(serieId[-1])
                        escola=dbEscola.getDado(escolaId)
                        ## remove a vaga do aluno na tabela de series antiga
                        dbSeries.update(serieId[-1],{"vagas": int(serieDados['vagas'])-1}) 
                    novaSerieId=[id for id in dbSeries.acharDadoExato("idDaEscola", escolaId) if id in dbSeries.acharDadoExato("serie", serie)]
                    if novaSerieId: #se a escola não tem a série, não muda
                        novaSerieDados=dbSeries.getDado(novaSerieId[-1])
                        dbSeries.update(novaSerieId[-1],{"vagas": int(novaSerieDados['vagas'])+1})  #Adiciona o aluno a nova vaga                                   

            dbAlunos.update(aluno['id'], {"serie":serie})

        print("Alunos: ",[aluno['serie'] for aluno in dbAlunos.todosOsDados()])
        print("Series: ",series)
        self.operatonFinished.emit()


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
