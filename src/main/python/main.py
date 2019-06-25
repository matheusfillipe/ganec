''' GANEC = Gestor de Alunos Nas Escolas do Carmo '''

from PyQt5 import QtWidgets, QtGui, uic, Qt, QtCore
from fbs_runtime.application_context import ApplicationContext
from lib.osm import MapWidget
import os
from data.config import Config

from lib.gmaps import QGoogleMap 
import sys
from lib.database import VariableManager, QInterface


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
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init__(self)
        self.setupUi(self)


class MainWindow(QtWidgets.QMainWindow, MAIN_WINDOW):
    EXIT_CODE_REBOOT = 200

    def __init__(self): 
        QtWidgets.QMainWindow.__init__(self)
        MAIN_WINDOW.__init__(self)
        self.varManager=VariableManager(os.path.dirname(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)))
        if RESET:
            self.varManager.removeDatabase()
            self.close()
        self.setupUi(self)
        self.actionSair.triggered.connect(self.close)
        self.actionModalidades.triggered.connect(self.modalidadesDialog)
        self.actionAlunos.triggered.connect(self.newAlunoDialog)    
        self.actionConfigura_es.triggered.connect(self.settingDialog)               
        self.config=self.varManager.read(Config(),"config")   
        self.config.modified.connect(lambda: self.config.customSlot("disclaim"))   
        self.config.notModified.connect(lambda: self.config.customSlot("apply"))  
        self.addMap()

    def restartProgram(self):
        QtWidgets.qApp.exit(MainWindow.EXIT_CODE_REBOOT)

    def addMap(self):
        if self.config.get().map==2:
            #TODO implement here maps
            w=QtWidgets.QLabel("Here Maps não está disponível, por favor mude para google ou osm nas configurações")
        elif self.config.get().map==1:
            w=MapWidget()
        elif self.config.get().map==0:
            w=QGoogleMap()
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
        a=dialog.exec_()
        print(a)


class ModalidadesDialog(QtWidgets.QDialog, MODALIDADES_DIALOD):
    def __init__(self, iface):
        QtWidgets.QDialog.__init__(self)
        MODALIDADES_DIALOD.__init__(self)
        self.setupUi(self)

        #carregar da DB
        self.addToListWidget1()
        self.addToListWidget2()
        self.listWidget.itemClicked.connect(self.modalidadeChanged)


    def addToListWidget1(self):
        itemN = QtWidgets.QListWidgetItem() 
        widget = NewModalidadeWidget()
        widget.label.setText("Nome da Modalidade")
        widget.pushButton.clicked.connect(self.addToListWidget1)
        widget.pushButton.clicked.connect(lambda: widget.pushButton.setText("Remover"))
        widget.pushButton.clicked.connect(lambda: self.setRemovableFromListWidget1(widget, itemN))

        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())    
        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)

    def removeFromListWidget1(self, item):
        self.listWidget.takeItem(self.listWidget.row(item))   

    def setRemovableFromListWidget1(self, widget, itemN):
        while True:
            try: widget.pushButton.clicked.disconnect() 
            except Exception: break
        widget.lineEdit.setReadOnly(True)
        widget.pushButton.clicked.connect(lambda: self.removeFromListWidget1(itemN))

    def modalidadeChanged(self):
        #item=self.listWidget.currentItem()
        self.listWidget_2.clear()         
        self.addToListWidget2()
      
    def addToListWidget2(self):
        #load from DB
        itemN = QtWidgets.QListWidgetItem() 
        widget = NewModalidadeWidget()
        widget.label.setText("Nome da Turma")
        widget.pushButton.clicked.connect(self.addToListWidget2)
        widget.pushButton.clicked.connect(lambda: widget.pushButton.setText("Remover"))
        widget.pushButton.clicked.connect(lambda: self.setRemovableFromListWidget2(widget, itemN))

        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())    
        self.listWidget_2.addItem(itemN)
        self.listWidget_2.setItemWidget(itemN, widget)

    def removeFromListWidget2(self, item):
        return self.listWidget_2.takeItem(self.listWidget_2.row(item))   

    def setRemovableFromListWidget2(self, widget, itemN):
        while True:
            try: widget.pushButton.clicked.disconnect() 
            except Exception: break
        widget.lineEdit.setReadOnly(True)
        widget.pushButton.clicked.connect(lambda: self.removeFromListWidget2(itemN))




if __name__ == '__main__':

    currentExitCode = MainWindow.EXIT_CODE_REBOOT

    while currentExitCode == MainWindow.EXIT_CODE_REBOOT:
        app = QtWidgets.QApplication(sys.argv)
        win=MainWindow()
        win.showMaximized()        
        currentExitCode=app.exec_()
    
    sys.exit(currentExitCode)



