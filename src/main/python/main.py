''' GANEC = Gestor de Alunos Nas Escolas do Carmo '''

import PyQt5
from PyQt5 import QtWidgets, QtGui, uic, Qt, QtCore
from fbs_runtime.application_context import ApplicationContext
import os, sys

from data.config import *
from data.aluno import *
from data.escola import *

#importei a biblioteca para leitura dos dados salvos
import sqlite3

from lib.osm import MapWidget
from lib.gmaps import QGoogleMap 
from lib.database import VariableManager, QInterface
from lib.constants import *


MAIN_WINDOW, _ = uic.loadUiType("./src/main/python/ui/mainWindow.ui")
MODALIDADES_DIALOD, _ = uic.loadUiType("./src/main/python/ui/dialogs/modalidades.ui")
NEW_MODALIDADE_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/modalidadeForm.ui")
SETTINGS_DIALOG,_ = uic.loadUiType("./src/main/python/ui/dialogs/settingsDialog.ui")
NEW_ALUNO_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/alunoForm.ui")
NEW_ESCOLA_WIDGET, _ = uic.loadUiType("./src/main/python/ui/widgets/escolaForm2.ui")
EDITAR_ALUNO, _ = uic.loadUiType("./src/main/python/ui/widgets/editarOuExcluir.ui")

#usado para definir todas as séries que existem. E assim alocar cada aluno numa escola em que a série que ele está existe;
listaDeSeries  = ["Educação infantil - N1",
                  "Educação infantil - N2", 
                  "Educação infantil - N3", 
                  "Ensino Fundamental - 1° Ano", 
                  "Ensino Fundamental - 2° Ano", 
                  "Ensino Fundamental - 3° Ano", 
                  "Ensino Fundamental - 4° Ano", 
                  "Ensino Fundamental - 5° Ano", 
                  "Ensino Fundamental - 6° Ano", 
                  "Ensino Fundamental - 7° Ano", 
                  "Ensino Fundamental - 8° Ano", 
                  "Ensino Fundamental - 9° Ano", 
                  "Ensino Médio - 1° Ano", 
                  "Ensino Médio - 2° Ano", 
                  "Ensino Médio - 3° Ano"]


listaDeModalidades  = ["Ensino Infantil",
                        "Ensino Fundamental", 
                        "Ensino Médio",  
                        "INDEFINIDO"]

cidade = "Carmo Do Paranaíba"

RESET=0

def messageDialog(iface, title="Concluído", info="", message=""):
    msgBox = QtWidgets.QMessageBox(iface)
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.setInformativeText(info)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
    msgBox.show()
    return msgBox.exec_() == QtWidgets.QMessageBox.Ok


def yesNoDialog(iface, title="Atenção", info="", message=""):
    msgBox = QtWidgets.QMessageBox(iface)
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.setInformativeText(info)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
    msgBox.show()
    return msgBox.exec_() == QtWidgets.QMessageBox.Yes


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
            self.iface.varManager.removeDatabase()
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

#defini o ctr-z
        iface.aluno.setup(self,
        signals=[self.pushButtonAdiconar.clicked, self.lineEditNome.textEdited, self.lineEditRG.textEdited, self.lineEditCPF.textEdited, self.lineEditNomeDaMae.textEdited, self.lineEditNomeDoPai.textEdited, self.lineEditTelefone.textEdited, self.lineEditRua.textEdited, self.lineEditNumero.textEdited, self.lineEditBairro.textEdited, self.lineEditComplemento.textEdited, self.lineEditMatricula.textEdited, self.comboBoxSerie.currentIndexChanged],
        slots=[  iface.saveAluno,                 lambda: 0,                    lambda: 0,                  lambda: 0,                   lambda: 0,                         lambda: 0,                         lambda: 0,                        lambda: 0,                   lambda: 0,                      lambda: 0,                      lambda: 0,                           lambda: 0,                         lambda: 0],
        properties=["name",                    "RG",                    "CPF",                    "nomeMae",                      "nomePai",                      "telefone",                    "rua",                    "numero",                    "bairro",                    "complemento",                    "matricula"],
        readers =  [self.lineEditNome.text,    self.lineEditRG.text,    self.lineEditCPF.text,    self.lineEditNomeDaMae.text,    self.lineEditNomeDoPai.text,    self.lineEditTelefone.text,    self.lineEditRua.text,    self.lineEditNumero.text,    self.lineEditBairro.text,    self.lineEditComplemento.text,    self.lineEditMatricula.text],
        writers =  [self.lineEditNome.setText, self.lineEditRG.setText, self.lineEditCPF.setText, self.lineEditNomeDaMae.setText, self.lineEditNomeDoPai.setText, self.lineEditTelefone.setText, self.lineEditRua.setText, self.lineEditNumero.setText, self.lineEditBairro.setText, self.lineEditComplemento.setText, self.lineEditMatricula.setText])

#quando clicar no botao para adicionar escolas ele executa a função, definida aqui, salvarDados        
        self.pushButtonAdiconar.clicked.connect(self.salvarDados)

#quando clicar no botao de opcoes executar editarAluno       
        self.toolButtonEditarAlunos.clicked.connect(self.editarAluno)

    def salvarDados(self):
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

            dadosAluno = [matricula, nome, dataNasc, RG, CPF, nomeDaMae, nomeDoPai, telefone, endereco_, serie]
            dE=definirEscola(dadosAluno)
            l, coordenada = dE.salvarDados(dadosAluno)
            
            erro = 1
            deuCerto=coordenada[0]

            if deuCerto:
                messageDialog(self, "Editado", "", "Aluno encontrado com sucesso!")
            else:
                x,y=coordenada
                messageDialog(self, "ERRO", "", "Favor posicione o aluno manualmente")
                self.iface.w.addMarker(nome,x,y)
                
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
            yesNoDialog(self, "Atenção", "", "Todos os campos Obrigatórios devem estar preenchidos.")

         
    def editarAluno(self):
        dialog=editarAlunoDialog(self.iface)             
        #dialog.setModal(True)
        dialog.show()
        self.iface.dialog.append(dialog)
        dialog.exec_()



#classe para escolher entre editar ou excluir um aluno
class editarAlunoDialog(QtWidgets.QDialog, EDITAR_ALUNO):   

    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        EDITAR_ALUNO.__init__(self)
        self.setupUi(self)
        self.addTodosOsAlunos()

        #quando clicar no botao de buscas executar a funcao de procurar alunos
        self.pushButtonBuscarAluno.clicked.connect(self.encontraraluno)

        #quando apertar para editar algum aluno
        self.pushButtonEditar.clicked.connect(self.editar)

        #quando apertar para excluir algum aluno
        self.pushButtonExcluir.clicked.connect(self.excluir)

        #quando escolher algum item da lista
        self.listViewAlunos.itemClicked.connect(self.setarAluno)

        for i in listaDeSeries:
            self.comboBoxSerie.addItem(i)
        #self.comboBoxSerie.setInitialPos(idSerie)

    def addTodosOsAlunos(self):

        dadosSalvos = sqlite3.connect("dadosAlunos.db")
        cursor = dadosSalvos.cursor()

        lista = []
        self.listViewAlunos.clear()
        row = 0

        for i in cursor.execute("SELECT rowid, * FROM dados ORDER BY nome"):
            lista.append(i)
            nasc = lista[row][3].split()
            nascimento = nasc[2] + "/" + nasc[1] + "/" + nasc[3]
            strr = "Nome: " + lista[row][2]  + "  - Matrícula: " + lista[row][1] + "\n" + listaDeSeries[lista[row][10]] + "\nData de Nascimento: " + nascimento + "\nRG: " + lista[row][4] + "  - CPF: " + lista[row][5] + "\nMãe: " + lista[row][6] + "  - Pai: " + lista[row][7] + "\nTelefone: " + lista[row][8] + "\nEndereço: " + lista[row][9] + "\nEscola: " +  str(lista[row][11]) + "\nID: " + str(lista[row][14]) + "\n\n"
            self.listViewAlunos.addItem(strr)
            row = row + 1
        
        dadosSalvos.close()
    
    def setarAluno(self):

        #caso um aluno seja removido isso aqui vai dar errado! Porque listView não vai saber o indixe que está no banco de dados
        #Equando que no banco de dados o indice se mantem o mesmo

        var = manipularDB(self.listViewAlunos.currentItem().text())
        lista = var.setarAluno()
        #print(lista)

        self.lineEditNome.setText(lista[0])
        self.lineEditMatricula.setText(lista[1])
        self.lineEditRG.setText(lista[2])
        self.lineEditCPF.setText(lista[3])
        self.lineEditMae.setText(lista[4])
        self.lineEditPai.setText(lista[5])
        self.lineEditTelefone.setText(lista[6])
        self.lineEditEndereco.setText(lista[7])
        self.labelEscola.setText("Escola: " + str(lista[8]))
        self.labelId.setText("ID: " + str(lista[10]))
        self.dateEditNascimento.setDate(lista[9])

    def editar(self):
        if self.lineEditNome.text() != "" and self.labelId.text() != "ID: ":

            dados = []

            dados.append(self.lineEditNome.text())
            dados.append(self.lineEditMatricula.text())
            dados.append(self.lineEditRG.text())
            dados.append(self.lineEditCPF.text())
            dados.append(self.lineEditMae.text())
            dados.append(self.lineEditPai.text())
            dados.append(self.lineEditTelefone.text())
            dados.append(self.lineEditEndereco.text())
            dados.append(self.comboBoxSerie.currentIndex())

            var = manipularDB(self.listViewAlunos.currentItem().text())
            deuCerto = var.editarAluno(dados)

            self.lineEditNome.setText("")
            self.lineEditMatricula.setText("")
            self.lineEditRG.setText("")
            self.lineEditCPF.setText("")
            self.lineEditMae.setText("")
            self.lineEditPai.setText("")
            self.lineEditTelefone.setText("")
            self.lineEditEndereco.setText("")
            self.labelId.setText("ID: ")

            self.addTodosOsAlunos()
            
            if deuCerto == 1:
                messageDialog(self, "Editado", "", "Aluno editado com sucesso!")
            elif deuCerto == 2:
                messageDialog(self, "ERRO", "", "Favor posicione o aluno manualmente")



        else: 
            messageDialog(self, "Escolha um aluno", "", "Escolha um aluno na lista ao lado!")

    def excluir(self):
        if self.lineEditRG.text() != "":

            excluir_ = yesNoDialog(self, "Atenção", "Tem certeza que deseja fazer isso?", "Todos os dados desse aluno serão removidos!")
            
            if excluir_ :

                var = manipularDB(self.listViewAlunos.currentItem().text())
                deuCerto = var.excluirAluno()

                self.addTodosOsAlunos()

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


    def encontraraluno(self):
        lista = []
        idsComOsNomes = []
        dadosSalvos = sqlite3.connect("dadosAlunos.db")
        cursor = dadosSalvos.cursor()

        alunoEncontrar = self.lineEditBuscarAlunos.text()

        for row in cursor.execute("SELECT rowid, * FROM dados ORDER BY nome"):
                lista.append(row)

        if alunoEncontrar != "":
            i = 0
            for row in lista:
                print (row[2].count(alunoEncontrar))
                if row[2].count(alunoEncontrar) > 0:
                    idsComOsNomes.append(i)
                i = i + 1
                
            #print(idsComOsNomes)
            self.listViewAlunos.clear()
            
            if idsComOsNomes == []:
                 self.listViewAlunos.addItem("Nenhum Aluno com esse nome")

            else:
                for row in idsComOsNomes:

                    nasc = lista[row][3].split()
                    nascimento = nasc[2] + "/" + nasc[1] + "/" + nasc[3]

                    strr = "Nome: " + lista[row][2]  + "  - Matrícula: " + lista[row][1] + "\n" + listaDeSeries[lista[row][10]] + "\nData de Nascimento: " + nascimento + "\nRG: " + lista[row][4] + "  - CPF: " + lista[row][5] + "\nMãe: " + lista[row][6] + "  - Pai: " + lista[row][7] + "\nTelefone: " + lista[row][8] + "\nEndereço: " + lista[row][9] + "\n\n"
                    self.listViewAlunos.addItem(strr)
                
        else :
            self.listViewAlunos.clear()
            self.listViewAlunos.addItem("Digite um nome")
        dadosSalvos.close()

#mudei até aqui!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        NEW_ALUNO_WIDGET.__init__(self)
        self.setupUi(iface)   



class NewModalidadeWidget(QtWidgets.QWidget, NEW_MODALIDADE_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_MODALIDADE_WIDGET.__init__(self)
        self.setupUi(self)      

        self.lineEdit:QtWidgets.QLineEdit

        self.widget : QtWidgets.QWidget
        self.widget : QtWidgets.QWidget
        self.label : QtWidgets.QLabel
        self.lineEdit : QtWidgets.QLineEdit
        self.pushButton : QtWidgets.QPushButton

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
        
    def addToListWidget1(self, modalidade:Modalidade, removable=False):

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

    def addToListWidget2(self, turma:Turma, removable=False):        
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

class NewEscolaWidget(QtWidgets.QWidget, NEW_ESCOLA_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ESCOLA_WIDGET.__init__(self)
        self.setupUi(iface)

#DIALOG ESCOLA
class NewEscolaDialog(QtWidgets.QDialog, NEW_ESCOLA_WIDGET):
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ALUNO_WIDGET.__init__(self)    
        self.iface = iface
        self.iface.varManager : VariableManager
        self.iface=iface
        newEscolaWidget = NewEscolaWidget(self)
        newEscolaWidget.show()
        self.setupUi(iface)
        #self.signals_connection();

        self.lineEditNome : QtWidgets.QLineEdit
        self.lineEditRua : QtWidgets.QLineEdit
        self.lineEditNumero : QtWidgets.QLineEdit
        self.lineEditBairro : QtWidgets.QLineEdit


        self.comboBoxModalidade : QtWidgets.QComboBox


        for i in listaDeModalidades:
            self.comboBoxModalidade.addItem(i)


      #  iface.escola.setup(self,
      #  signals=[self.buttonOk.clicked, self.lineEditNome.textEdited, self.lineEditRua.textEdited, self.lineEditNumero.textEdited, self.lineEditBairro.textEdited,  self.comboBoxModalidade.currentIndexChanged],
      #  slots=[  iface.saveEscola,                 lambda: 0,                    lambda: 0,                  lambda: 0,                   lambda: 0,                         lambda: 0,                         lambda: 0],
      #  properties=["nome",                    "rua",                    "numero",                    "bairro",                      "modalidade"],
      #  readers =  [self.lineEditNome.text,    self.lineEditRua.text,    self.lineEditNumero.text,    self.lineEditBairro.text],
      #  writers =  [self.lineEditNome.text,    self.lineEditRua.text,    self.lineEditNumero.text,    self.lineEditBairro.text])
 
        self.buttonOk.clicked.connect(self.salvarDadosEscola)

    def salvarDadosEscola(self):
        erro = 0

        nome = self.lineEditNome.text()
        rua = self.lineEditRua.text()
        numero = self.lineEditNumero.text()
        bairro = self.lineEditBairro.text()
        modalidade = self.comboBoxModalidade.text()


        if (self.lineEditNome.text() != "") and (self.lineEditRua.text() != "") and (self.lineEditNumero.text() != "") and (self.lineEditBairro.text() != ""):
            erro = 1
            yesNoDialog(self, "Atenção", "", "É necessário preencher todos os campos.")
        

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
        self.addMap()
        self.dialog=[]

#Mechi aqui tbm !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def buscarAluno(self):
        aluno = self.lineEditAluno.text()

        var = buscaAvancadaAluno(aluno)

        busca = var.buscando()

        self.w.addMarkerAtAdress(aluno)
        self.w.centerAtAdress(aluno)        

        #print(list(busca))

        #for i in busca:
            #self.listViewBusca.addItem(i)

 
    def closeEvent(self, event):
        # here you can terminate your threads and do other stuff

        # and afterwards call the closeEvent of the super-class
        [d.close() for d in self.dialog]
        super().closeEvent(event)       

    def restartProgram(self):
        self.app.restart=True
        self.close()
        self.app.quit()
    
    def updateCenter(self, key, lat, lng):
        if key=="Centro":
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
            w.markerMoved.connect(self.updateCenter)
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
        self.aluno.save(DB_ADD_ALUNO)

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




def main(*args):
    while True:
        app = QtWidgets.QApplication(*args)
        app.restart=False
        win=MainWindow(app)
        win.showMaximized()     
        currentExitCode=app.exec_()
        if not app.restart:
            break        
    return currentExitCode   

if __name__ == '__main__':
    currentExitCode=main(sys.argv)
    sys.exit(currentExitCode)
