''' GANEC = Gestor de Alunos Nas Escolas do Carmo '''

from PyQt5.QtWidgets import QMainWindow
from fbs_runtime.application_context import ApplicationContext

import sys

if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    window = QMainWindow()
    window.resize(600, 500)
    window.show()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)