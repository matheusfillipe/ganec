from PyQt5 import QtWidgets, QtGui, uic, Qt, QtCore
from PyQt5.QtCore import pyqtSignal
from lib.constants import *
from customWidgets import *
from sqlitedb import DB
from data.aluno import *
from data.escola import *


NEW_ALUNO_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/alunoForm.ui")
EDITAR_ALUNO, _ = uic.loadUiType("./src/main/python/ui/widgets/editarOuExcluir.ui")
ALUNO_BUSCA, _ = uic.loadUiType("./src/main/python/ui/widgets/alunoBusca.ui")

from data.config import *
cidade=Config.cidade()

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


class alunoBusca(QtWidgets.QDialog, ALUNO_BUSCA):
    def __init__(self, parent, aluno):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)        
        self.Form : QtWidgets.QWidget
        self.label : QtWidgets.QLabel
        self.parent=parent
        self.aluno=aluno
        self.pushButton : QtWidgets.QPushButton
        self.pushButton.clicked.connect(lambda : editarAlunoDialog(parent, aluno['id']).exec_())
        self.label.setText("Nome: " + aluno['nome'] + "\nMãe: " + aluno['nomeDaMae'] + "\nPai: " + aluno['nomeDoPai'] + "\nMatrícula: "+aluno['matricula'])

    def mouseDoubleClickEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            editarAlunoDialog(self.parent, self.aluno['id']).exec_()
        return super().mouseDoubleClickEvent(QMouseEvent)

class NewAlunoDialog(QtWidgets.QDialog, NEW_ALUNO_WIDGET):

    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ALUNO_WIDGET.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)
        self.aluno = self.iface.aluno

        self.lineEditNome : QtWidgets.QLineEdit
        self.lineEditRG : QtWidgets.QLineEdit
        self.lineEditCPF : QtWidgets.QLineEdit
        self.lineEditNomeDaMae : QtWidgets.QLineEdit
        self.lineEditNomeDoPai : QtWidgets.QLineEdit
        self.lineEditTelefone : QtWidgets.QLineEdit
        self.lineEditRua : QtWidgets.QLineEdit
        self.lineEditNumero : QtWidgets.QLineEdit
        self.lineEditBairro : QtWidgets.QLineEdit
        self.lineEditComplemento : QtWidgets.QLineEdit
        self.lineEditMatricula : QtWidgets.QLineEdit        
        self.comboBoxSerie : QtWidgets.QComboBox
        self.comboBoxSerie.addItems(Escola.todasAsSeries())        
        self.pushButtonAdiconar.clicked.connect(self.salvarDados)
        self.toolButtonEditarAlunos.clicked.connect(self.editarAluno)
      

    def salvarDados(self):
        self.iface.mapWidget.deleteMarker("alunoNovo")
        erro = 0

        #peguei cada dado digitado na minha UI e aloquei em variaveis para transformalas numa string e numa lista com todos esses dados
        nome = self.lineEditNome.text() 
        nomeDaMae = self.lineEditNomeDaMae.text()
        nomeDoPai = self.lineEditNomeDoPai.text()
        RG = self.lineEditRG.text()
        CPF = self.lineEditCPF.text()
        rua =self.lineEditRua.text()
        numero = self.lineEditNumero.text()
        bairro = self.lineEditBairro.text()
        complemento = self.lineEditComplemento.text()
        matricula = self.lineEditMatricula.text()
        telefone = self.lineEditTelefone.text()
        dataNasc = self.dateEditNascimento.date().toString()
        serie = self.comboBoxSerie.currentText()

        #confiro se todos os dados estão digitados    
        if (self.lineEditNome.text() != "") and (self.lineEditRua.text() != "") and (self.lineEditNumero.text() != "") and (self.lineEditBairro.text() != ""):
            
            endereco = [rua, numero, bairro, complemento]
            endereco_ = "Rua " + rua + " " + numero + ", Bairro " + bairro
            
            #monto uma string com os dados para ser utilizada em outras aplicações 
            stringDados = "Matrícula: " + matricula + "\n\nNome: " + nome + "\nRG: " + RG + "\nCPF: " + CPF + "\nMãe: " + nomeDaMae + "\nPai: " + nomeDoPai + "\nTelefone: " + telefone + "\nEndereço:\n\nRua: " + endereco[0] + ", " + endereco[1] + "\nBairro: " + endereco[2]

            if endereco[3] != "":
                stringDados = stringDados + "\nComplemento: " + endereco[3]
                endereco_ = endereco_ + ", Complemento " + complemento
            
            endereco_ = endereco_ + ", " + cidade

            aluno = Aluno(nome, matricula, dataNasc, RG, CPF, nomeDaMae, nomeDoPai, telefone, endereco_, serie)
            coordenada = aluno.salvar()
            
            erro = 1
            deuCerto=coordenada[0]

            if deuCerto != 0:
                messageDialog(self, "Editado", "", "Aluno encontrado com sucesso!\n\nMas confira na pagina inicial se o local está correto")
            else:            
                messageDialog(self, "ERRO", "", "Favor ir na pagina inicial e mover o marcador de endereço manualmente")
                self.iface.alunoId=aluno.id
                self.iface.mapWidget.centerAt(self.iface.config.get().lat, self.iface.config.get().lng)
                self.iface.mapWidget.addMarker("alunoNovo",self.iface.config.get().lat,self.iface.get().lng,
                **dict(
                icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
                draggable=True,
                title=aluno.nome
                ))
            
                
            nome = self.lineEditNome.setText("") 
            nomeDaMae = self.lineEditNomeDaMae.setText("")
            nomeDoPai = self.lineEditNomeDoPai.setText("")
            RG = self.lineEditRG.setText("")
            CPF = self.lineEditCPF.setText("")
            rua =self.lineEditRua.setText("")
            numero = self.lineEditNumero.setText("")
            bairro = self.lineEditBairro.setText("")
            complemento = self.lineEditComplemento.setText("")
            matricula = self.lineEditMatricula.setText("")
            telefone = self.lineEditTelefone.setText("")

        if erro == 0:
            messageDialog(self, "Atenção", "", "Todos os campos Obrigatórios devem estar preenchidos.")

         
    def editarAluno(self):
        dialog=editarAlunoDialog(self.iface)             
        #dialog.setModal(True)
        dialog.show()
        self.iface.dialog.append(dialog)
        dialog.exec_()

    def closeEvent(self, QCloseEvent):
        self.iface.mapWidget.deleteMarker("alunoNovo") 
        return super().closeEvent(QCloseEvent)



class editarAlunoDialog(QtWidgets.QDialog, EDITAR_ALUNO):   

    def __init__(self, iface, alunoId=None):
        QtWidgets.QWidget.__init__(self)       
        self.alunoId=None
        self.setupUi(self)
        self.iface=iface
        self.db = DB(str(confPath() /Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        #quando apertar para editar algum aluno
        self.pushButtonEditar.clicked.connect(self.editar)
        #quando apertar para excluir algum aluno
        self.pushButtonExcluir.clicked.connect(self.excluir)
        #quando escolher algum item da lista
        self.listViewAlunos.itemClicked.connect(lambda: self.setarAluno(None))
        todasEscolas=Escola.todasAsEscolas()
        if len(todasEscolas)==0:
            self.invalid=True
            return
        self.comboBoxEscola: QtWidgets.QComboBox

        self.comboBoxEscola.addItems(todasEscolas)
        self.comboBoxEscola.currentTextChanged.connect(self.comboBoxSerie.clear)
        self.comboBoxEscola.currentTextChanged.connect(lambda text: self.comboBoxSerie.addItems(iface.dbEscola.acharDados('nome', text)[-1]['series'].split(SEPARADOR_SERIES)))
        self.comboBoxEscola.currentTextChanged.emit(todasEscolas[0])
        #quando pesquisar um nome
        self.lineEditBuscarAlunos.textChanged.connect(self.buscarOsAlunos)
        self.labelId.hide()
        if not alunoId is None:
            self.setarAluno(alunoId)


    def show(self):
        if hasattr(self, "invalid"):
            messageDialog(title="ERRO", message="Você deve cadastrar as escolas!")
        return super().show()

    def exec_(self):
        if hasattr(self, "invalid"):
                messageDialog(title="ERRO", message="Você deve cadastrar as escolas!")
        return super().exec_()

       


    def buscarOsAlunos(self):
        self.listViewAlunos.clear()
        row = 0
        alunos = self.lineEditBuscarAlunos.text()
        if alunos != "":
            listaDeIds = self.db.acharDado(ATRIBUTOS['aluno'][0], alunos)
            resultado = self.db.getDadosComId(listaDeIds)
        else:
            resultado = []
        self.resultado=resultado
        for i in resultado:
            nasc = i['dataNasc'].split()
            if len(nasc) >= 3:
                nascimento = nasc[2] + "/" + nasc[1] + "/" + nasc[3]
            else:
                nascimento = nasc[0]
            strr = "Nome: " + i['nome'] + "  - Matrícula: " + i['matricula'] + "\n" + self.comboBoxSerie.currentText() + "\nData de Nascimento: " + nascimento + "\nRG: " + i['RG'] + "  - CPF: " + i['CPF'] + "\nMãe: " + i['nomeDaMae'] + "  - Pai: " + i['nomeDoPai'] + "\nTelefone: " + i['telefone'] + "\nEndereço: " + i['endereco'] + "\nEscola: " +  str(i['escola'])  + "\n\n"
            self.listViewAlunos.addItem(strr)
            row = row + 1

    def setarAluno(self, id=None):
        if id is None:
            self.listViewAlunos : QtWidgets.QListWidget
            id = self.listViewAlunos.currentRow()
            id = self.resultado[id]["id"]
            self.id=id
            aluno = self.iface.dbAluno.getDado(id)
        else:
            aluno=self.iface.dbAluno.getDado(id)
            self.id=id
            try:
                self.comboBoxEscola.setCurrentIndex(Escola.todasAsEscolas().index(aluno['escola']))
            except:
                pass # ??? aluno sem escola
            
        self.lineEditNome.setText(aluno['nome'])
        self.lineEditMatricula.setText(aluno['matricula'])
        data = aluno['dataNasc']
        data_ = data.split(' ')
        if len(data_) < 3:
            data_ = data.split('/')
            mes=0
            try:
                mes=int(data_[1])            
            except:
                mes=dataEmNumero[data_[1]]
            self.dateEdit.setDate(QDate(int(data_[2]), mes, int(data_[0])))        

        else:
            mes=0
            try:
                mes=int(data_[1])            
            except:
                mes=dataEmNumero[data_[1]]
            self.dateEdit.setDate(QDate(int(data_[3]), mes, int(data_[2])))
        
        self.lineEditRG.setText(aluno['RG'])
        self.lineEditCPF.setText(aluno['CPF'])
        self.lineEditMae.setText(aluno['nomeDaMae'])
        self.lineEditPai.setText(aluno['nomeDoPai'])
        self.lineEditTelefone.setText(aluno['telefone'])
        self.lineEditEndereco.setText(aluno['endereco'])
        self.comboBoxEscola.setCurrentText(str(aluno['escola']))
        self.comboBoxSerie.setCurrentText(aluno['serie'])
        self.alunoAnterior=aluno

    def editar(self):
        self.iface.mapWidget.deleteMarker("alunoNovo") 
        Turma.decrement(self.alunoAnterior['serie'], self.alunoAnterior['escola'])
        if self.lineEditNome.text() != "":
            dados = []
            dados.append(self.lineEditNome.text())
            dados.append(self.lineEditMatricula.text())
            nasc = self.dateEdit.date().toString().split()
            nascimento = nasc[2] + "/" + nasc[1] + "/" + nasc[3]
            dados.append(nascimento)
            dados.append(self.lineEditRG.text())
            dados.append(self.lineEditCPF.text())
            dados.append(self.lineEditMae.text())
            dados.append(self.lineEditPai.text())
            dados.append(self.lineEditTelefone.text())
            dados.append(self.lineEditEndereco.text())
            dados.append(self.comboBoxSerie.currentText())
            dados.append(self.comboBoxEscola.currentText())

            id = self.id
            aluno_ = Aluno(dados[0],dados[1],dados[2],dados[3],dados[4],dados[5],dados[6],dados[7],dados[8],dados[9], dados[10], id=id)
            deuCerto = aluno_.editar(id)
            Turma.increment(aluno_['serie'], aluno_['escola'])

            self.lineEditNome.setText("")
            self.lineEditMatricula.setText("")
            self.lineEditRG.setText("")
            self.lineEditCPF.setText("")
            self.lineEditMae.setText("")
            self.lineEditPai.setText("")
            self.lineEditTelefone.setText("")
            self.lineEditEndereco.setText("")
            self.labelId.setText("ID: ")
            self.listViewAlunos.clear()
            if deuCerto == 1:
                messageDialog(self, "Editado", "", "Aluno editado com sucesso!")
            elif deuCerto == 2:
                messageDialog(self, "ERRO", "", "Favor posicione o aluno manualmente")
                #colocar para posicionar manualmente!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                self.iface.alunoId=aluno_.id
                self.iface.mapWidget.centerAt(self.iface.config.get().lat, self.iface.config.get().lng)
                self.iface.mapWidget.addMarker("alunoNovo",self.iface.config.get().lat,self.iface.get().lng,
                **dict(
                icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
                draggable=True,
                title=aluno_.nome
                ))
 
        else: 
            messageDialog(self, "Escolha um aluno", "", "Escolha um aluno na lista ao lado!")

    def excluir(self):
        if self.lineEditRG.text() != "":
            excluir_ = yesNoDialog(self, "Atenção", "Tem certeza que deseja fazer isso?", "Todos os dados desse aluno serão removidos!")
            if excluir_ :
                id=self.id
                self.db.apagarDado(id)
                self.listViewAlunos.clear() 
                self.lineEditNome.setText("")
                self.lineEditMatricula.setText("")
                self.lineEditRG.setText("")
                self.lineEditCPF.setText("")
                self.lineEditMae.setText("")
                self.lineEditPai.setText("")
                self.lineEditTelefone.setText("")
                self.lineEditEndereco.setText("")
                self.labelId.setText("ID: ")
            else :
                messageDialog(self, "Não excluido", "", "Ok, o aluno nao foi excluido")
        else: 
            messageDialog(self, "ID do aluno", "", "Nenhum aluno com esse ID")

    def closeEvent(self, QCloseEvent):
        self.iface.mapWidget.deleteMarker("alunoNovo") 
        return super().closeEvent(QCloseEvent)

