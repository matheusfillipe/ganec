import lib.constants
from sqlitedb import DB
from lib.osmNet import netHandler
from lib.constants import *
from data.aluno import Aluno


from pathlib import Path
import csv, time, sys, math
from PyQt5.QtWidgets import QFileDialog, QWidget
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, Qt, QTimer

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
        return ""


def correctSeries(countChanged):
    dbAluno = DB(str(confPath()/Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
    dbSeries =  DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'])
    count=0
    series = dbSeries.todosOsDadosComId()
    alunos=dbAluno.todosOsDadosComId()
    dbSeries.connect()
    for serie in series:
        countChanged.emit(int(count/(len(alunos)+len(series))*50))
        dbSeries._update(serie["id"], {"nDeAlunos": 0})
        count+=1
    dbSeries.connect()
    for aluno in alunos:
        countChanged.emit(int(count/(len(alunos)+len(series))*50+50))
        id=dbSeries.acharDadoExato(SERIES_ATTR[0], aluno['escola'])
        if len(id)==0:
            print("Erro! Escola não consta na tabela de séries, id: " + str(aluno['escola']))
            continue
        seriesDados=dbSeries.getDadosComId(id)
        id=[serie['id'] for serie in seriesDados if serie['serie']==aluno['serie'] ]   
        if len(id)==0:
            print("Erro! A série "+aluno['serie']+" não pertence a escola de id: "+str(aluno['escola']))
            continue
        serie=dbSeries.getDadoComId(str(id[-1]))
        dbSeries.update(serie['id'], {"nDeAlunos":str(int(serie["nDeAlunos"])+1)})
        count+=1

class imageThread(QtCore.QThread):
    def __init__(self, iface, filepath):
        self.filepath=filepath
        self.iface=iface
        super().__init__()

    def run(self):
        time.sleep(.5)
        self.iface.saveImage(self.filepath)
 
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
        db.connect()
        for aluno in tdodd:
            self.countChanged.emit(int(count/len(tdodd)*100))
            cor=Aluno.getLatLong(aluno['endereco'])
            cor = cor if cor else centro
            db._update(aluno['id'], {'lat': cor[0],'long':cor[1]})
            count +=1          
        db.close()

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
        db.connect()
        for aluno in tdodd:
            self.countChanged.emit(int(count/len(tdodd)*100))
            cor=Aluno.getLatLong(aluno['endereco'])
            cor = cor if cor else centro
            db._update(aluno['id'], {'lat': cor[0],'long':cor[1]})
            count +=1         
        db.close()



class calcularRotasThread(QtCore.QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)
    error = pyqtSignal()
    def __init__(self, alunos=None, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.alunos = alunos

    def run(self):
        count = 0
        dbE=DB(str(confPath() /Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])
        listaDeEscolas=dbE.todosOsDadosComId()
        dbE.connect()
        dbA=DB(str(confPath() /Path(CAMINHO['aluno'])), TABLE_NAME['aluno'], ATRIBUTOS['aluno'])
        if self.alunos is None:
            listaDeAlunos=dbA.todosOsDadosComId()
        else:
            listaDeAlunos=self.alunos
        dbSeries =  DB(str(confPath()/Path(CAMINHO['escola'])), TABLE_NAME['series'], ATRIBUTOS['series'], connection=dbE.connection)        
        configFolder=confPath()
        osmpath=osmFilePath()  #???
        db=DB(str(confPath()/Path('settings.db')),"strings", ['nome', 'string'])
        zonearReto=bool(db.getDado(db.acharDado("nome","zonearReto")[-1])['string'])
        if not Path(osmpath).is_file():
            self.error.emit()
            dbE.close()
            return
        try:
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
            net=netHandler(osmpath=osmpath, linha_reta=zonearReto)   #netHandler distancia até todas
            dbA.connect()
            for j, aluno in enumerate(listaDeAlunos):   #para cada aluno na lista
                self.countChanged.emit(int(j/len(listaDeAlunos)*100))
                try:
                    if aluno['escola'] and aluno['serie'] in dbE._getDado(aluno['escola'])["series"].split(SEPARADOR_SERIES): #Se o aluno esta matriculado e a escola o suporta, ignora
                        continue
                except Exception as e:
                    import traceback     
                    print("Erro: "+str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
                    print("ALUNO: "+str(aluno))
                    continue
                    
                alunoFolder=alunosFolder / Path(str(aluno['id']))
                alunoFolder.mkdir(parents=True, exist_ok=True)
                escolas=[escola for escola in listaDeEscolas if aluno[SERIE] in escola[ESCOLA_SERIES].split(",") ]  #lista de posíveis escolas destino
                ptA=[aluno['long'], aluno['lat']]
                res=[] # resultado [[caminho, distancia, index], ..]
                for i, escola in enumerate(escolas):
                    ptB=[escola['long'], escola['lat']]     
                    try:               
                        parts, dist = net.shortest_path(source=net.addNode(ptA, "aluno: "+str(aluno['id'])), target=net.addNode(ptB, "escola: "+str(escola['id'])))                
                        res.append([parts, dist, i])         
                    except:
                        print("Escola: "+escola['nome']+" não encrontada!!!")                        
                res.sort(key=lambda d: d[1])
                count=False
                for j, valorDados in enumerate(res):      #mínima --> salvar todos geojson com todas com cor variando, blue para a mais proxima    
                    parts, dist, i = valorDados
                    escola=escolas[i]            
                    net.parts=parts
                    saveFile=alunoFolder / Path(str(escola['id'])+".geojson")            
                    net.save_geojson(str(saveFile), COLORS[j if j < len(COLORS) else -1])

                    if not count:            
                        try: #tentar remover a vaga
                            if aluno['escola'] and not aluno['serie'] in dbE._getDado(aluno['escola'])["series"].split(SEPARADOR_SERIES): #Se o aluno esta matriculado e a escola não o suporta mais
                                #remover aluno da série antiga:
                                id=dbSeries._acharDadoExato(SERIES_ATTR[0], aluno['escola'])
                                if len(id)==0:
                                    print("Erro! Escola não consta na tabela de séries, id: " + aluno['escola'])   
                                else:                             
                                    seriesDados=dbSeries._getDadosComId(id)
                                    id=[serie['id'] for serie in seriesDados if serie['serie']==aluno['serie'] ]   
                                    if len(id)==0:
                                        print("Erro! A série "+aluno['serie']+" não pertence a escola de id"+str(aluno['escola']))                                
                                    else:
                                        serie=dbSeries._getDadoComId(str(id[-1]))
                                        dbSeries._update(serie['id'], {"nDeAlunos":serie["nDeAlunos"]-1})

                        except Exception as e:
                            import traceback     
                            print("Erro: "+str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
                            print("ALUNO: "+str(aluno))        
    
                        id=dbSeries._acharDadoExato(SERIES_ATTR[0], escola['id'])
                        if len(id)==0:
                            print("Erro! Escola não consta na tabela de séries, id: " + str(escola['id']))
                            continue
                        seriesDados=dbSeries._getDadosComId(id)
                        id=[serie['id'] for serie in seriesDados if serie['serie']==aluno['serie'] ]   
                        if len(id)==0:
                            print("Erro! A série "+aluno['serie']+" não pertence a escola de id"+str(escola['id']))
                            continue
                        serie=dbSeries._getDadoComId(str(id[-1]))
                        if int(serie[SERIES_ATTR[3]]) < int(serie[SERIES_ATTR[2]]): #salvar mais proxima no dicionário do aluno
                            count=True
                            serie[SERIES_ATTR[3]]=str(int(serie[SERIES_ATTR[3]])+1)
                            dbSeries._update(id[-1], serie)
                            listaDeAlunos[j]['escola']=escola['id']
                            dbA._update(aluno['id'],{'escola': str(escola['id'])})


             #   print("ADICIONANDO  Aluno: " + str(aluno["nome"]))
            #    print("Escola:   " + str(listaDeAlunos[j]['escola']))
            #    print("Serie:    " + str(aluno['serie']))
            dbA.close()
            dbE.close()
        except Exception as e:
            import traceback
            print("Erro: "+str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
            self.error.emit()
            try:
                dbA.close()
            except:
                print("Failed to close Alunos DB")
            try:
                dbE.close()
            except:
                print("Failed to close Escola DB")
            return



class Runner(QtCore.QThread):    
    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self._target = target
        self._args = args
        self._kwargs = kwargs

    def run(self):
        if len(self._kwargs.keys())==0 and len(self._args)==0:
            self._target()   
        else:
            self._target(*self._args, **self._kwargs)

def nogui(func):
    from functools import wraps
    @wraps(func)
    def async_func(*args, **kwargs):
        runner = Runner(func, *args, **kwargs)
        # Keep the runner somewhere or it will be destroyed
        func.__runner = runner
        runner.start()

    return async_func
                

class Overlay(QWidget):
    stoped=pyqtSignal()
    started=pyqtSignal()
    def __init__(self, parent = None, text="", N=8): 
        self.parent=parent
        QWidget.__init__(self, parent)
        parent: QtWidgets.QWidget
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)
        self.label=QtWidgets.QLabel(text, self)
        self.label.setAlignment(Qt.AlignHCenter)
        self.label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.label.setStyleSheet('color: rgb(240,240,240); ')  #border: 2px solid gray;')
        gf=QtWidgets.QGraphicsDropShadowEffect(self)
        gf.setXOffset(2);
        gf.setYOffset(10);
        gf.setBlurRadius(8);
        gf.setColor(QtGui.QColor(10, 10, 30, 200));
        self.label.setGraphicsEffect(gf)
        self.label.setWordWrap(True)
        if parent is not None:
             self.label.setFixedWidth(parent.width())
                
        self.hide()            
        self.N=N
        self.stoped.connect(self.onStop)
        self.started.connect(self.onStart)


    def paintEvent(self, event):        
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(60, 60, 60, 200)))
        painter.setPen(QtGui.QPen(Qt.NoPen))
        N=self.N
        R=max(35,min(self.width(),self.height())/8)
        r=max(25, 2*3.1416*R/N-10)
        d=5        
        self.label.move(12, self.height()/2+R+r+12)
        self.label.setFont(QtGui.QFont("Arial", int(max(min(14*self.height()/350, 24),10)), QtGui.QFont.Bold))

        for i in range(N):
            I=int(self.counter / 5) % N
            if I == i:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(100+d*3, 127+d*3, 240+d*3)))
            elif i==I-1 or I-1+N==i:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(100+d*2, 127+d*2, 220+d*2)))
            elif i==I-2 or I-2+N==i:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(100+d, 127+d, 200+d)))
            elif i==I-3 or I-3+N==i:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 127, 150)))
            else:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 100, 250)))

            painter.drawEllipse(
                self.width()/2 + R * math.cos(2 * math.pi * i / N),
                self.height()/2 + R * math.sin(2 * math.pi * i / N),
                r, r)
        painter.end()
    
    def showEvent(self, event):        
        self.timer = self.startTimer(15)
        self.counter = 0
    
    def timerEvent(self, event):        
        self.counter += 1
        self.update()

#        if self.counter == 240:
#            self.stop()
    def onStart(self):
        self.show()

    def onStop(self):
        self.killTimer(self.timer)
        self.hide()

    def resize(self, w):
        if self.parent is not None:
            self.label.setFixedWidth(self.parent.width()-24)    
        super().resize(w)




     
def test():
    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self, parent = None):
        
            super(QtWidgets.QMainWindow, self).__init__(parent)        
            widget = QWidget(self)
            self.editor = QtWidgets.QTextEdit()
            self.editor.setPlainText("0123456789"*100)
            layout = QtWidgets.QGridLayout(widget)
            layout.addWidget(self.editor, 0, 0, 1, 3)
            button = QtWidgets.QPushButton("Calcular")
            layout.addWidget(button, 1, 1, 1, 1)            
            self.setCentralWidget(widget)

            self.overlay = Overlay(self,"Calculando Absolutamente Nada...")  #Overlay de loading passando qual widget ele deve cobrir e um texto opicional para aparecer
            #self.overlay = Overlay(self)
            button.clicked.connect(self.compute) #O botão ativa a função para rodar em background
       
        def resizeEvent(self, event):        #todo widget tem esse método e essa é a melhor maneira de redimensionar o loading overlay quando o usuário der resize na janela
            self.overlay.resize(event.size()) #redimensiona o overlay
            event.accept()

        @nogui  #Isso aqui é um decorator. A função que ficar abaixo dele vai rodar em background quando chamada, ou seja, em outro thread
        def compute(self, a=None):
            #O qt só permite se comunicar com a main thread por sinais, por isso nunca modifique a UI diretamente por aqui (como criar widgets, mudar textos, etc...)
            self.overlay.started.emit()              # Inicia o overlay emitindo um sinal (loading)

            # Uma tarefa para rodar em segundo plano
            import time 
            for i in range(20):
                time.sleep(.5)
                print("Running....   ", i)
            print("Over.")

            self.overlay.stoped.emit() #para o overlay quando a tarefa estiver pronta



    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    test()