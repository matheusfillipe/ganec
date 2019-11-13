from PyQt5 import QtWidgets, QtGui, uic, Qt, QtCore
from PyQt5.QtCore import pyqtSignal
from lib.constants import *
from customWidgets import *
from sqlitedb import DB
from data.aluno import *
from data.escola import *
from threads import nogui, Overlay

try:
    I=0
    NEW_ALUNO_WIDGET, _ = uic.loadUiType(BASEPATHS[I]+"ui/widgets/alunoForm.ui")
    EDITAR_ALUNO, _ = uic.loadUiType(BASEPATHS[I]+"ui/widgets/editarOuExcluir.ui")
    ALUNO_BUSCA, _ = uic.loadUiType(BASEPATHS[I]+"ui/widgets/alunoBusca.ui")
except:
    I=1
    NEW_ALUNO_WIDGET, _ = uic.loadUiType(BASEPATHS[I]+"ui/widgets/alunoForm.ui")
    EDITAR_ALUNO, _ = uic.loadUiType(BASEPATHS[I]+"ui/widgets/editarOuExcluir.ui")
    ALUNO_BUSCA, _ = uic.loadUiType(BASEPATHS[I]+"ui/widgets/alunoBusca.ui")

from data.config import *

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
       # self.pushButton : QtWidgets.QPushButton
       # self.pushButton.clicked.connect(self.editar)
        self.dbEscola = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        strr = "Nome: " + aluno['nome'] + "\nMãe: " + aluno['nomeDaMae'] + "\nPai: " + aluno['nomeDoPai'] + "\nEscola: "
        if aluno['escola']!="" and aluno['escola']!=None:
            strr+=self.dbEscola.getDadoComId(aluno['escola'])['nome']
        else:
            strr+="--"
        self.label.setText(strr) 

    def editar(self):
        diag=editarAlunoDialog(self.parent, self.aluno['id'])
        diag.exec_()        

    def mouseDoubleClickEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            editarAlunoDialog(self.parent, self.aluno['id']).exec_()
        return super().mouseDoubleClickEvent(QMouseEvent)

class NewAlunoDialog(QtWidgets.QDialog, NEW_ALUNO_WIDGET):
    geolocate=pyqtSignal(Aluno, bool, int, int)
    def __init__(self, iface):
        QtWidgets.QWidget.__init__(self)
        NEW_ALUNO_WIDGET.__init__(self)
        iface : MainWindow
        self.iface=iface 
        self.setupUi(self)
        self.aluno = self.iface.aluno

        self.dbEscola = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        self.dbSeries = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])

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
        #self.comboBoxEscolas : QtWidgets.QComboBox
        comboSeries=SERIES
        self.comboBoxSerie.addItems(comboSeries)

        self.pushButtonAdiconar.clicked.connect(self.salvarDados)
        self.toolButtonEditarAlunos.clicked.connect(self.editarAluno)

        self.overlay = Overlay(self,"Geolocalizando...")  
        self.geolocate.connect(self.onGeolocate)
    
    def resizeEvent(self, event):        
        self.overlay.resize(event.size()) 
        event.accept()

    @nogui
    def salvarDados(self, a=None):
        self.iface.mapWidget.deleteMarker("alunoNovo")
        erro = 0
        self.overlay.started.emit()

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
            
            endereco_ = endereco_ + ", " + Config.cidade()

            aluno = Aluno(nome, matricula, dataNasc, RG, CPF, nomeDaMae, nomeDoPai, telefone, endereco_, serie)
            coordenada = aluno.salvar()
            
            erro = 1
            deuCerto=coordenada[0]
            self.geolocate.emit(aluno, True, deuCerto, id)
        else:
            self.geolocate.emit(Aluno(), False, 0, id)

        self.overlay.stoped.emit()

    def onGeolocate(self, aluno, preenchido, deuCerto, id):
        if preenchido:       
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
        else:
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

    geolocate=pyqtSignal(Aluno, bool, int, str, str)
    def __init__(self, iface, alunoId=None):
        QtWidgets.QWidget.__init__(self)       
        self.alunoId=alunoId
        self.setupUi(self)
        self.iface=iface
        self.alunoSet = {'serie':None}
        self.db = DB(str(confPath() /Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        self.dbEscola = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        self.dbSeries = DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
        self.todasAsEscolas = []
        for i in self.dbEscola.todosOsDados():
            self.todasAsEscolas.append(i)
        #quando apertar para editar algum aluno
        self.pushButtonEditar.clicked.connect(self.editar)
        #quando apertar para excluir algum aluno
        self.pushButtonExcluir.clicked.connect(self.excluir)
        #quando escolher algum item da lista
        self.listViewAlunos.itemClicked.connect(lambda: self.setarAluno(None))
        if len(self.todasAsEscolas)==0:
            self.invalid=True
            return
        self.comboBoxEscola: QtWidgets.QComboBox

        '''#######################self.comboBoxEscola.addItems(todasEscolas)
        self.comboBoxEscola.currentTextChanged.connect(self.comboBoxSerie.clear)
        self.comboBoxEscola.currentTextChanged.connect(lambda text: self.comboBoxSerie.addItems(iface.dbEscola.acharDados('nome', text)[-1]['series'].split(SEPARADOR_SERIES)))
        self.comboBoxEscola.currentTextChanged.emit(todasEscolas[0])
        #quando pesquisar um nome'''
        self.lineEditBuscarAlunos.textChanged.connect(self.buscarOsAlunos)
        self.comboBoxEscola.currentTextChanged.connect(self.adicionarSeries)
        self.labelId.hide()
        if not alunoId is None:
            self.setarAluno(alunoId)
        self.overlay = Overlay(self,"Geolocalizando...")  
        self.geolocate.connect(self.onGeolocate)
    
    def resizeEvent(self, event):        
        try:
            self.overlay.resize(event.size()) 
        except:
            pass
        event.accept()

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
            strr = "Nome: " + i['nome'] + "  - Matrícula: " + i['matricula'] + "\n" + i['serie'] + "\nData de Nascimento: " + nascimento + "\nRG: " + i['RG'] + "  - CPF: " + i['CPF'] + "\nMãe: " + i['nomeDaMae'] + "  - Pai: " + i['nomeDoPai'] + "\nTelefone: " + i['telefone'] + "\nEndereço: " + i['endereco']
            try:
                strr+="\nEscola: " +  self.dbEscola.getDadoComId(i['escola'])['nome']  + "\n\n"
            except:
                strr+="\nEscola: ----\n\n"

            self.listViewAlunos.addItem(strr)
            row = row + 1

    def setarAluno(self, id=None):
        
        self.listViewAlunos : QtWidgets.QListWidget

        #if id is None:
        if id is None:
            self.nomeAntes = self.resultado[self.listViewAlunos.currentRow()]['nome']
            id = self.db.acharDadoExato('nome', self.nomeAntes)[-1]
        else:
            self.nomeAntes = ""
#            id = self.db.acharDado('nome', self.nomeAntes)[-1]
        #id = self.listViewAlunos.currentRow()
        #id = self.resultado[id]["id"]
        self.id=id
        aluno = self.iface.dbAluno.getDado(id)
        self.dbAluno = self.iface.dbAluno       
        self.alunoSet = aluno

        self.lineEditNome.setText(aluno['nome'])
        self.lineEditMatricula.setText(aluno['matricula'])

        self.comboBoxEscola.clear()
        self.comboBoxSerie.clear()

        #print(aluno['escola'])
        #print(aluno['serie'])

        ordemDasEscolas = []
        print("Dados")
        for i in self.todasAsEscolas:
            ordemDasEscolas.append(i['nome'])
            self.comboBoxEscola.addItem(i['nome'])
        self.comboBoxEscola.addItem("Sem escola")
        j = 0
        temEscola = False
        for i in self.todasAsEscolas:
            if aluno['escola'] != None and aluno['escola'] != "":
                print("escola:" +str(aluno['escola']) + ".")
                escola =  self.dbEscola.getDadoComId(aluno['escola'])['nome']
            else:
                escola = None
            if i['nome'] == escola:
                temEscola = True
                break
            j+=1
        if not temEscola:
            j=-1
            self.comboBoxEscola.setCurrentIndex(len(ordemDasEscolas))
            messageDialog(title="ERRO", message="Esse aluno ainda não tem uma escola\nCalcule as rotas novamente") # ??? aluno sem escola
        else:
            print(self.todasAsEscolas[j]['nome'])
            self.comboBoxEscola.setCurrentIndex(j)
        
        self.adicionarSeries()

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
        #self.comboBoxEscola.setCurrentText(str(aluno['escola']))
        #self.comboBoxSerie.setCurrentText(aluno['serie'])
        self.alunoAnterior=aluno
    
    def adicionarSeries(self):
        self.comboBoxSerie.clear()
        if self.comboBoxEscola.currentText() != "Sem escola":
            series = []
            for i in self.dbSeries.acharDados('idDaEscola', (self.dbEscola.acharDado('nome', self.comboBoxEscola.currentText())[-1])):
                series.append(i)
                self.comboBoxSerie.addItem(i['serie'])
            j = 0
            for i in series:
                #print(self.alunoSet['serie'])
                if i['serie'] == self.alunoSet['serie']:
                    break
                j+=1
            self.comboBoxSerie.setCurrentIndex(j)
        else:
            comboSeries = []
            comboSeries=list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in self.dbEscola.todosOsDados()],[])))
            self.comboBoxSerie.addItems(comboSeries)

    #@nogui
    def editar(self, a=None):
        self.iface.mapWidget.deleteMarker("alunoNovo") 
        self.overlay.started.emit()
        #Turma.decrement(self.alunoAnterior['serie'], self.alunoAnterior['escola'])
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
            serieEditar = self.comboBoxSerie.currentText()
            if self.comboBoxEscola.currentText() != "Sem escola":
                escolaEditar = self.comboBoxEscola.currentText()
            else:
                escolaEditar = ""
            if serieEditar == "":
                serieEditar = self.alunoSet['serie']

            id = self.id

            #print("SSerie " + serieEditar)
            print("EEscola "+ escolaEditar)

            if escolaEditar != "" and escolaEditar != None:
                serieAnterior = self.alunoSet['serie']
                if self.alunoSet['escola'] != "" and self.alunoSet['escola'] != None:
                    escolaAnterior = self.dbEscola.getDadoComId(self.alunoSet['escola'])['nome']
                else:
                    escolaAnterior = ""

                if (escolaAnterior == "" or escolaAnterior == None) and escolaEditar!=escolaAnterior:
                    print("Sem escola anterior mais cadastrando em uma")
                    idEscolaEditar     = self.dbEscola.acharDadoExato('nome',       escolaEditar)[-1]
                    idDaSerieEditar1   = self.dbSeries.acharDadoExato('idDaEscola', idEscolaEditar)
                    idDaSerieEditar2   = self.dbSeries.acharDadoExato('serie',      serieEditar)
                    idDaSerieEditar    = [i for i in idDaSerieEditar1 if i in idDaSerieEditar2]

                    escolaEditar_ =   self.dbEscola.getDadoComId(idEscolaEditar)
                    serieEditar_ =    self.dbSeries.getDadoComId(idDaSerieEditar[-1])

                    if int(serieEditar_['nDeAlunos'])+1<=serieEditar_['vagas']:
                        self.dbSeries.update(serieEditar_['id'], {'nDeAlunos': (int(serieEditar_['nDeAlunos'])+1)})
                        dados[9] = serieEditar_['serie']
                        dados[10] = escolaEditar_['id']
                        aluno_ = Aluno(dados[0],dados[1],dados[2],dados[3],dados[4],dados[5],dados[6],dados[7],dados[8],dados[9], dados[10], id=id)
                        deuCerto = aluno_.editar(id)
                    else:
                            messageDialog(title="ERRO", message="Essa serie nessa escola já esta cheia")
                else:
                    print("Com escola anterior e cadastrando em uma nova")
                    idEscolaAnterior   = self.dbEscola.acharDadoExato('nome',       escolaAnterior)[-1]
                    idEscolaEditar     = self.dbEscola.acharDadoExato('nome',       escolaEditar)[-1]
                    idDaSerieAnterior1 = self.dbSeries.acharDadoExato('idDaEscola', idEscolaAnterior)
                    idDaSerieAnterior2 = self.dbSeries.acharDadoExato('serie',      serieAnterior)
                    idDaSerieAnterior  = [i for i in idDaSerieAnterior1 if i in idDaSerieAnterior2]
                    idDaSerieEditar1   = self.dbSeries.acharDadoExato('idDaEscola', idEscolaEditar)
                    idDaSerieEditar2   = self.dbSeries.acharDadoExato('serie',      serieEditar)
                    idDaSerieEditar    = [i for i in idDaSerieEditar1 if i in idDaSerieEditar2]

                    escolaEditar_ =   self.dbEscola.getDadoComId(idEscolaEditar)
                    escolaAnterior_ = self.dbEscola.getDadoComId(idEscolaAnterior)

                    serieAnterior_ =  self.dbSeries.getDadoComId(idDaSerieAnterior[-1])
                    self.dbSeries.update(serieAnterior_['id'], {'nDeAlunos': (int(serieAnterior_['nDeAlunos'])-1)})

                    serieEditar_ =    self.dbSeries.getDadoComId(idDaSerieEditar[-1])

                    print(serieEditar_)
                    print(serieAnterior_)

                    if int(serieEditar_['nDeAlunos'])+1<=serieEditar_['vagas']:
                        self.dbSeries.update(serieEditar_['id'], {'nDeAlunos': (int(serieEditar_['nDeAlunos'])+1)})
                        dados[9] = serieEditar_['serie']
                        dados[10] = escolaEditar_['id']
                        aluno_ = Aluno(dados[0],dados[1],dados[2],dados[3],dados[4],dados[5],dados[6],dados[7],dados[8],dados[9], dados[10], id=id)
                        deuCerto = aluno_.editar(id)
                    else:
                            messageDialog(title="ERRO", message="Essa serie nessa escola já esta cheia")
            else:
                print("com escola cadastrando em nenhuma")
                if self.alunoSet['escola'] != "" and self.alunoSet['escola']:
                    escolaAnterior = self.dbEscola.getDadoComId(self.alunoSet['escola'])['nome']
                    serieAnterior = self.alunoSet['serie']
                    idEscolaAnterior   = self.dbEscola.acharDadoExato('nome',       escolaAnterior)[-1]
                    idDaSerieAnterior1 = self.dbSeries.acharDadoExato('idDaEscola', idEscolaAnterior)
                    idDaSerieAnterior2 = self.dbSeries.acharDadoExato('serie',      serieAnterior)
                    idDaSerieAnterior  = [i for i in idDaSerieAnterior1 if i in idDaSerieAnterior2]

                    escolaAnterior_ = self.dbEscola.getDadoComId(idEscolaAnterior)

                    serieAnterior_ =  self.dbSeries.getDadoComId(idDaSerieAnterior[-1])
                    self.dbSeries.update(serieAnterior_['id'], {'nDeAlunos': (int(serieAnterior_['nDeAlunos'])-1)})

                print(serieEditar)

                dados[9] = serieEditar
                dados[10] = ""
                aluno_ = Aluno(dados[0],dados[1],dados[2],dados[3],dados[4],dados[5],dados[6],dados[7],dados[8],dados[9], dados[10], id=id)
                deuCerto = aluno_.editar(id)
                    
        else:
            self.geolocate.emit(Aluno(), False , 0, "", "")

        self.overlay.stoped.emit()
        self.listViewAlunos.clear()
        self.lineEditNome.setText("")
        self.lineEditMatricula.setText("")
        self.lineEditRG.setText("")
        self.lineEditCPF.setText("")
        self.lineEditMae.setText("")
        self.lineEditPai.setText("")
        self.lineEditTelefone.setText("")
        self.lineEditEndereco.setText("")

    def onGeolocate(self, aluno_, preenchido, deuCerto, serieEditar, escolaEditar):
        if preenchido:
            self.lineEditNome.setText("")
            self.lineEditMatricula.setText("")
            self.lineEditRG.setText("")
            self.lineEditCPF.setText("")
            self.lineEditMae.setText("")
            self.lineEditPai.setText("")
            self.lineEditTelefone.setText("")
            self.lineEditEndereco.setText("")
            self.labelId.setText("ID: ")
            self.comboBoxEscola.clear()
            self.listViewAlunos.clear()
            if deuCerto == 1:
                messageDialog(self, "Editado", "", "Aluno editado com sucesso!")

            elif deuCerto == 2:
                messageDialog(self, "ERRO", "", "Favor posicione o aluno manualmente")
                self.iface.alunoId=aluno_.id
                self.iface.mapWidget.centerAt(self.iface.config.get().lat, self.iface.config.get().lng)
                self.iface.mapWidget.addMarker("alunoNovo",self.iface.config.get().lat,self.iface.get().lng,
                **dict(
                icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
                draggable=True,
                title=aluno_.nome
                ))

            elif deuCerto == 3:
                messageDialog(self, "Erro ao editar", "", ("As vagas para a série " + serieEditar + " na escola " + escolaEditar + " já estão cheias"))
 
        else: 
            messageDialog(self, "Escolha um aluno", "", "Escolha um aluno na lista ao lado!")


    def excluir(self):
        excluir_ = yesNoDialog(self, "Atenção", "Tem certeza que deseja fazer isso?", "Todos os dados desse aluno serão removidos!")
        if excluir_ :
            id=self.id
            self.db.apagarDado(self.db.acharDadoExato('nome', self.nomeAntes)[-1])
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

    def closeEvent(self, QCloseEvent):
        self.iface.mapWidget.deleteMarker("alunoNovo") 
        return super().closeEvent(QCloseEvent)


def pular(PULO):
    from collections import OrderedDict
    dbEscola=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
    dbAlunos=DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
    dbSeries =  DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
    series=SERIES #list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in dbEscola.todosOsDados()],[])))
    print("Alunos: ",[aluno['serie'] for aluno in dbAlunos.todosOsDados()])
    print("Series: ",series)
    #PULO=1 #muda para -1 para descer de séries

    for aluno in dbAlunos.todosOsDadosComId():
        ## Move o aluno para a próxima serie
        serie=aluno['serie']
        if serie=="FORMADO":
            continue
        elif serie=="SEM_ESCOLA":
            continue
        else:
            serieIndex=series.index(serie)
            nextSerieIndex=serieIndex+PULO
            escolaId=aluno['escola']
            serieId=[id for id in dbSeries.acharDadoExato("idDaEscola", escolaId) if id in dbSeries.acharDadoExato("serie", aluno['serie'])][-1]
            serieDados=dbSeries.getDado(serieId)
            escola=dbEscola.getDado(escolaId)

        if nextSerieIndex>=len(series): #ALUNO FORMOU
            serie="FORMADO"  #Serie para todos que formaram (Como isso não existe em nenhuma escola vai ser ignorado)
        elif nextSerieIndex<=0 or not serie in escola["series"].split(SEPARADOR_SERIES):  #Se a escola não te suporta mais
            serie="SEM_ESCOLA"
        else:
            serie=series[nextSerieIndex]            
            novaSerieId=[id for id in dbSeries.acharDadoExato("idDaEscola", escolaId) if id in dbSeries.acharDadoExato("serie", serie)][-1]
            novaSerieDados=dbSeries.getDado(novaSerieId)
            dbSeries.update(novaSerieId,{"vagas": novaSerieDados['vagas']+1})  #Adiciona o aluno a nova vaga

        dbAlunos.update(aluno['id'], {"serie":serie})

        ## remove a vaga do aluno na tabela de series antiga
        dbSeries.update(serieId,{"vagas": serieDados['vagas']-1})
    print("Alunos: ",[aluno['serie'] for aluno in dbAlunos.todosOsDados()])
    print("Series: ",series)
 
def pular(PULO):
    from collections import OrderedDict
    dbEscola=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
    dbAlunos=DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
    dbSeries =  DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
    series=SERIES #list(OrderedDict.fromkeys(sum([escola["series"].split(SEPARADOR_SERIES) for escola in dbEscola.todosOsDados()],[])))
    print("Alunos: ",[aluno['serie'] for aluno in dbAlunos.todosOsDados()])
    print("Series: ",series)
    #PULO=1 #muda para -1 para descer de séries
    return

    for aluno in dbAlunos.todosOsDadosComId():
        ## Move o aluno para a próxima serie
        serie=aluno['serie']
        if serie=="FORMADO":
            continue
        elif serie==series[0]:        
            continue
        else:
            serieIndex=series.index(serie)
            nextSerieIndex=serieIndex+PULO
            escolaId=aluno['escola']
            serieId=[id for id in dbSeries.acharDadoExato("idDaEscola", escolaId) if id in dbSeries.acharDadoExato("serie", aluno['serie'])][-1]
            serieDados=dbSeries.getDado(serieId)
            escola=dbEscola.getDado(escolaId)

        if nextSerieIndex>len(series)-1: #ALUNO FORMOU
            serie="FORMADO"  #Serie para todos que formaram (Como isso não existe em nenhuma escola vai ser ignorado)
        elif nextSerieIndex<=0 or not serie in escola["series"].split(SEPARADOR_SERIES):  #Se a escola não te suporta mais
            serie=series[0]
        else:
            serie=series[nextSerieIndex]            
            novaSerieId=[id for id in dbSeries.acharDadoExato("idDaEscola", escolaId) if id in dbSeries.acharDadoExato("serie", serie)][-1]
            novaSerieDados=dbSeries.getDado(novaSerieId)
            dbSeries.update(novaSerieId,{"vagas": novaSerieDados['vagas']+1})  #Adiciona o aluno a nova vaga

        dbAlunos.update(aluno['id'], {"serie":serie})

        ## remove a vaga do aluno na tabela de series antiga
        dbSeries.update(serieId,{"vagas": serieDados['vagas']-1})
    print("Alunos: ",[aluno['serie'] for aluno in dbAlunos.todosOsDados()])
    print("Series: ",series)

if __name__=="__main__":
    pular(1)

