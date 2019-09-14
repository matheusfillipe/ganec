''' GANEC = Gestor de Alunos Nas Escolas do Carmo '''

import PyQt5
from PyQt5 import QtWidgets, QtGui, uic, Qt, QtCore
from fbs_runtime.application_context import ApplicationContext
import os, sys, traceback
from copy import deepcopy

from data.config import *
from data.aluno import *
from data.escola import *
from lib.osm import MapWidget
from lib.gmaps import QGoogleMap 
from lib.database import VariableManager, QInterface
from lib.constants import *
from algoritmos import *
from customWidgets import exportCsv, confPath, csvDialog
from PyQt5.QtCore import pyqtSignal

MAIN_WINDOW, _ = uic.loadUiType("./src/main/python/ui/mainWindow.ui")
MODALIDADES_DIALOD, _ = uic.loadUiType("./src/main/python/ui/dialogs/modalidades.ui")
NEW_MODALIDADE_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/modalidadeForm.ui")
SETTINGS_DIALOG,_ = uic.loadUiType("./src/main/python/ui/dialogs/settingsDialog.ui")
NEW_ALUNO_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/alunoForm.ui")
NEW_ESCOLA_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/escolaForm2.ui")
EDITAR_ALUNO, _ = uic.loadUiType("./src/main/python/ui/widgets/editarOuExcluir.ui")
ALUNO_BUSCA, _ = uic.loadUiType("./src/main/python/ui/widgets/alunoBusca.ui")
EDITAR_ESCOLA, _ = uic.loadUiType("./src/main/python/ui/widgets/escolaEditar.ui")


RESET=0

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
        self.label.setText("Nome: " + aluno['nome'] + "\nMatrícula: "+aluno['matricula'])
    
    def mouseDoubleClickEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            editarAlunoDialog(self.parent, self.aluno['id']).exec_()
        return super().mouseDoubleClickEvent(QMouseEvent)
       

class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    def __init__(self,iface):
        QtWidgets.QWidget.__init__(self)
        SETTINGS_DIALOG.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)

        self.comboBox : QtWidgets.QComboBox 
        self.lineEdit : QtWidgets.QLineEdit
        self.lineEdit_2 : QtWidgets.QLineEdit
        self.buttonBox : QtWidgets.QDialogButtonBox

        self.comboBox.addItem("Google")    
        self.comboBox.addItem("OSM")
        self.comboBox.addItem("Here")
        self.comboBox.addItem("Arquivo")

        iface.config.setup(self,
        signals=[self.buttonBox.accepted, self.comboBox.currentIndexChanged, self.aplicarBtn.clicked, self.cleanDbButton.clicked],
        slots=[iface.saveConfig,                lambda: 0,                         iface.saveConfig,           self.reset],
        properties=["map"],
        readers=[self.comboBox.currentIndex],
        writers=[self.comboBox.setCurrentIndex])        
        
    
    def reset(self):        
        reply = yesNoDialog(iface=self, message="Tem certeza que deseja remover todos os dados cadastrados?", 
        info="Esta operação irá remover todos os arquivos de configuração e de banco de dados. Isso não é reversível.")
        if reply:
            try:
                self.iface.varManager.removeDatabase()
            except:
                pass
            try:
                os.rmdir(str(confPath()))
            except:
                pass
            messageDialog(self, message="O programa irá reiniciar")
            self.close()
            self.iface.restartProgram()                

#classe que pega os dados digitados na UI e concatena em uma string, assim como os manda para um otra classe em outro arquivo
#chamado aluno, que vai salvar e organizar esses dados e também pesquizar qual a escola mais próxima

class NewAlunoDialog(QtWidgets.QDialog, NEW_ALUNO_WIDGET):

    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ALUNO_WIDGET.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)
        self.aluno = self.iface.aluno

#mostro ao python o que é cada coisa "defino variaveis"

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

#adicionei a comboBox de séries cada série disponível nas escolas. conferir se as séries estao corretas.
        for i in listaDeSeries:
            self.comboBoxSerie.addItem(i)

        '''#defini o ctr-z
        iface.aluno.setup(self,
        signals=[self.pushButtonAdiconar.clicked, self.lineEditNome.textEdited, self.lineEditRG.textEdited, self.lineEditCPF.textEdited, self.lineEditNomeDaMae.textEdited, self.lineEditNomeDoPai.textEdited, self.lineEditTelefone.textEdited, self.lineEditRua.textEdited, self.lineEditNumero.textEdited, self.lineEditBairro.textEdited, self.lineEditComplemento.textEdited, self.lineEditMatricula.textEdited, self.comboBoxSerie.currentIndexChanged],
        slots=[  iface.saveAluno,                 lambda: 0,                    lambda: 0,                  lambda: 0,                   lambda: 0,                         lambda: 0,                         lambda: 0,                        lambda: 0,                   lambda: 0,                      lambda: 0,                      lambda: 0,                           lambda: 0,                         lambda: 0],
        properties=["name",                    "RG",                    "CPF",                    "nomeMae",                      "nomePai",                      "telefone",                    "rua",                    "numero",                    "bairro",                    "complemento",                    "matricula"],
        readers =  [self.lineEditNome.text,    self.lineEditRG.text,    self.lineEditCPF.text,    self.lineEditNomeDaMae.text,    self.lineEditNomeDoPai.text,    self.lineEditTelefone.text,    self.lineEditRua.text,    self.lineEditNumero.text,    self.lineEditBairro.text,    self.lineEditComplemento.text,    self.lineEditMatricula.text],
        writers =  [self.lineEditNome.setText, self.lineEditRG.setText, self.lineEditCPF.setText, self.lineEditNomeDaMae.setText, self.lineEditNomeDoPai.setText, self.lineEditTelefone.setText, self.lineEditRua.setText, self.lineEditNumero.setText, self.lineEditBairro.setText, self.lineEditComplemento.setText, self.lineEditMatricula.setText])
        '''
#quando clicar no botao para adicionar escolas ele executa a função, definida aqui, salvarDados        
        self.pushButtonAdiconar.clicked.connect(self.salvarDados)

#quando clicar no botao de opcoes executar editarAluno       
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
        serie = self.comboBoxSerie.currentIndex()

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



#classe para escolher entre editar ou excluir um aluno
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
        for i in listaDeSeries:
            self.comboBoxSerie.addItem(i)
        #quando pesquisar um nome
        self.lineEditBuscarAlunos.textChanged.connect(self.buscarOsAlunos)
        self.labelId.hide()
        if not alunoId is None:
            self.setarAluno(alunoId)
        self.show()

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
            strr = "Nome: " + i['nome'] + "  - Matrícula: " + i['matricula'] + "\n" + listaDeSeries[int(i['serie'])] + "\nData de Nascimento: " + nascimento + "\nRG: " + i['RG'] + "  - CPF: " + i['CPF'] + "\nMãe: " + i['nomeDaMae'] + "  - Pai: " + i['nomeDoPai'] + "\nTelefone: " + i['telefone'] + "\nEndereço: " + i['endereco'] + "\nEscola: " +  str(i['escola'])  + "\n\n"
            self.listViewAlunos.addItem(strr)
            row = row + 1

    def setarAluno(self, id=None):
        if id is None:
            self.listViewAlunos : QtWidgets.QListWidget
            id = self.listViewAlunos.currentRow()
            id = self.resultado[id]["id"]
            self.id=id
            aluno = self.db.getDado(id)
        else:
            aluno=self.db.getDado(id)
            self.id=id
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
        self.labelEscola.setText("Escola: " + str(aluno['escola']))
        self.comboBoxSerie.setCurrentIndex(int(aluno['serie']))
      #  self.id=id
       # self.labelId.setText("ID: " + str(id[0]))

    def editar(self):
        self.iface.mapWidget.deleteMarker("alunoNovo") 
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
            dados.append(self.comboBoxSerie.currentIndex())
            id = self.id
            aluno_ = Aluno(dados[0],dados[1],dados[2],dados[3],dados[4],dados[5],dados[6],dados[7],dados[8],dados[9], id=id)
            deuCerto = aluno_.editar(id)
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


#mudei até aqui!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
class NewModalidadeWidget(QtWidgets.QWidget, NEW_MODALIDADE_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init__(self)
        self.setupUi(self)        
        self.lineEdit:QtWidgets.QLineEdit
        self.lineEdit.setPlaceholderText("Nome da Modalidade")

class NewTurmaWidget(QtWidgets.QWidget, NEW_MODALIDADE_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init__(self)
        self.setupUi(self)
        self.lineEdit:QtWidgets.QLineEdit
        self.lineEdit.setPlaceholderText("Turma/Série")

class ModalidadesDialog(QtWidgets.QDialog, MODALIDADES_DIALOD):
    edited = QtCore.pyqtSignal()
    def __init__(self, iface):
        QtWidgets.QDialog.__init__(self)
        MODALIDADES_DIALOD.__init__(self)
        self.setupUi(self)

        self.iface:MainWindow
        self.varManager:VariableManager
        self.listWidget:QtWidgets.QListWidget
        self.listWidget_2:QtWidgets.QListWidget
        self.modalidades:QInterface
        self.buttonBox:QtWidgets.QDialogButtonBox

        self.iface=iface
        self.varManager:VariableManager = iface.varManager
        self.modalidades=self.iface.modalidades    
        self.listWidget.itemClicked.connect(self.modalidadeChanged)

        self.modalidades.setup(self,
            signals =  [],
            slots   =  [], 
            properties=["modalidades"], 
            readers  = [self.read],
            writers  = [self.write]
        )

    def read(self):
        return []

    def write(self,modalidades:list):
        for i,m in enumerate(modalidades):   
            self.addToListWidget1(m, removable=True if i<len(modalidades)-1 else False)
        
    def addToListWidget1(self, modalidade, removable=False):

        itemN = QtWidgets.QListWidgetItem() 
        widget = NewModalidadeWidget(self)
        widget.label.setText("Modalidade Escolar: ")
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())  
        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)

        i=self.listWidget.row(itemN)
        widget.lineEdit.setText(modalidade.nome)                
        widget.pushButton.clicked.connect(lambda: self.addToListWidget1(Modalidade()))
        widget.pushButton.clicked.connect(lambda: self.setRemovableFromListWidget1(widget, itemN))

        if removable:
            self.setRemovableFromListWidget1(widget, itemN)


    def removeFromListWidget1(self, item):
        i=self.listWidget.row(item)
        self.listWidget.takeItem(i)
        self.modalidades.get().removeByIndex(i)

    def setRemovableFromListWidget1(self, widget, itemN):
        while True:
            try: widget.pushButton.clicked.disconnect() 
            except Exception: break
        widget.lineEdit.setReadOnly(True)
        widget.pushButton.clicked.connect(lambda: self.removeFromListWidget1(itemN))
        widget.pushButton.setText("Remover")

    def modalidadeChanged(self):
        item=self.listWidget.currentItem()
        self.listWidget_2.clear()  
        lista=self.modalidades.get().modalidades[self.listWidget.row(item)].turmas
        for i,t in enumerate(lista):
            self.addToListWidget2(t,removable=True if i < len(lista)-1 else False)

    def addToListWidget2(self, turma, removable=False):        
        item=self.listWidget.currentItem()
        itemN = QtWidgets.QListWidgetItem() 
        widget = NewTurmaWidget(self)
        widget.label.setText("Turma: ")
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        itemN.setSizeHint(widget.sizeHint())    

        self.listWidget_2.addItem(itemN)
        self.listWidget_2.setItemWidget(itemN, widget)
        widget.pushButton.clicked.connect(lambda: self.addToListWidget2(Turma()))
        widget.pushButton.clicked.connect(lambda: self.setRemovableFromListWidget2(widget, itemN))

        if removable:
            self.setRemovableFromListWidget2(widget, itemN)

    def removeFromListWidget2(self, item):
        i=self.listWidget_2.row(item)
        item=self.listWidget.currentItem()       
        self.listWidget_2.takeItem(i)   
        self.modalidades.get().modalidades[self.listWidget.row(item)]
        

    def setRemovableFromListWidget2(self, widget, itemN):
        while True:
            try: widget.pushButton.clicked.disconnect() 
            except Exception: break
        widget.lineEdit.setReadOnly(True)
        widget.pushButton.clicked.connect(lambda: self.removeFromListWidget2(itemN))
        widget.pushButton.setText("Remover")

class NewEscolaDialog(QtWidgets.QDialog, NEW_ESCOLA_WIDGET):
    def __init__(self, iface):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        self.iface = iface
        self.lineEditNome : QtWidgets.QLineEdit
        self.lineEditRua : QtWidgets.QLineEdit
        self.lineEditNumero : QtWidgets.QLineEdit
        self.lineEditBairro : QtWidgets.QLineEdit
        self.comboBoxModalidade : QtWidgets.QComboBox

        for i in listaDeModalidades:
            self.comboBoxModalidade.addItem(i) 
        self.buttonOk.clicked.connect(self.salvarDadosEscola)
        self.toolButtonEditar.clicked.connect(self.editarEscola)
        self.buttonCancelar.clicked.connect(self.close)
    
    def editarEscola(self):
        dialog=editarEscolaDialog(self.iface)
        dialog.setModal(True)
        dialog.show()
        self.iface.dialog.append(dialog)
        dialog.exec_()


    def salvarDadosEscola(self):
        nome = self.lineEditNome.text()
        rua = self.lineEditRua.text()
        numero = self.lineEditNumero.text()
        bairro = self.lineEditBairro.text()
        modalidad = self.comboBoxModalidade.currentIndex()
        

        #Verificar se todos os dados foram preenchidos
        if (self.lineEditNome.text() != "") and (self.lineEditRua.text() != "") and (self.lineEditNumero.text() != "") and (self.lineEditBairro.text() != ""):
            enderecoEscola = [rua, numero, bairro]
            stringEndereco = "Rua " + rua + ", " + numero + ", " + bairro + cidade
        else:
            messageDialog(self, "Atenção", "Todos os campos devem ser preenchidos.")

        nome = self.lineEditNome.setText("")
        rua = self.lineEditRua.setText("")
        numero = self.lineEditNumero.setText("")
        bairro = self.lineEditBairro.setText("")
        
        escola = Escola(nome, enderecoEscola, modalidad)
        coordenada = escola.salvar()
            
class editarEscolaDialog(QtWidgets.QDialog, EDITAR_ESCOLA):   

    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        EDITAR_ESCOLA.__init__(self)
        self.setupUi(self)
        self.db = DB(CAMINHO['escola'], TABLE_NAME['escola'], ATRIBUTOS['escola'])
        #quando apertar para editar algum aluno
        #self.pushButtonEditar.clicked.connect()
        #quando apertar para excluir algum aluno
        #self.pushButtonExcluir.clicked.connect(self.excluir)
        #quando escolher algum item da lista
        #self.listViewEscolas.itemClicked.connect(self.setarEscola)
        #for i in listaDeModalidades:
        #    self.comboBoxModalidade.addItem(i) 

 
class calcularAlunosThread(QtCore.QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)
    def __init__(self, iface):
        self.iface=iface
        super().__init__()

    def run(self):
        count = 0
        db= DB(str(confPath() /Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        a=Aluno()
        tdodd=db.todosOsDadosComId()
        tdodd=[aluno for aluno in tdodd if not aluno['lat']]       
        config=self.iface.config
        centro=[config.get().lat, config.get().lng]
        for aluno in tdodd:
            a.endereco=aluno['endereco']
            cor=a.latLongAluno()
            cor = cor if cor else centro
            db.update(aluno['id'], {'lat': cor[0],'long':cor[1]})
            count +=1          
            self.countChanged.emit(int(count/len(tdodd)*100))



class calcularEscolasThread(QtCore.QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)

    def run(self):
        count = 0
        db= DB(str(confPath() /Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        a=Aluno()
        tdodd=db.todosOsDadosComId()
        varManager=VariableManager(os.path.dirname(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)))       
        config=varManager.read(Config(),DB_CONFIG)  
        centro=[config.get().lat, config.get().lng]
        for aluno in tdodd:
            a.endereco=aluno['endereco']
            cor=a.latLongAluno()
            cor = cor if cor else centro
            db.update(aluno['id'], {'lat': cor[0],'long':cor[1]})
            count +=1          
            self.countChanged.emit(int(count/len(tdodd)*100))



class MainWindow(QtWidgets.QMainWindow, MAIN_WINDOW):

    def __init__(self, app):         
        QtWidgets.QMainWindow.__init__(self)
        MAIN_WINDOW.__init__(self)
        self.app : QtWidgets.QApplication
        self.app=app 
        self.varManager=VariableManager(os.path.dirname(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)))
        if RESET:
            #self.varManager.removeDatabase()
            self.close()
        self.setupUi(self)
        self.actionSair.triggered.connect(self.close)
        self.actionModalidades.triggered.connect(self.modalidadesDialog)
        self.actionAlunos.triggered.connect(self.newAlunoDialog)    
        self.actionConfigura_es.triggered.connect(self.settingDialog)               
        self.actionEscolas.triggered.connect(self.newEscolaDialog)
        self.config=self.varManager.read(Config(),DB_CONFIG)  
        self.config.modified.connect(lambda: self.config.customSlot("disclaim"))   
        self.config.notModified.connect(lambda: self.config.customSlot("apply"))
        self.pushButtonBusca.clicked.connect(self.buscarAluno)
        self.actionExportarBusca.triggered.connect(self.exportarBusca)
        self.listViewBusca.itemClicked.connect(self.setarEndereco)
        self.idEscola = 0
        self.latLong = []
        self.latLongAns = ["a"]
        self.spinBoxIdadeMaxima.setValue(50)
        self.spinBoxIdadeMinima.setValue(1)
        for i in ["Escolas:","teste1","teste2","teste3","teste4","teste5", "teste6"]:
            self.comboBoxEscolas.addItem(i)
            '''colocar para buscar todas as escolas'''
        for i in ATRIBUTOS_STRING['aluno']:
            self.comboBoxBusca.addItem(i)
        self.listaParaExportar = []
        self.comboBoxEscolas.currentIndexChanged.connect(self.adicionarSeries)
        self.lineEditAluno.textChanged.connect(self.buscarAluno)
        self.scrollAreaTeste : QtWidgets.QScrollArea
        self.addMap()
        self.dialog=[]
        self.actionAlunos_3.triggered.connect(self.imporAlunoCsv)
        self.actionEscolar.triggered.connect(self.imporEscolaCsv)
        self.actionCalcular_rotas.triggered.connect(self.calcularRotas)
        self.progressBar.hide()        

    def calcularRotas(self):
        self.calc = calcularRotasThread()
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()   
        self.loadingLabel.setText("Computando rotas")   
        self.calc.finished.connect(self.cleanProgress)   


    def imporAlunoCsv(self):
        dialog=csvDialog(CSV_ALUNOS)
        dialog.exec_()
        res=dialog.result
        if not res: return
        try:
            dados=deepcopy(res)
            a=Aluno()
            for i, r in enumerate(res):            
                dados[i].update({"idade": a.calcularIdade(r['dataNasc'])})
            db = DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
            db.salvarDados(dados)   

        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
    
        self.calc = calcularAlunosThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()   
        self.loadingLabel.setText("Computando localização dos alunos")   
        self.calc.finished.connect(self.cleanProgress)   

    def onCountChanged(self, value):
        self.progressBar.show()
        self.progressBar.setValue(value)


    def imporEscolaCsv(self):
        dialog=csvDialog(CSV_ESCOLAS)
        dialog.exec_()
        res=dialog.result
        if not res: return
        try:          
            db = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
            dbs= DB(str(confPath()/Path(CAMINHO['series'])), TABLE_NAME['series'], ATRIBUTOS['series'])
            for r in res:
                id=db.salvarDado(r)
                for s in r['series'].split(","): 
                   dbs.salvarDado(dbs.toDict([id,s,0,0]))            

        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1])

        self.calc = calcularEscolasThread()
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()         
        self.calc.finished.connect(self.cleanProgress)       
        self.loadingLabel.setText("Computando localização das Escolas")      

    def cleanProgress(self):
        self.progressBar.setValue(0)
        self.loadingLabel.setText("")
        self.progressBar.hide()

#Mechi aqui tbm !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def buscarAluno(self):        
        self.idadeMinima = self.spinBoxIdadeMinima.value()
        self.idadeMaxima = self.spinBoxIdadeMaxima.value()
        self.listViewBusca.clear()
        db = DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        busca = self.lineEditAluno.text()
        try:
            if self.comboBoxBusca.currentIndex() != 0:
                listaDeIdsBusca = db.acharDado(ATRIBUTOS['aluno'][self.comboBoxBusca.currentIndex() - 1], busca)

                serie = 0
                listaDeIdsSeries = []
                for i in listaDeSeries:
                    if self.checkBoxSeries[i].isChecked():
                        for j in db.acharDado(ATRIBUTOS['aluno'][9], serie):
                            listaDeIdsSeries.append(j)
                    serie += 1

                listaDeIdsIdade = []
                for i in range((self.idadeMaxima - self.idadeMinima) + 1):
                    i+=(self.idadeMinima)
                    ids = db.acharDado(ATRIBUTOS['aluno'][11], i)
                    for row in ids:
                        listaDeIdsIdade.append(row)
                id1 = [id1 for id1 in listaDeIdsBusca if id1 in listaDeIdsIdade]
                id = [id for id in id1 if id in listaDeIdsSeries]
                
                resultado=db.getDadosComId(id)                
                self.buscaResultado=resultado
                
                self.latLong = []
                j = 0
                for i in resultado:
                    id_ = id[j]
                    self.latLong.append([i['nome'],i['lat'], i['long'], id_])                    
                    itemN = QtWidgets.QListWidgetItem() 
                    widget = alunoBusca(self, i)                   
                    itemN.setSizeHint(widget.sizeHint())  
                    self.listViewBusca.addItem(itemN)                    
                    self.listViewBusca.setItemWidget(itemN, widget)
                    d=deepcopy(i)  #remover coisas inúteis para csv
                    d.pop("id")
                    self.listaParaExportar.append(d)
                    j += 1
                if j==0:
                    self.listViewBusca.addItem("Nenhum aluno foi encontrado")
                   
        except Exception as e:
            print(e)
            self.listViewBusca.addItem("Nenhum aluno foi cadastrado até o momento")
    
    def exportarBusca(self):
        if len(self.listaParaExportar) > 0:
            exportCsv(self.listaParaExportar)
        else:
            messageDialog(self, "Problema ao salvar arquivo", "", "Nenhum aluno corresponde a busca")

    def setarEndereco(self):       
        self.mapWidget.deleteMarker("aluno")
        coordenads = self.latLong[self.listViewBusca.currentRow()]
        self.mapWidget.centerAt(coordenads[1], coordenads[2])
        self.mapWidget.addMarker("aluno", coordenads[1], coordenads[2], **dict(
        icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
        draggable=True,
        title=coordenads[0]
        ))
        print(self.latLongAns[0])
        self.latLongAns = coordenads
    
    def markerMovido(self, n, lat, long):
        if n=="Centro":
            self.updateCenter(lat, long)
        elif n=="aluno":
            id = self.buscaResultado[self.listViewBusca.currentRow()]['id']        
            v = Aluno("", "", "", "", "", "", "", "", "", 0, 0, 0, lat, long, id)
            v.salvarCoordenada()            
        elif n=="alunoNovo":
            v = Aluno("", "", "", "", "", "", "", "", "", 0, 0, 0, lat, long, self.alunoId)
            v.salvarCoordenada()          

    def adicionarSeries(self):
        self.idEscola = self.comboBoxEscolas.currentIndex() - 1
        print(self.idEscola)
        top_widget = QtWidgets.QWidget()
        top_layout = QtWidgets.QVBoxLayout()
        top_layout.setSpacing(1)
        listaDeSeries_add = listaDeSeries #!!!!!!!!!!!!!!!!!!!!!Adicionar as series para cada escola.
        self.checkBoxSeries = {}
        for i in listaDeSeries_add:
            self.checkBoxSeries[i] = QtWidgets.QCheckBox(i)
            group_box = QtWidgets.QGroupBox()
            layout = QtWidgets.QHBoxLayout(group_box)
            layout.addWidget(self.checkBoxSeries[i])
            top_layout.addWidget(group_box)
        top_widget.setLayout(top_layout)
        self.scrollAreaTeste.setWidget(top_widget)
        self.scrollAreaTeste.setFixedSize(self.spinBoxIdadeMinima.width()*12,self.spinBoxIdadeMinima.height()*8)

    def closeEvent(self, event):
        # here you can terminate your threads and do other stuff

        # and afterwards call the closeEvent of the super-class
        [d.close() for d in self.dialog]
        super().closeEvent(event)       

    def restartProgram(self):
        self.app.restart=True
        self.close()
        self.app.quit()
    
    def updateCenter(self, lat, lng):       
            self.config.get().setInitialPos(lat,lng)
            self.config.save(DB_CONFIG)

    def addMap(self):
        if self.config.get().map==3:
            w=QtWidgets.QLabel("shapefile não está disponível, por favor mude para google ou osm nas configurações")
        elif self.config.get().map==2:
            #TODO implement here maps
            w=QtWidgets.QLabel("Here Maps não está disponível, por favor mude para google ou osm nas configurações")
        elif self.config.get().map==1:
            w=MapWidget()
        elif self.config.get().map==0:
            w=QGoogleMap(lat=self.config.get().lat, lng=self.config.get().lng)
            w.markerMoved.connect(self.markerMovido)
        else:
            w=QtWidgets.QLabel("Problema no banco de dados! Tente limpar as configurações")
        self.mapWidget=w
        self.horizontalLayout_4.addWidget(w)
        w.show()

    def settingDialog(self):
        dialog=SettingsDialog(self)
       # dialog.setModal(True)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()
    
    def saveAluno(self):
        print("Não está salvando")
        #self.aluno.save(DB_ADD_ALUNO)

    def saveEscola(self):
        pass

    def newAlunoDialog(self): 
        self.aluno=self.varManager.read(Aluno(), DB_ADD_ALUNO) 
        dialog=NewAlunoDialog(self)             
        #dialog.setModal(True)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()


    def newEscolaDialog(self):  
        self.escola=self.varManager.read(Escola(), DB_ADD_ESCOLA) 
        dialog=NewEscolaDialog(self)             
        #dialog.setModal(True)
        self.dialog.append(dialog)
        dialog.show()
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
        self.modalidades=self.varManager.read(ListaModalidades(),DB_MODALIDADES_BASE)    
        dialog=ModalidadesDialog(self)
        #dialog.setModal(True)
        dialog.accepted.connect(self.modalidades.save)
        self.dialog.append(dialog)
        dialog.show()
        dialog.exec_()


def main(*args):
    global CONF_PATH
    while True:
        try:
            app = QtWidgets.QApplication(*args)
            app.restart=False
            win=MainWindow(app)
            from pathlib import Path
            path=QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.ConfigLocation)[0] / Path(NAME)
            path.mkdir(parents=True, exist_ok=True)  
            CONF_PATH=str(path)
            win.showMaximized()     
            currentExitCode=app.exec_()
            if not app.restart:
                break        
        except Exception as e:
            messageDialog(title="Erro", message=str(traceback.format_exception(None, e, e.__traceback__))[1:-1], info="O programa irá reiniciar")
            currentExitCode=-13
        return currentExitCode   

if __name__ == '__main__':
    currentExitCode=main(sys.argv)
    sys.exit(currentExitCode)