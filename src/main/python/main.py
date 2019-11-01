# -*- coding: utf-8 -*-

"""

/**********************************************************************************
GANEC = Gestor de Alunos Nas Escolas do Carmo 
    
        
        begin                : 2019-15-09
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Fellipe, Lucas e Matheus
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
* OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
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

MAIN_WINDOW, _ = uic.loadUiType("./src/main/python/ui/mainWindow.ui")
SETTINGS_DIALOG,_ = uic.loadUiType("./src/main/python/ui/dialogs/settingsDialog.ui")

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
            import shutil
            shutil.rmtree(str(confPath()), ignore_errors=True)
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
        if RESET:
            #self.varManager.removeDatabase()
            self.close()

        self.dbAluno = DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        self.dbEscola = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])  
        self.dbSeries =  DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])


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
                try:
                    ids=self.dbEscola.acharDado("nome", dado["escola"])[-1]
                    if len(ids)==0:
                        if yesNoDialog(message="A escola com nome: "+str(aluno['escola']+" não está cadastrada, deseja cadastrar?")):
                            self.dbEscola.salvarDado({"nome": dado['escola']})
                    dado['escola']=ids
                except:
                    pass
                newDados.append(dado)
            db.salvarDados(newDados)   

        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
    
        self.calc = calcularAlunosThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()   
        self.loadingLabel.setText("Computando localização dos alunos")   
        self.calc.finished.connect(self.cleanProgress)         
        self.update()


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
                id=db.salvarDado(r)
                for s in r['series'].split(","): 
                   dbs.salvarDado(dbs.toDict([id,s,0,0]))            

        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1])

        self.calc = calcularEscolasThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()         
        self.calc.finished.connect(self.cleanProgress)       
        self.loadingLabel.setText("Computando localização das Escolas")      
        self.update()


    def cleanProgress(self):
        self.progressBar.setValue(0)
        self.loadingLabel.setText("")
        self.progressBar.hide()


    def buscarAluno(self):        
        self.idadeMinima = self.spinBoxIdadeMinima.value()
        self.idadeMaxima = self.spinBoxIdadeMaxima.value()
        self.listViewBusca.clear()
        busca = self.lineEditAluno.text()
        self.listaParaExportar=[]
        
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
        self.adicionarTodosCaminhos(aluno)
    

    def markerMovido(self, n, lat, long):
        if n=="Centro":
            self.updateCenter(lat, long)
        elif n=="aluno":
            id = self.buscaResultado[self.listViewBusca.currentRow()]['id']        
            v = Aluno("", "", "", "", "", "", "", "", "", 0, 0, 0, lat, long, id)
            v.salvarCoordenada()          
            self.listViewBusca.clear()
            self.buscarAluno()  
        elif n=="alunoNovo":
            v = Aluno("", "", "", "", "", "", "", "", "", 0, 0, 0, lat, long, self.alunoId)
            v.salvarCoordenada()           
            self.listViewBusca.clear()
            self.buscarAluno()              
        elif n=="escola":
            self.dbEscola.update(self.escolaId, {'lat':lat, 'long':long})        
        

    def adicionarSeries(self):
      
        self.listaDeSeriesPorEscola = []
        #mechi tbm na main.ui para essas mudanças...
        for i in self.listaDeEscolasSelecionadas:
            #for row in self.dbEscola.acharDado(ATRIBUTOS['escola'][5], self.listaDeEscolas[i]).split(SEPARADOR_SERIES):
                #self.listaDeSeriesPorEscola.append(row)
            #todasAsSeries = self.dbSeries.todosOsDados()
            #todasAsSeries = todasAsSeries['serie']
            #todasAsSeries = todasAsSeries.split(SEPARADOR_SERIES)
            #todasAsSeries = list(set(todasAsSeries)) 
            todasAsSeries = listaDeSeries
            for row in self.listaDeSeriesParaTeste[i].split(SEPARADOR_SERIES):
                self.listaDeSeriesPorEscola.append(row)
        self.listaDeSeriesPorEscola = list(set(self.listaDeSeriesPorEscola))
        listaDeSeries_add = []
        for ap in sorted(self.listaDeSeriesPorEscola, key=int):
            listaDeSeries_add.append(todasAsSeries[int(ap)])
        self.dropDownSeries = dropDown(listaDeSeries_add)
        self.layoutDropDown.setWidget(self.dropDownSeries)
   
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
 
    def saveConfig(self):  
        self.dialog[-1].db.update(self.dialog[-1].db.acharDado('nome', 'cidade')[0], {'string': self.dialog[-1].lineEdit_2.text()})   
        cfg=self.config.get()
        if not cfg.isApplied:      
            self.config.get().apply()
            self.config.save("config")
            self.mapWidget.hide()
            self.horizontalLayout_4.removeWidget(self.mapWidget)
            self.addMap()
            
    def modalidadesDialog(self):
        self.modalidades=self.varManager.read(ListaModalidades(),DB_MODALIDADES_BASE)    
        dialog=ModalidadesDialog(self)
        #dialog.setModal(True)
        dialog.accepted.connect(self.modalidades.save)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()

    def adicionarCaminho(self, aluno):
        self.mapWidget.clearPaths()
        f=confPath()/ Path(PASTA_ALUNOS) / Path(str(aluno['id']))  
        if f.is_dir():
            f=f/Path(aluno['escola'])
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
        self.dropDownEscolas.todos.setChecked(True)
        self.dropDownSeries.todos.setChecked(True)




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