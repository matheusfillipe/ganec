from PyQt5 import QtWidgets, QtGui, uic, Qt, QtCore
from PyQt5.QtCore import pyqtSignal
from lib.constants import *
from customWidgets import *
from sqlitedb import DB
from data.escola import *
from data.aluno import *
from data.config import *



NEW_ESCOLA_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/escolaForm.ui")
EDITAR_ESCOLA, _ = uic.loadUiType("./src/main/python/ui/widgets/escolaEditar.ui")
VAGAS_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/vagas.ui")


def messageDialog(iface=None, title="Concluído", info="", message=""):
    msgBox = QtWidgets.QMessageBox(iface)
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.setInformativeText(info)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
    msgBox.show()
    return msgBox.exec_() == QtWidgets.QMessageBox.Ok


def yesNoDialog(iface=None, title="Atenção", info="", message=""):
    msgBox = QtWidgets.QMessageBox(iface)
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.setInformativeText(info)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
    msgBox.show()
    return msgBox.exec_() == QtWidgets.QMessageBox.Yes


def confPath():
    path=QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.ConfigLocation)[0] / Path(NAME)
    path.mkdir(parents=True, exist_ok=True)  
    return path


class WidgetVagas(QtWidgets.QWidget, VAGAS_WIDGET):
    def __init__(self, iface):
        super(QtWidgets.QWidget, self).__init__(iface)
        self.setupUi(self)
        iface : MainWindow
        self.iface = iface        
        self.Form : QtWidgets.QWidget
        self.labelNumAlunos : QtWidgets.QLabel
        self.labelSerie : QtWidgets.QLabel
        self.labelVagas : QtWidgets.QLabel
        self.spinBoxNumAlunos : QtWidgets.QSpinBox
        self.spinBoxVagas : QtWidgets.QSpinBox
        self.verticalLayoutWidget : QtWidgets.QWidget
        self.btnRemover : QtWidgets.QPushButton
        self.spinBoxVagas.valueChanged.connect(self.spinBoxNumAlunos.setMaximum)
    
    def vagas(self):
        return self.spinBoxVagas.value()

    def alunos(self):
        return self.spinBoxNumAlunos.value()

 
class NewEscolaWidget(QtWidgets.QWidget, NEW_ESCOLA_WIDGET):
    def __init__(self, iface, parent, main=True):
        super(QtWidgets.QWidget, self).__init__(parent=parent)      
        self.setupUi(self)
        self.iface=iface
        self.lineEditNome : QtWidgets.QLineEdit
        self.lineEditRua : QtWidgets.QLineEdit
        self.lineEditNumero : QtWidgets.QLineEdit
        self.lineEditBairro : QtWidgets.QLineEdit
        self.buttonOk : QtWidgets.QPushButton
        self.pushButtonAdicionarSerie : QtWidgets.QPushButton
        self.buttonEditar : QtWidgets.QPushButton
        self.comboBoxSerie : QtWidgets.QComboBox
        self.listWidget : QtWidgets.QListWidget

        self.db=iface.dbEscola
        db=self.db
        self.series=[]
        self.widgets=[]
        self.todasSeries=Escola.todasAsSeries()
        self.comboBoxSerie.addItems([serie for serie in self.todasSeries if not (serie in self.series)])
        self.buttonOk.clicked.connect(self.salvarDadosEscola)
        self.pushButtonAdicionarSerie.clicked.connect(lambda: self.addTurma(self.comboBoxSerie.currentText()))

        if main:
            self.buttonEditar.clicked.connect(self.editarDialog)

    def editarDialog(self):
        d=editarEscolaDialog(self.iface)
        d.exec_()

    def addTurma(self, text):
        itemN = QtWidgets.QListWidgetItem() 
        widget = WidgetVagas(self)
        widget.labelSerie.setText(text)
        itemN.setSizeHint(widget.sizeHint())    
        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)
        widget.btnRemover.clicked.connect(lambda: self.series.remove(text))
        widget.btnRemover.clicked.connect(lambda: self.removeFromListWidget(itemN))
        self.series.append(text)
        self.widgets.append(widget)
        self.listWidget.scrollToBottom()

    def removeFromListWidget(self, item):
        i=self.listWidget.row(item)
        self.listWidget.takeItem(i)
        del self.widgets[i]

    def salvarDadosEscola(self):
        escola={}
        escola ["nome"]= self.lineEditNome.text() 
        rua = self.lineEditRua.text()
        numero = self.lineEditNumero.text()
        bairro = self.lineEditBairro.text()
        escola['series'] = SEPARADOR_SERIES.join(self.series)
        
        #confiro se todos os dados estão digitados    
        if (self.lineEditNome.text() != "") and (self.lineEditRua.text() != "") and (self.lineEditNumero.text() != "") and (self.lineEditBairro.text() != ""):
            a=Aluno()
            a.endereco = "Rua " + rua + ", " + numero + ", Bairro " + bairro + ", " + cidade
            escola['endereco']=rua + "," +  numero + ", " + bairro 
            cor=a.latLongAluno()
            escola['lat'], escola['long']=cor
            self.iface.escolaId=self.db.salvarDado(escola)            
            #TODO update series com vagas e alunos
            for s, w in zip(self.series, self.widgets):
                Turma.update(s,escola['nome'],{'vagas': w.spinBoxVagas.value(), 'nDeAlunos': w.spinBoxNumAlunos.value()})

            if cor:
                messageDialog(self, "Editado", "", "Por favor, confirme a posição da escola:")
                x,y=cor
            else:
                x,y=self.iface.centro()
                messageDialog(self, "ERRO", "", "Favor posicione a escola manualmente")    
                self.iface.mapWidget.centerAt(x,y)

            self.iface.mapWidget.addMarker("escola",x,y,
            **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
            draggable=True,
            title=escola['nome']
            ))     

            self.clear()
            self.listWidget.clear()
        else:
            messageDialog(self, "Atenção", "", "Todos os campos Obrigatórios devem estar preenchidos.")


    def setEscola(self, escola):
        self.lineEditNome.setText(escola['nome'])         
        self.lineEditRua.setText(escola['endereco'].split(",")[0])
        self.lineEditNumero.setText(escola['endereco'].split(",")[1])
        self.lineEditBairro.setText(escola['endereco'].split(",")[2:])
        [self.addTurma(turma) for turma in escola['series'].split(SEPARADOR_SERIES)]

    def clear(self):
        self.lineEditNome.setText("") 
        self.lineEditRua.setText("")
        self.lineEditNumero.setText("")
        self.lineEditBairro.setText("")


class NewEscolaDialog(QtWidgets.QDialog):
    def __init__(self, iface):
        super(QtWidgets.QDialog, self).__init__(None)  
        self.iface = iface
        self.iface=iface
        iface : MainWindow
        self.widget=NewEscolaWidget(iface, self)
        self.layout=QtWidgets.QGridLayout(self)
        self.setLayout(self.layout)
        self.layout.addWidget(self.widget)
        self.widget.buttonCancelar.clicked.connect(self.close)
        self.setWindowTitle("Nova Escola")

    def closeEvent(self, evnt):
        self.iface.mapWidget.deleteMarker("escola")
        super(NewEscolaDialog, self).closeEvent(evnt)
        

class editarEscolaDialog(QtWidgets.QDialog, EDITAR_ESCOLA):   
    def __init__(self, iface):
        super(QtWidgets.QDialog, self).__init__(None)
        self.setupUi(self)
        self.iface = iface
        self.iface=iface
        iface : MainWindow

        self.label : QtWidgets.QLabel
        self.lineEditNomeEscola : QtWidgets.QLineEdit
        self.listViewEscolas : QtWidgets.QListView
        self.pushButtonEditar : QtWidgets.QPushButton
        self.pushButtonExcluir : QtWidgets.QPushButton

        self.setupUi(self)
        self.gridLayout_2 : QtWidgets.QGridLayout
        self.widget=NewEscolaWidget(iface, self, False)
        self.widget.buttonOk.hide()
        self.widget.buttonCancelar.hide()
        self.widget.buttonEditar.hide()     

        self.gridLayout.addWidget(self.widget)
        self.lineEditNomeEscola.textChanged.connect(self.buscaEscolas)
        self.listViewEscolas.itemClicked.connect(self.setarEscola)
        self.pushButtonEditar.clicked.connect(self.editar)
        self.pushButtonExcluir.clicked.connect(self.excluir)


    def buscaEscolas(self):
        self.listViewEscolas.clear()
        escola = self.lineEditNomeEscola.text()
        if escola != "":
            listaDeIds = self.iface.dbEscola .acharDado('nome', escola)
            resultado = self.db.getDadosComId(listaDeIds)
        else:
            resultado = []
        self.resultado=resultado
        for i in resultado:
            strr = "Nome: " + i['nome'] + "  \nSeries: " + i['series']+"\n\n"
            self.lineEditNomeEscola.addItem(strr)


    def setarEscola(self, i):
        self.escola=self.resultado[i]
        self.widget.setEscola(self.escola) 


    def editar(self):
        if hasattr(self, "escola"):
            escola=self.escola
            #TODO verificar mudança de endereço e modificar lat long e salvar vagas e alunos
            self.iface.dbEscola.update(escola['id'], escola)
            x,y=self.iface.centro()
            self.iface.mapWidget.addMarker("escola",x,y)


    def excluir(self):
        if hasattr(self, "escola"):
            escola=self.escola
            self.iface.dbEscola.apagarDado(escola['id'])
            self.clear()


def test():
    app = QtWidgets.QApplication([]) 
    win=NewEscolaDialog()
    win.show()
    app.exec_()          

if __name__=="__main__":
    test()
