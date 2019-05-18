''' GANEC = Gestor de Alunos Nas Escolas do Carmo '''

from PyQt5 import QtWidgets, QtGui, uic
from fbs_runtime.application_context import ApplicationContext


import sys

MAIN_WINDOW, _ = uic.loadUiType("./src/main/python/ui/mainWindow.ui")
MODALIDADES_DIALOD, _ = uic.loadUiType("./src/main/python/ui/dialogs/modalidades.ui")
NEW_MODALIDADE_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/modalidadeForm.ui")

class NewModalidadeWidget(QtWidgets.QWidget, NEW_MODALIDADE_WIDGET):
    def __init(self):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init(self)
        self.setupUi(self)

class MainWindow(QtWidgets.QMainWindow, MAIN_WINDOW):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        MAIN_WINDOW.__init__(self)
        self.setupUi(self)
        self.actionModalidades.triggered.connect(self.modalidadesDialog)
    
    def modalidadesDialog(self):
        dialog=ModalidadesDialog(self)
        dialog.show()
        dialog.exec()

class ModalidadesDialog(QtWidgets.QDialog, MODALIDADES_DIALOD):
    def __init__(self, iface):
        QtWidgets.QDialog.__init__(self)
        MODALIDADES_DIALOD.__init__(self)
        self.setupUi(self)
        self.addToListWidget1()

    def addToListWidget1(self):
        itemN = QtWidgets.QListWidgetItem() 
        widget = NewModalidadeWidget()
        widget.pushButton.clicked.connect(self.addToListWidget1)
        widget.pushButton.clicked.connect(lambda: widget.pushButton.setText("Remover"))
        widget.pushButton.clicked.connect(lambda: widget.pushButton.clicked.connect(self.removeToListWidget1))
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())    
        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)

    def removeToListWidget1(self):
        pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win=MainWindow()
    win.show()    
    sys.exit(app.exec())



