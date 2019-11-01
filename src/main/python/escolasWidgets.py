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

#cidade=Config.cidade()
cidade = "Carmo do Paranaiba"


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
        iface : MainWindow
        self.iface = iface
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
        iface : MainWindow
        self.iface = iface
        self.setupUi(self)

        #daqui para baixo modifiquei muitas coisas para tentar arrumar o de editar e excluiur as escolas.
        #################################################################################################

        self.label : QtWidgets.QLabel
        self.lineEditNomeEscola : QtWidgets.QLineEdit
        self.listViewEscolas : QtWidgets.QListWidget
        self.listViewSeries : QtWidgets.QListWidget
        self.pushButtonEditar : QtWidgets.QPushButton
        self.pushButtonExcluir : QtWidgets.QPushButton

        self.series = []
        self.widgets = []
        self.todasSeries=Escola.todasAsSeries()

        self.dbEscola = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])  
        self.dbSeries =  DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])

        for i in self.dbEscola.todosOsDados():
            self.listViewEscolas.addItem(i['nome'] + "\n\n")

        self.listViewEscolas.itemClicked.connect(self.setarEscola)
        self.pushButtonExcluir.clicked.connect(self.excluir)
        self.pushButtonEditar.clicked.connect(self.editar)

        self.comboBoxSeries.addItems([serie for serie in self.todasSeries if not (serie in self.series)])

        self.pushButtonAddSerie.clicked.connect(lambda: self.addTurma(self.comboBoxSeries.currentText()))
    
    #Funções de editar excluir e adicionar os widgets de aluinos;

    def addTurma(self, text):
        itemN = QtWidgets.QListWidgetItem() 
        widget = WidgetVagas(self)
        widget.labelSerie.setText(text)
        itemN.setSizeHint(widget.sizeHint())    
        self.listViewSeries.addItem(itemN)
        self.listViewSeries.setItemWidget(itemN, widget)
        widget.btnRemover.clicked.connect(lambda: self.series.remove(text))
        widget.btnRemover.clicked.connect(lambda: self.removeFromListWidget(itemN))
        self.series.append(text)
        self.widgets.append(widget)
        self.listViewSeries.scrollToBottom()

    def removeFromListWidget(self, item):
        i=self.listViewSeries.row(item)
        self.listViewSeries.takeItem(i)
        del self.widgets[i]

    def setarEscola(self, i):
        self.escolaEscolhida=self.dbEscola.acharDado('nome', self.listViewEscolas.currentItem().text().split("\n\n")[0])
        self.escolaEscolhida=self.dbEscola.getDados(self.escolaEscolhida)[0]
        self.lineEditNomeEscola.setText(self.escolaEscolhida['nome'])
        self.lineEditEndereco.setText(self.escolaEscolhida['endereco'])
        self.listViewSeries.clear()
        self.series = []
        seriesAdd = []
        series = self.escolaEscolhida['series'].split(SEPARADOR_SERIES)
        for i in series:
            if i not in seriesAdd:
                seriesAdd.append(i)
        seriesAdd.sort()
        for i in seriesAdd:
            self.addTurma(i)


    def editar(self):
        series = self.series[0]
        seriesAns = []
        j=0
        for i in self.series:
           if(j>=1):
               seriesAns.append(i)
           j+=1 

        for i in seriesAns:
            series += "," + i

        print(series)

        escola_ = Escola(self.lineEditNomeEscola.text(), self.lineEditEndereco.text(), "", "", series = series)
        deuCerto = escola_.editar(self.dbEscola.acharDado('nome', self.escolaEscolhida['nome'])[0])

        x,y=self.iface.centro()
        self.iface.mapWidget.addMarker("escola",x,y)
        self.limparTextos()
        self.listViewSeries.clear()
        self.series = []
        if deuCerto:
            messageDialog(self, "Editada", "", "Escola editada com sucesso!")
        else:
            messageDialog(self, "ERRO", "", "Favor posicione a escola manualmente")


    def excluir(self):
        excluir_ = yesNoDialog(self, "Atenção", "Tem certeza que deseja fazer isso?", "Todos os dados desse aluno serão removidos!")
        if excluir_ :
            self.dbEscola.apagarDado(self.dbEscola.acharDado('nome', self.lineEditNomeEscola.text())[0])
            self.limparTextos()    

        else :
            messageDialog(self, "Não excluido", "", "Ok, a Escola nao foi excluida")
        

    def limparTextos(self):
        self.lineEditNomeEscola.setText("")
        self.lineEditEndereco.setText("")
        self.listViewEscolas.clear()
        for i in self.dbEscola.todosOsDados():
            self.listViewEscolas.addItem(i['nome'] + "\n\n")


def test():
    app = QtWidgets.QApplication([]) 
    win=NewEscolaDialog()
    win.show()
    app.exec_()          

if __name__=="__main__":
    test()
