# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'escolaForm2.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from sqlitedb import create_db
class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.labelNome = QtWidgets.QLabel(Dialog)
        self.labelNome.setEnabled(True)
        self.labelNome.setGeometry(QtCore.QRect(10, 30, 47, 21))
        self.labelNome.setObjectName("labelNome")
        self.labelRua = QtWidgets.QLabel(Dialog)
        self.labelRua.setGeometry(QtCore.QRect(10, 70, 61, 21))
        self.labelRua.setObjectName("labelRua")
        self.labelBairro = QtWidgets.QLabel(Dialog)
        self.labelBairro.setGeometry(QtCore.QRect(10, 150, 47, 21))
        self.labelBairro.setObjectName("labelBairro")
        self.labelNumero = QtWidgets.QLabel(Dialog)
        self.labelNumero.setGeometry(QtCore.QRect(10, 100, 41, 41))
        self.labelNumero.setObjectName("labelNumero")
        self.lineEditNome = QtWidgets.QLineEdit(Dialog)
        self.lineEditNome.setGeometry(QtCore.QRect(80, 30, 311, 20))
        self.lineEditNome.setObjectName("lineEditNome")
        self.lineEditRua = QtWidgets.QLineEdit(Dialog)
        self.lineEditRua.setGeometry(QtCore.QRect(80, 70, 311, 20))
        self.lineEditRua.setObjectName("lineEditRua")
        self.lineEditNumero = QtWidgets.QLineEdit(Dialog)
        self.lineEditNumero.setGeometry(QtCore.QRect(80, 110, 311, 20))
        self.lineEditNumero.setObjectName("lineEditNumero")
        self.lineEditBairro = QtWidgets.QLineEdit(Dialog)
        self.lineEditBairro.setGeometry(QtCore.QRect(80, 150, 311, 20))
        self.lineEditBairro.setObjectName("lineEditBairro")
        self.labelModalidade = QtWidgets.QLabel(Dialog)
        self.labelModalidade.setGeometry(QtCore.QRect(10, 190, 61, 21))
        self.labelModalidade.setObjectName("labelModalidade")
        self.comboBoxModalidade = QtWidgets.QComboBox(Dialog)
        self.comboBoxModalidade.setGeometry(QtCore.QRect(80, 190, 311, 22))
        self.comboBoxModalidade.setObjectName("comboBoxModalidade")
        self.buttonOk = QtWidgets.QPushButton(Dialog)
        self.buttonOk.setGeometry(QtCore.QRect(220, 250, 75, 23))
        self.buttonOk.setObjectName("buttonOk")
        self.buttonCancelar = QtWidgets.QPushButton(Dialog)
        self.buttonCancelar.setGeometry(QtCore.QRect(300, 250, 75, 23))
        self.buttonCancelar.setObjectName("buttonCancelar")

        ###############################################################################################

        self.buttonOk.clicked.connect(lambda : create_db())
        

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.labelNome.setText(_translate("Dialog", "Nome:"))
        self.labelRua.setText(_translate("Dialog", "Rua:"))
        self.labelBairro.setText(_translate("Dialog", "Bairro:"))
        self.labelNumero.setText(_translate("Dialog", "Número:"))
        self.labelModalidade.setText(_translate("Dialog", "Modalidade:"))
        self.buttonOk.setText(_translate("Dialog", "OK"))
        self.buttonCancelar.setText(_translate("Dialog", "Cancelar"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

