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


MAIN_WINDOW, _ = uic.loadUiType("./src/main/python/ui/mainWindow.ui")
MODALIDADES_DIALOD, _ = uic.loadUiType("./src/main/python/ui/dialogs/modalidades.ui")
NEW_MODALIDADE_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/modalidadeForm.ui")
SETTINGS_DIALOG,_ = uic.loadUiType("./src/main/python/ui/dialogs/settingsDialog.ui")
NEW_ALUNO_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/alunoForm.ui")

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
        properties=["map", "text", "text2"],
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

    
class NewAlunoDialog(QtWidgets.QDialog):
    def __init__(self, iface):
        super(NewAlunoDialog, self).__init__(None)
        self.iface=iface
        newAlunoWidget = NewAlunoWidget(self)
        newAlunoWidget.show()      


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
        self.lineEdit:QtWidgets.QLineEdit
        self.lineEdit.setPlaceholderText("Nome da Modalidade")

class NewTurmaWidget(QtWidgets.QWidget, NEW_MODALIDADE_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init__(self)
        self.setupUi(self)
        self.lineEdit:QtWidgets.QLineEdit
        self.lineEdit.setPlaceholderText("Turma/Série")

class ModalidadesDialog(QtWidgets.QDialog, MODALIDADES_DIALOD):
    edited = QtCore.pyqtSignal()
    def __init__(self, iface):
        QtWidgets.QDialog.__init__(self)
        MODALIDADES_DIALOD.__init__(self)
        self.setupUi(self)

        self.iface:MainWindow
        self.varManager:VariableManager
        self.listWidget:QtWidgets.QListWidget
        self.listWidget_2:QtWidgets.QListWidget
        self.modalidades:QInterface
        self.buttonBox:QtWidgets.QDialogButtonBox
        self.listaModalidades=[]        

        self.varManager:VariableManager = iface.varManager
        self.modalidades=self.varManager.read(ListaModalidades(),DB_MODALIDADES_BASE)    
        self.listWidget.itemClicked.connect(self.modalidadeChanged)
        self.modalidades.setup(self,
            signals =  [self.buttonBox.accepted],
            slots   =  [self.modalidades.save], 
            properties=["modalidades"], 
            readers  = [self.read],
            writers  = [self.write]
            )

    def read(self):
        return self.listaModalidades

    def write(self,modalidades:list):
        for m in modalidades:            
            self.addToListWidget1()
        
    def addToListWidget1(self):
        itemN = QtWidgets.QListWidgetItem() 
        widget = NewModalidadeWidget(self)
        widget.label.setText("Modalidade Escolar: ")
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())    

        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)
        
        i=self.listWidget.row(itemN)
        modalidade=self.modalidades.get()
        modalidade=modalidade.modalidades[i]
        modalidade=self.modalidades.getChild(modalidade)
        modalidade.setup(widget,
            signals =  [widget.lineEdit.textEdited],
            slots   =  [lambda: 0],
            properties=["nome"],
            readers  = [widget.lineEdit.text],
            writers  = [widget.lineEdit.setText]
            )
        self.listaModalidades.append(modalidade.get())

        widget.pushButton.clicked.connect(lambda: self.modalidades.get().append(Modalidade(nome="",turmas=[Turma(nome="")])))
        widget.pushButton.clicked.connect(modalidade.save)
        widget.pushButton.clicked.connect(self.addToListWidget1)
        widget.pushButton.clicked.connect(lambda: widget.pushButton.setText("Remover"))
        widget.pushButton.clicked.connect(lambda: self.setRemovableFromListWidget1(widget, itemN))
 
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

    def modalidadeChanged(self):
        item=self.listWidget.currentItem()
        self.listWidget_2.clear()  
        for t in self.modalidades.get().modalidades[self.listWidget.row(item)].turmas:
            self.addToListWidget2()
      
    def addToListWidget2(self):
        item=self.listWidget.currentItem()
        itemN = QtWidgets.QListWidgetItem() 
        widget = NewTurmaWidget(self)
        widget.label.setText("Turma: ")
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())    

        self.listWidget_2.addItem(itemN)
        self.listWidget_2.setItemWidget(itemN, widget)

        turma=self.modalidades.getChild(self.modalidades.get().modalidades[self.listWidget.row(item)].turmas[self.listWidget_2.row(itemN)])
        turma.setup(widget,
            signals =  [widget.lineEdit.textEdited],
            slots   =  [lambda: 0, ],
            properties=["nome"],
            readers  = [widget.lineEdit.text],
            writers  = [widget.lineEdit.setText]
            )
        widget.pushButton.clicked.connect(lambda: self.modalidades.get().get(self.listWidget.row(item)).addTurma(Turma(nome="")))
        widget.pushButton.clicked.connect(turma.save)
        widget.pushButton.clicked.connect(self.addToListWidget2)
        widget.pushButton.clicked.connect(lambda: widget.pushButton.setText("Remover"))
        widget.pushButton.clicked.connect(lambda: self.setRemovableFromListWidget2(widget, itemN))
 
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


class MainWindow(QtWidgets.QMainWindow, MAIN_WINDOW):
    def __init__(self, app):         
        QtWidgets.QMainWindow.__init__(self)
        MAIN_WINDOW.__init__(self)
        self.app : QtWidgets.QApplication
        self.app=app 
        self.varManager=VariableManager(os.path.dirname(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)))
        if RESET:
            self.varManager.removeDatabase()
            self.close()
        self.setupUi(self)
        self.actionSair.triggered.connect(self.close)
        self.actionModalidades.triggered.connect(self.modalidadesDialog)
        self.actionAlunos.triggered.connect(self.newAlunoDialog)    
        self.actionConfigura_es.triggered.connect(self.settingDialog)               
        self.config=self.varManager.read(Config(),DB_CONFIG)   
        self.config.modified.connect(lambda: self.config.customSlot("disclaim"))   
        self.config.notModified.connect(lambda: self.config.customSlot("apply"))  
        self.addMap()

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

    def settingDialog(self):
        dialog=SettingsDialog(self)
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
    
    def newAlunoDialog(self):
        dialog=NewAlunoDialog(self)             
        dialog.setModal(True)    
        dialog.show()    
        dialog.exec_()

    def saveConfig(self):  
        cfg=self.config.get()
        if not cfg.isApplied:      
            self.config.get().apply()
            self.config.save("config")
            self.mapWidget.hide()
            self.horizontalLayout_4.removeWidget(self.mapWidget)
            self.addMap()
            
    def modalidadesDialog(self):
        dialog=ModalidadesDialog(self)
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()


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



