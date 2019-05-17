''' GANEC = Gestor de Alunos Nas Escolas do Carmo '''

from PyQt5 import QtWidgets, uic
from fbs_runtime.application_context import ApplicationContext


import sys

if __name__ == '__main__':
    app = QtWidgets.QApplication([])        
    win = uic.loadUi("./src/main/python/ui/mainWindow.ui") #specify the location of your .ui file    
    win.show()    
    sys.exit(app.exec())

