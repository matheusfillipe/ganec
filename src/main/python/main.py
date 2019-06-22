''' GANEC = Gestor de Alunos Nas Escolas do Carmo '''

from PyQt5 import QtWidgets, QtGui, uic, Qt
from fbs_runtime.application_context import ApplicationContext
from lib.osm import MapWidget
from data.config import config

from lib.gmaps import QGoogleMap 
import sys

MAIN_WINDOW, _ = uic.loadUiType("./src/main/python/ui/mainWindow.ui")
MODALIDADES_DIALOD, _ = uic.loadUiType("./src/main/python/ui/dialogs/modalidades.ui")
NEW_MODALIDADE_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/modalidadeForm.ui")
SETTINGS_DIALOG,_ = uic.loadUiType("./src/main/python/ui/dialogs/settingsDialog.ui")
NEW_ALUNO_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/alunoForm.ui")
NEW_ESCOLA_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/escolaForm.ui")

class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    def __init__(self,iface):
        QtWidgets.QWidget.__init__(self)
        SETTINGS_DIALOG.__init__(self)
        self.setupUi(self)
        self.comboBox.addItem("Google")    
        self.comboBox.addItem("OSM")
        self.comboBox.currentIndexChanged.connect(self.updateconfig)
        self.aplicarBtn.clicked.connect(self.updateconfig)
        #load from db 
        self.tmpConfig=config()
        self.comboBox.setCurrentIndex(self.tmpConfig.map)

    def updateconfig(self):
        self.tmpConfig.map=self.comboBox.currentIndex()
        
#WIDGET ALUNO   
class NewAlunoWidget(QtWidgets.QWidget, NEW_ALUNO_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ALUNO_WIDGET.__init__(self)
        self.setupUi(iface)

#DIALOG ALUNO 
class NewAlunoDialog(QtWidgets.QDialog):
    def __init__(self, iface):
        super(NewAlunoDialog, self).__init__(None)
        self.iface=iface
        newAlunoWidget = NewAlunoWidget(self)
        newAlunoWidget.show()      

#WIDGET MODALIDADE     
class NewModalidadeWidget(QtWidgets.QWidget, NEW_MODALIDADE_WIDGET):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init__(self)
        self.setupUi(self)

#DIALOG MODALIDADE
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





if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win=MainWindow()
    win.showMaximized()        
    sys.exit(app.exec_())



