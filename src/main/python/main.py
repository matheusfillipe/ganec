''' GANEC = Gestor de Alunos Nas Escolas do Carmo '''

from PyQt5 import QtWidgets, QtGui, uic, Qt, QtCore
from fbs_runtime.application_context import ApplicationContext
import os, sys

from data.config import *
from data.aluno import *
from data.escola import *

from lib.osm import MapWidget
from lib.gmaps import QGoogleMap 
from lib.database import VariableManager, QInterface
from lib.constants import *
from customWidgets import *


MAIN_WINDOW, _ = uic.loadUiType(UI_FILES_PATH+"/mainWindow.ui")
MODALIDADES_DIALOD, _ = uic.loadUiType(UI_FILES_PATH+"/dialogs/modalidades.ui")
NEW_MODALIDADE_WIDGET, _ = uic.loadUiType(UI_FILES_PATH+"/widgets/modalidadeForm.ui")
SETTINGS_DIALOG,_ = uic.loadUiType(UI_FILES_PATH+"/dialogs/settingsDialog.ui")
NEW_ALUNO_WIDGET, _ = uic.loadUiType(UI_FILES_PATH+"/widgets/alunoForm.ui")
NEW_ESCOLA_WIDGET, _ = uic.loadUiType(UI_FILES_PATH+"/widgets/escolaForm.ui")

FILTER_WIDGET,_ = uic.loadUiType(UI_FILES_PATH+"/widgets/filtroForm.ui")

listaComOsDados = []
#Resetar banco de dados
RESET=0

def messageDialog(iface, title="Concluído", info="", message=""):
    msgBox = QtWidgets.QMessageBox(iface)
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.setInformativeText(info)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
    msgBox.show()
    return msgBox.exec_() == QtWidgets.QMessageBox.Ok


def yesNoDialog(iface, title="Atenção", info="", message=""):
    msgBox = QtWidgets.QMessageBox(iface)
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.setInformativeText(info)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
    msgBox.show()
    return msgBox.exec_() == QtWidgets.QMessageBox.Yes


class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    def __init__(self,iface):
        QtWidgets.QWidget.__init__(self)
        SETTINGS_DIALOG.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)
        self.comboBox.addItem("Google")    
        self.comboBox.addItem("OSM")

        self.comboBox.addItem("Here")
        self.comboBox.addItem("Arquivo")

        self.comboBox : QtWidgets.QComboBox 
        self.lineEdit : QtWidgets.QLineEdit
        self.lineEdit_2 : QtWidgets.QLineEdit
        self.buttonBox : QtWidgets.QDialogButtonBox

        iface.config.setup(self,
        signals=[self.buttonBox.accepted, self.lineEdit.textEdited, self.lineEdit_2.textEdited, self.comboBox.currentIndexChanged, self.aplicarBtn.clicked, self.cleanDbButton.clicked],
        slots=[iface.saveConfig,            lambda: 0,               lambda: 0,                  lambda: 0,                         iface.saveConfig,           self.reset],
        properties=["map",                  "text",               "text2"],
        readers=[self.comboBox.currentIndex, self.lineEdit.text, self.lineEdit_2.text],
        writers=[self.comboBox.setCurrentIndex, self.lineEdit.setText, self.lineEdit_2.setText])
                   
    def reset(self):        
        reply = yesNoDialog(iface=self, message="Tem certeza que deseja remover todos os dados cadastrados?", 
        info="Esta operação irá remover todos os arquivos de configuração e de banco de dados. Isso não é reversível.")
        if reply:
            self.iface.varManager.removeDatabase()
            messageDialog(self, message="O programa irá reiniciar")
            self.close()
            self.iface.restartProgram()                


class FilterWidget(QtWidgets.QWidget, FILTER_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        FILTER_WIDGET.__init__(self)
        self.setupUi(iface)
        self.Form : QtWidgets.QWidget
        self.comboBox : QtWidgets.QComboBox
        self.comboBox_2 : QtWidgets.QComboBox 
        self.lineEdit : QtWidgets.QLineEdit
        self.pushButton : QtWidgets.QPushButton        

class NewAlunoDialog(QtWidgets.QDialog, NEW_ALUNO_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ALUNO_WIDGET.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)

        self.aluno = self.iface.aluno

        self.lineEditNome : QtWidgets.QLineEdit
        self.lineEditRG : QtWidgets.QLineEdit
        self.lineEditCPF : QtWidgets.QLineEdit
        self.lineEditNomeDaMae : QtWidgets.QLineEdit
        self.lineEditNomeDoPai : QtWidgets.QLineEdit
        self.lineEditTelefone : QtWidgets.QLineEdit
        self.lineEditRua : QtWidgets.QLineEdit
        self.lineEditNumero : QtWidgets.QLineEdit
        self.lineEditBairro : QtWidgets.QLineEdit
        self.lineEditComplemento : QtWidgets.QLineEdit
        self.lineEditMatricula : QtWidgets.QLineEdit
        
        self.comboBoxEscolas : QtWidgets.QComboBox
        self.comboBoxSerie : QtWidgets.QComboBox

        for i in listaDeEscolas:
            self.comboBoxEscolas.addItem(i)
        for i in listaDeSeries[0]:
            self.comboBoxSerie.addItem(i)

        iface.aluno.setup(self,
        signals=[self.pushButtonAdiconar.clicked, self.lineEditNome.textEdited, self.lineEditRG.textEdited, self.lineEditCPF.textEdited, self.lineEditNomeDaMae.textEdited, self.lineEditNomeDoPai.textEdited, self.lineEditTelefone.textEdited, self.lineEditRua.textEdited, self.lineEditNumero.textEdited, self.lineEditBairro.textEdited, self.lineEditComplemento.textEdited, self.lineEditMatricula.textEdited, self.comboBoxEscolas.currentIndexChanged, self.comboBoxSerie.currentIndexChanged],
        slots=[  iface.saveAluno,                 lambda: 0,                    lambda: 0,              lambda: 0,               lambda: 0,                     lambda: 0,                     lambda: 0,                    lambda: 0,               lambda: 0,                  lambda: 0,                  lambda: 0,                       lambda: 0,                     lambda: 0,                                lambda: 0],
        properties=["name",                    "RG",                    "CPF",                    "nomeMae",                      "nomePai",                      "telefone",                    "rua",                    "numero",                    "bairro",                    "complemento",                    "matricula"],
        readers =  [self.lineEditNome.text,    self.lineEditRG.text,    self.lineEditCPF.text,    self.lineEditNomeDaMae.text,    self.lineEditNomeDoPai.text,    self.lineEditTelefone.text,    self.lineEditRua.text,    self.lineEditNumero.text,    self.lineEditBairro.text,    self.lineEditComplemento.text,    self.lineEditMatricula.text],
        writers =  [self.lineEditNome.setText, self.lineEditRG.setText, self.lineEditCPF.setText, self.lineEditNomeDaMae.setText, self.lineEditNomeDoPai.setText, self.lineEditTelefone.setText, self.lineEditRua.setText, self.lineEditNumero.setText, self.lineEditBairro.setText, self.lineEditComplemento.setText, self.lineEditMatricula.setText])
        
        self.pushButtonAdiconar.clicked.connect(self.salvarDados)
        self.comboBoxEscolas.currentIndexChanged.connect(self.addSeries)

    def salvarDados(self):
        erro = 0

        if (self.lineEditNome.text() != "") and (self.lineEditRG.text() != "") and (self.lineEditCPF.text() != "") and (self.lineEditRua.text() != "") and (self.lineEditNumero.text() != "") and (self.lineEditBairro.text() != "") and (self.lineEditMatricula.text() != ""):
            endereco = [self.Aluno.rua, self.Aluno.numero, self.Aluno.bairro, self.Aluno.complemento]
            dados = "Matrícula: " + self.Aluno.matricula + "\n\nNome: " + self.Aluno.nome + "\nRG: " + self.Aluno.RG + "\nCPF: " + self.Aluno.CPF + "\nMãe: " + self.Aluno.nomeDaMae + "\nPai: " + self.Aluno.nomeDoPai +  "\nTelefone: " + self.Aluno.telefone + "\nEndereço:\n\nRua: " + endereco[0] + ", " + endereco[1] + "\nBairro: " + endereco[2]
            if endereco[3] != "":
                dados = dados + "\nComplemento: " + endereco[3]
            listaComOsDados.append(dados)
            model = QtGui.QStandardItemModel()
            self.listViewAlunos.setModel(model)
            for i in listaComOsDados:
                item = QtGui.QStandardItem(i)
                model.appendRow(item)
            erro = 1
        if erro == 0:
            #printar erro que todos os campos obrigatórios devem ser preenchidos 
            print("Erro")                    
 
    def addSeries(self):
        self.comboBoxSerie.clear()
        for i in listaDeSeries[self.comboBoxEscolas.currentIndex()]:
            self.comboBoxSerie.addItem(i)  
 
class NewAlunoWidget(QtWidgets.QWidget, NEW_ALUNO_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ALUNO_WIDGET.__init__(self)
        self.setupUi(iface)   


class NewModalidadeWidget(QtWidgets.QWidget, NEW_MODALIDADE_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init__(self)
        self.setupUi(self)        
        self.widget : QtWidgets.QWidget
        self.widget : QtWidgets.QWidget
        self.label : QtWidgets.QLabel
        self.lineEdit : QtWidgets.QLineEdit
        self.pushButton : QtWidgets.QPushButton
        self.lineEdit.setPlaceholderText("Nome da Modalidade")


class NewTurmaWidget(QtWidgets.QWidget, NEW_MODALIDADE_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init__(self)
        self.setupUi(self)
        self.widget : QtWidgets.QWidget
        self.widget : QtWidgets.QWidget
        self.label : QtWidgets.QLabel
        self.lineEdit : QtWidgets.QLineEdit
        self.pushButton : QtWidgets.QPushButton
        
        self.lineEdit.setPlaceholderText("Turma/Série")


class ModalidadesDialog(QtWidgets.QDialog, MODALIDADES_DIALOD):
    edited = QtCore.pyqtSignal()
    def __init__(self, iface):
        QtWidgets.QDialog.__init__(self)
        MODALIDADES_DIALOD.__init__(self)
        self.setupUi(self)

        self.iface:MainWindow
        self.varManager:VariableManager
        self.modalidades:QInterface
        self.Dialog : QtWidgets.QDialog
        self.listWidget : QtWidgets.QListWidget
        self.listWidget_2 : QtWidgets.QListWidget
        self.buttonBox : QtWidgets.QDialogButtonBox

        self.iface=iface
        self.varManager:VariableManager = iface.varManager
        self.modalidades=self.iface.modalidades    
        self.listWidget.itemClicked.connect(self.modalidadeChanged)

        self.modalidades.setup(self,
            signals =  [],
            slots   =  [], 
            properties=["modalidades"], 
            readers  = [self.read],
            writers  = [self.write]
        )

    def read(self):
        return []

    def write(self,modalidades:list):
        for i,m in enumerate(modalidades):   
            self.addToListWidget1(m, removable=True if i<len(modalidades)-1 else False)
        
    def addToListWidget1(self, modalidade:Modalidade, removable=False):

        itemN = QtWidgets.QListWidgetItem() 
        widget = NewModalidadeWidget(self)
        widget.label.setText("Modalidade Escolar: ")        
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())  
        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)

        i=self.listWidget.row(itemN)
        widget.lineEdit.setText(modalidade.nome)                
        widget.pushButton.clicked.connect(lambda: self.addToListWidget1(Modalidade()))
        widget.pushButton.clicked.connect(lambda: self.setRemovableFromListWidget1(widget, itemN))        

        if removable:
            self.setRemovableFromListWidget1(widget, itemN)


    def removeFromListWidget1(self, item):
        i=self.listWidget.row(item)
        self.listWidget.takeItem(i)
        self.modalidades.get().removeByIndex(i)

    def setRemovableFromListWidget1(self, widget, itemN):
        while True:
            try: widget.pushButton.clicked.disconnect() 
            except Exception: break
        widget.lineEdit.setReadOnly(True)
        widget.pushButton.clicked.connect(lambda: self.removeFromListWidget1(itemN))
        widget.pushButton.setText("Remover")

    def modalidadeChanged(self):
        item=self.listWidget.currentItem()
        self.listWidget_2.clear()  
        lista=self.modalidades.get().modalidades[self.listWidget.row(item)].turmas
        for i,t in enumerate(lista):
            self.addToListWidget2(t,removable=True if i < len(lista)-1 else False)

    def addToListWidget2(self, turma:Turma, removable=False):        
        item=self.listWidget.currentItem()
        itemN = QtWidgets.QListWidgetItem() 
        widget = NewTurmaWidget(self)
        widget.label.setText("Turma: ")
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())    

        self.listWidget_2.addItem(itemN)
        self.listWidget_2.setItemWidget(itemN, widget)
        widget.pushButton.clicked.connect(lambda: self.addToListWidget2(Turma()))
        widget.pushButton.clicked.connect(lambda: self.setRemovableFromListWidget2(widget, itemN))

        if removable:
            self.setRemovableFromListWidget2(widget, itemN)

    def removeFromListWidget2(self, item):
        i=self.listWidget_2.row(item)
        item=self.listWidget.currentItem()       
        self.listWidget_2.takeItem(i)   
        self.modalidades.get().modalidades[self.listWidget.row(item)]
        

    def setRemovableFromListWidget2(self, widget, itemN):
        while True:
            try: widget.pushButton.clicked.disconnect() 
            except Exception: break
        widget.lineEdit.setReadOnly(True)
        widget.pushButton.clicked.connect(lambda: self.removeFromListWidget2(itemN))
        widget.pushButton.setText("Remover")

class NewEscolaDialog(QtWidgets.QDialog, NEW_ESCOLA_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ESCOLA_WIDGET.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)


class MainWindow(QtWidgets.QMainWindow, MAIN_WINDOW):
    def __init__(self, app):         
        QtWidgets.QMainWindow.__init__(self)
        MAIN_WINDOW.__init__(self)
        self.app : QtWidgets.QApplication
        self.filterVLayout : QtWidgets.QVBoxLayout
        self.MainWindow : QtWidgets.QMainWindow
        self.centralwidget : QtWidgets.QWidget
        self.leftPart : QtWidgets.QWidget
        self.comboBox : QtWidgets.QComboBox
        self.comboBox_2 : QtWidgets.QComboBox
        self.comboBox_3 : QtWidgets.QComboBox
        self.addFilterButton : QtWidgets.QPushButton
        self.searchLine : QtWidgets.QLineEdit
        self.searchButton : QtWidgets.QPushButton
        self.listWidget_2 : QtWidgets.QListWidget
        self.menubar : QtWidgets.QMenuBar
        self.menuArquivo : QtWidgets.QMenu
        self.menuCadastrar : QtWidgets.QMenu
        self.menuExibir : QtWidgets.QMenu
        self.menuMapas : QtWidgets.QMenu
        self.menuOp_es : QtWidgets.QMenu
        self.statusbar : QtWidgets.QStatusBar
        self.scrollLayout : QtWidgets.QFormLayout

        self.app=app 
        self.varManager=VariableManager(os.path.dirname(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)))
        if RESET:
            self.varManager.removeDatabase()
            self.close()
            self.app.quit()
        self.setupUi(self)
        self.actionSair.triggered.connect(self.close)
        self.actionModalidades.triggered.connect(self.modalidadesDialog)
        self.actionAlunos.triggered.connect(self.newAlunoDialog)    
        self.actionConfigura_es.triggered.connect(self.settingDialog)               
        self.actionEscolas.triggered.connect(self.newEscolaDialog)
        self.config=self.varManager.read(Config(),DB_CONFIG)   
        self.config.modified.connect(lambda: self.config.customSlot("disclaim"))   
        self.config.notModified.connect(lambda: self.config.customSlot("apply"))  
        self.addMap()

        self.comboBox.addItems(UI_FILTER1)
        self.comboBox.currentIndexChanged.connect(self.setComboBox_2)
        self.comboBox_3.addItems(UI_ORDEM)
        self.searchLine.editingFinished.connect(self.search)  
        self.setComboBox_2()     
        self.addFilterButton.clicked.connect(self.addFilter)

        self.filterWidgets=[]
        
      #  # scroll area widget contents
      #  self.scrollWidget = QtWidgets.QWidget()
      #  self.scrollWidget.setLayout(self.scrollLayout)

      #  # scroll area
      #  self.scrollArea = QtWidgets.QScrollArea()
      #  self.scrollArea.setWidgetResizable(True)
      #  self.scrollArea.setWidget(self.scrollWidget)


    def addFilter(self):
        w=FilterWidget(self)
        self.scrollLayout.addRow(w)
        self.filterWidgets.append(w)        
        w.pushButton.clicked.connect(lambda: self.removeFilter(len(self.filterWidgets)-1))
        w.pushButton.clicked.connect(w.deleteLater)

    def removeFilter(self, i):
        for j in range(i,len(self.filterWidgets)):
            self.filterVLayout.removeWidget(self.filterWidgets[j])
            self.filterWidgets[j].deleteLater()
            del self.filterWidgets[j]
        
    def setComboBox_2(self):
        self.comboBox_2.clear()
        if self.comboBox.currentIndex()==0:
            self.comboBox_2.addItems(UI_FILTER2_ALUNO)
        elif self.comboBox.currentIndex()==1:
            self.comboBox_2.addItems(UI_FILTER2_ESCOLA)   

    def search(self):
        ordem=self.comboBox_3.currentIndex()
        busca=self.searchLine.text()
        n=self.comboBox_2.currentIndex()
        w=QtWaitingSpinner(self.listWidget_2)


        if self.comboBox.currentIndex()==0:  #Aluno
            if n==1: #Buscar aluno google maps
                self.listWidget_2.clear()
                print("Searching location")
                lat, lng=self.mapWidget.centerAtAddress(busca)     
                self.mapWidget.addMarker("novoAluno", lat, lng, **dict(
                icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_blue.png",
                draggable=True,
                title="Novo Aluno"
                 ))     
                print("search finished!!!!!!!!!!!!!")

                w.stop()
                itemN = QtWidgets.QListWidgetItem() 
                widget = QtWidgets.QPushButton("Adicionar Novo aluno nessa posição")
                itemN.setSizeHint(widget.sizeHint())                                  
                self.listWidget_2.addItem(itemN)
                self.listWidget_2.setItemWidget(itemN, widget)
                
                itemN2 = QtWidgets.QListWidgetItem()                
                label = QtWidgets.QLabel("Sem resultados")
                itemN2.setSizeHint(widget.sizeHint())                                  
                self.listWidget_2.addItem(itemN2)
                self.listWidget_2.setItemWidget(itemN2, label) 

                widget.clicked.connect(self.newAlunoDialog)
                widget.clicked.connect(self.listWidget_2.clear)

        else: #Escola
            pass     
        QTimer.singleShot(500,w.stop)
      
    
    def saveAluno(self):
        self.aluno.save(DB_ADD_ALUNO)
 
    def restartProgram(self):
        self.app.restart=True
        self.close()
        self.app.quit()
    
    def updateCenter(self, key, lat, lng):
        if key=="Centro":
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
            w.markerMoved.connect(self.updateCenter)
        else:
            w=QtWidgets.QLabel("Problema no banco de dados! Tente limpar as configurações")
        self.mapWidget=w
        self.horizontalLayout_4.addWidget(w)
        w.show()

    def newAlunoDialog(self): 
        self.aluno=self.varManager.read(Aluno(), DB_ADD_ALUNO) 
        dialog=NewAlunoDialog(self)             
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()

    def newEscolaDialog(self):  
        dialog=NewEscolaDialog(self)             
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()

    def settingDialog(self):
        dialog=SettingsDialog(self)
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
 
    def saveConfig(self):  
        cfg=self.config.get()
        if not cfg.isApplied:      
            self.config.get().apply()
            self.config.save(DB_CONFIG)
            self.mapWidget.hide()
            self.horizontalLayout_4.removeWidget(self.mapWidget)
            self.addMap()
            
    def modalidadesDialog(self):
        self.modalidades=self.varManager.read(ListaModalidades(),DB_MODALIDADES_BASE)    
        dialog=ModalidadesDialog(self)
        dialog.setModal(True)
        dialog.accepted.connect(self.modalidades.save)
        dialog.show()
        dialog.exec_()

#WIDGET ESCOLA
class NewEscolaWidget(QtWidgets.QWidget, NEW_ESCOLA_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ESCOLA_WIDGET.__init(self)
        self.setupUi(iface)

#DIALOG ESCOLA
class NewEscolaDialog(QtWidgets.QDialog):
    def __init__(self, iface):
        super(NewEscolaDialog, self).__init__(None)
        self.iface=iface
        newEscolaWidget = NewEscolaWidget(self)
        newEscolaWidget.show()

class MainWindow(QtWidgets.QMainWindow, MAIN_WINDOW):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        MAIN_WINDOW.__init__(self)
        self.setupUi(self)
        self.actionModalidades.triggered.connect(self.modalidadesDialog)
        self.actionAlunos.triggered.connect(self.newAlunoDialog) 
        self.actionConfigura_es.triggered.connect(self.settingDialog)
        self.actionEscolas.triggered.connect(self.NewEscolaDialog)    
        #w=MapWidget()
        w=QGoogleMap()
        #self.stackedWidget.setCurrentWidget(w)
        self.horizontalLayout_4.addWidget(w)
        w.show()

    def settingDialog(self):
        dialog=SettingsDialog(self)
        dialog.accepted.connect(lambda: self.saveConfig(dialog))
        dialog.aplicarBtn.clicked.connect(lambda: self.saveConfig(dialog))
        dialog.aplicarBtn.clicked.connect(self.loadConfig)
       
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
    
    def newAlunoDialog(self):
        dialog=NewAlunoDialog(self)             
        dialog.setModal(True)
        
        dialog.exec_()

    def saveConfig(self, dialog):
        print("config: "+str(dialog.tmpConfig.map))

    def loadConfig(self):
        print("Load from db")
    
    def modalidadesDialog(self):
        dialog=ModalidadesDialog(self)
        dialog.setModal(True)
        dialog.show()
        a=dialog.exec_()
        print(a)




def main(*args):
    while True:
        app = QtWidgets.QApplication(*args)
        app.restart=False
        win=MainWindow(app)
        win.showMaximized()        
        currentExitCode=app.exec_()
        if not app.restart:
            break        
    return currentExitCode   

if __name__ == '__main__':
    currentExitCode=main(sys.argv)
    sys.exit(currentExitCode)



