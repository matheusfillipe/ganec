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

        iface.config.setup(self,
        signals=[self.lineEdit.textChanged, self.comboBox.currentIndexChanged, self.aplicarBtn.clicked, self.cleanDbButton.clicked],
        slots=[lambda: 0, lambda: 0, iface.saveConfig, self.reset],
        properties=["map", "text"],
        interface=[self.comboBox.currentIndex, self.lineEdit.text],
        writers=[self.comboBox.setCurrentIndex, self.lineEdit.setText])
        #TODO alert dialog on remove database and reset application
    
    def reset(self):
        self.iface.varManager.removeDatabase()
    
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
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        MAIN_WINDOW.__init__(self)
        self.varManager=VariableManager(os.path.dirname(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)))
        if RESET:
            self.varManager.removeDatabase()
        self.setupUi(self)
        self.actionModalidades.triggered.connect(self.modalidadesDialog)
        self.actionAlunos.triggered.connect(self.newAlunoDialog)    
        self.actionConfigura_es.triggered.connect(self.settingDialog)               
        self.config=self.varManager.read(Config(),"config")
        self.addMap()

    def addMap(self):
        if self.config.get().map==2:
            #TODO implement here maps
            w=QtWidgets.QLabel("Here Maps não está disponível, por favor mude para google ou osm nas configurações")
        elif self.config.get().map==1:
            w=MapWidget()
        elif self.config.get().map==0:
            w=QGoogleMap()
        else:
            w=QtWidgets.QLabel("Problema no banco de dados!")
        self.mapWidget=w
        self.horizontalLayout_4.addWidget(w)
        w.show()

    def settingDialog(self):
        dialog=SettingsDialog(self)
        dialog.accepted.connect(lambda: self.saveConfig(dialog))
        dialog.aplicarBtn.clicked.connect(lambda: self.saveConfig(dialog))
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
    
    def newAlunoDialog(self):
        dialog=NewAlunoDialog(self)             
        dialog.setModal(True)        
        dialog.exec_()

    def saveConfig(self, dialog):        
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
    app = QtWidgets.QApplication(sys.argv)
    win=MainWindow()
    win.showMaximized()        
    sys.exit(app.exec_())



