import lib.constants
from sqlitedb import DB
from lib.osmNet import netHandler
from lib.constants import *
from data.aluno import Aluno


from pathlib import Path
import csv, time
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal


# Nomes dos atributos:
IDADE='idade'
PASTA_ALUNOS='alunos'
SERIE='serie'
ESCOLA_SERIES='series'  #lista de modalidades ou séries separadas por virgula em formato string
COLORS=["blue", "green", "yellow", "red", "black"] #em ordem de proximidade
DB_FILEPATH='/home/matheus/test.db'
TABLE_ESCOLAS="escolas"
TABLE_SERIES="SERIES"
SERIES_ATTR= ['idDaEscola' ,'serie' ,'vagas', 'nDeAlunos']
DELIMITADOR_CSV=';'

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



def osmFilePath():
    db=DB(str(confPath()/Path('settings.db')),"strings", ['nome', 'string'])
    try:
        return db.getDado(db.acharDado('nome','osmPath')[0])['string']
    except:
        return False




class imageThread(QtCore.QThread):
    def __init__(self, iface, filepath):
        self.filepath=filepath
        self.iface=iface
        super().__init__()

    def run(self):
        time.sleep(.5)
        self.iface.mapWidget.saveImage(self.filepath)
 
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
            self.countChanged.emit(int(count/len(tdodd)*100))
            cor=Aluno.getLatLong(aluno['endereco'])
            cor = cor if cor else centro
            db.update(aluno['id'], {'lat': cor[0],'long':cor[1]})
            count +=1          

class calcularEscolasThread(QtCore.QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)
    def __init__(self, iface):
        self.iface=iface
        super().__init__()

    def run(self):
        count = 0
        db= DB(str(confPath() /Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        a=Aluno()
        tdodd=db.todosOsDadosComId()
        config=self.iface.config       
        centro=[config.get().lat, config.get().lng]
        for aluno in tdodd:
            self.countChanged.emit(int(count/len(tdodd)*100))
            cor=Aluno.getLatLong(aluno['endereco'])
            cor = cor if cor else centro
            db.update(aluno['id'], {'lat': cor[0],'long':cor[1]})
            count +=1          



class calcularRotasThread(QtCore.QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)
    error = pyqtSignal()

    def run(self):
        count = 0
        dbE= DB(str(confPath() /Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        listaDeEscolas=dbE.todosOsDadosComId()
        dbA= DB(str(confPath() /Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        listaDeAlunos=dbA.todosOsDadosComId()
        configFolder=confPath()
        osmpath=osmFilePath()  #???
        if not osmpath:
            self.error.emit()
            return
    #def gerarDistAlunos(listaDeEscolas, listaDeAlunos, configFolder, osmpath='/home/matheus/map.osm'):
        '''
        retorna uma lista de alunos atualizada com a propriedade escola escolhida com o id da listaDeEscolas
        Ambas as listas são dicionários contendo o id
        Cria uma pasta aluno dentro de configFolder com uma pasta para cada id onde serão armazenados os geojson para cada caminho
        '''
        #pasta (id) --> 1.geojson, 2.geojson ... etc   idDaEscola.geojson 
        alunosFolder=Path(configFolder) / Path(PASTA_ALUNOS)    
        alunosFolder.mkdir(parents=True, exist_ok=True)
        #sort alunos by age, menor para maior  #TODO calcular idade exata
        listaDeAlunos.sort(key=lambda d: d[IDADE])   
        net=netHandler(osmpath=osmpath)     #netHandler distancia até todas

        for j, aluno in enumerate(listaDeAlunos):   #para cada aluno na lista
            self.countChanged.emit(int(j/len(listaDeAlunos)*100))
            alunoFolder=alunosFolder / Path(str(aluno['id']))
            alunoFolder.mkdir(parents=True, exist_ok=True)
            escolas=[escola for escola in listaDeEscolas if aluno[SERIE] in escola[ESCOLA_SERIES].split(",") ]  #lista de posíveis escolas destino
            ptA=[aluno['long'], aluno['lat']]
            res=[] # resultado [[caminho, distancia], ..]
            for i, escola in enumerate(escolas):
                ptB=[escola['long'], escola['lat']]
                parts, dist = net.shortest_path(source=net.addNode(ptA, "aluno: "+str(aluno['id'])), target=net.addNode(ptB, "escola: "+str(escola['id'])))
                res.append([parts, dist, i])
            
            res.sort(key=lambda d: d[1])
            count=False
            for i, r in enumerate(res):      #mínima --> salvar todos geojson com todas com cor variando, blue para a mais proxima    
                escola=escolas[i]            
                net.parts=r[0]
                saveFile=alunoFolder / Path(str(escola['id'])+".geojson")            
                net.save_geojson(str(saveFile), COLORS[i if i < len(COLORS) else -1])

                if not count:
                    db=DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
                    id=db.acharDado(SERIES_ATTR[0], escola['id'])
                    if len(id)==0:
                        print("Erro! Escola não consta na tabela de séries, id: " + escola['id'])
                        continue
                    id=id[0]            
                    serie=db.getDado(id)
                    if serie[SERIES_ATTR[3]] <= serie[SERIES_ATTR[2]]: #salvar mais proxima no dicionário do aluno
                        count=True
                        serie[SERIES_ATTR[3]]+=1
                        db.update(id, serie)                     
                        listaDeAlunos[j]['escola']=escola['id']

            dbA.update(aluno['id'],{'escola': listaDeAlunos[j]['escola']})
            #TODO imcrementar turmas 

                
def test():
    
    import math, sys
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5 import QtWidgets, QtGui
    from PyQt5.QtWidgets import QWidget

    class Overlay(QWidget):
        def __init__(self, parent = None):    
            QWidget.__init__(self, parent)
            palette = QtGui.QPalette(self.palette())
            palette.setColor(palette.Background, Qt.transparent)
            self.setPalette(palette)
        
        def paintEvent(self, event):
        
            painter = QtGui.QPainter()
            painter.begin(self)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(255, 255, 255, 127)))
            painter.setPen(QtGui.QPen(Qt.NoPen))
            
            for i in range(6):
                if (self.counter / 5) % 6 == i:
                    painter.setBrush(QtGui.QBrush(QtGui.QColor(127 + (self.counter % 5)*32, 127, 127)))
                else:
                    painter.setBrush(QtGui.QBrush(QtGui.QColor(127, 127, 127)))
                painter.drawEllipse(
                    self.width()/2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                    self.height()/2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10,
                    20, 20)
            
            painter.end()
        
        def showEvent(self, event):
        
            self.timer = self.startTimer(50)
            self.counter = 0
        
        def timerEvent(self, event):
        
            self.counter += 1
            self.update()
            if self.counter == 60:
                self.killTimer(self.timer)
                self.hide()


    class MainWindow(QtWidgets.QMainWindow):

        def __init__(self, parent = None):
        
            super(QtWidgets.QMainWindow, self).__init__(parent)        
            widget = QWidget(self)
            self.editor = QtWidgets.QTextEdit()
            self.editor.setPlainText("0123456789"*100)
            layout = QtWidgets.QGridLayout(widget)
            layout.addWidget(self.editor, 0, 0, 1, 3)
            button = QtWidgets.QPushButton("Wait")
            layout.addWidget(button, 1, 1, 1, 1)
            
            self.setCentralWidget(widget)
            self.overlay = Overlay(self.centralWidget())
            self.overlay.hide()
            button.clicked.connect(self.overlay.show)
        
        def resizeEvent(self, event):
        
            self.overlay.resize(event.size())
            event.accept()




    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    test()