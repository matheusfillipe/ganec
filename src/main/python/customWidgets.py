from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtGui, uic, QtCore
import csv
from PyQt5.QtWidgets import QFileDialog
from pathlib import Path

from lib.constants import *

DELIMITADOR_CSV=';'
CSV_DIALOG, _ = uic.loadUiType("./src/main/python/ui/dialogs/importCsv.ui")
delimiter = ";"


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

def confPath():
    path=QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.ConfigLocation)[0] / Path(NAME)
    path.mkdir(parents=True, exist_ok=True)  
    return path
 

class csvDialog(QtWidgets.QDialog, CSV_DIALOG):
    def __init__(self, dataNamesList:list, parent=None):
        '''dataNamesList: lista de strings com os nomes dos possíveis atributos '''
        super().__init__(None)
        self.setupUi(self)
        self.horizontalLayout : QtWidgets.QHBoxLayout
        self.cbList=[]
        self.dataNamesList=dataNamesList         
        self.result=[]
        self.header=[]

        for i,dName in enumerate(dataNamesList):
            cb=QtWidgets.QComboBox()                       
            cb.addItems(dataNamesList)
            self.con(cb,i) 
            vlay=QtWidgets.QVBoxLayout()
            lbl=QtWidgets.QLabel(str(i+1))
            vlay.addWidget(lbl)
            vlay.addWidget(cb)
            self.horizontalLayout.addLayout(vlay)
            cb.show()            
            lbl.show()
            self.cbList.append(cb)           

    def updateData(self, text, index):        
        for i, cb in enumerate(self.cbList):
            cb:QtWidgets.QComboBox         
            if i!=index:
                j=cb.currentIndex()
                while self.dataNamesList[j] in [cb.currentText() for k, cb in enumerate(self.cbList) if i!=k]:
                    j=j+1 if not j+1>=len(self.dataNamesList) else 0
                cb.setCurrentIndex(j)                
                self.con(cb, i) 
    
    def default(self):
        range=QtWidgets.QTableWidgetSelectionRange(0,0,9,len(self.dataNamesList)-1)
        self.tableWidget.setRangeSelected(range, True)
        for i,cb in enumerate(self.cbList):                        
            cb : QtWidgets.QComboBox
            cb.currentTextChanged.disconnect()
            cb.setCurrentIndex(i)
            self.con(cb,i) 

    def con(self, cb, i):
        cb.currentTextChanged.connect(lambda text: self.updateData(text, i))       

    def exec_(self):
        if self.openFile():
            self.default()
            return super().exec_()
        else:
            messageDialog(title="Atenção!", message="A planilha não contém um número de colunas suficiente ("+str(len(self.dataNamesList))+")")
            return                   
 

    def show(self):
        if self.openFile():
            self.default()
            return super().show()
        else:
            messageDialog(title="Atenção!", message="A planilha não contém um número de colunas suficiente ("+str(len(self.dataNamesList))+")")
            return        
    
    def accept(self):
        self.result=self.csvRead()   
        if not self.result:
            return 
        return super().accept()
    
    def csvRead(self):
        global delimiter
        result=[]
        first=True
        columnIndexes=list(set(index.column() for index in self.tableWidget.selectionModel().selectedIndexes()))
        if len(columnIndexes) != len(self.dataNamesList):
            messageDialog(title="Atenção!", message="Por favor selectione o mesmo número de colunas que de campos necessários \n Você seleciou "+str(len(columnIndexes))+", mas são necessários "+str(len(self.dataNamesList)))
            return False

        with open(self.filepath, 'r') as fi:
            for i, r in enumerate(csv.reader(fi, delimiter=delimiter, dialect='excel')):
                if self.checkBox.isChecked() and first:
                    first=False
                    continue
                first=False
                dado = {}
                j=0
                for field, dName in zip([f for index, f in enumerate(r) if index in columnIndexes], 
                                                        [cb.currentText() for cb in self.cbList]):
                    if dName=="":
                        messageDialog(title="Atenção!", message="Por favor atribua valores para cada coluna")
                        return False
                    dado[dName]=field
                result.append(dado)
        return result
    
    def openFile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(filter="Arquivo/Planilha CSV (*.csv)")[0]
        if filename in ["", None]: return False
        self.filepath=filename
        self.tableWidget : QtWidgets.QTableWidget

        with open(self.filepath, 'r') as fi:
            for i,r in enumerate(csv.reader(fi, delimiter=delimiter, dialect='excel')):        
                for j,field in enumerate(r):
                    if i==0:
                        self.header.append(field)                        
                        continue
                    if i>=1:
                        if i==1 and j==0:
                            self.tableWidget.setRowCount(10)                      
                            self.tableWidget.setColumnCount(len(self.header))
                            self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectColumns)
                            self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
                            #self.tableWidget.setHorizontalHeaderLabels((str(i+1) for i in range(len(self.header)) ))
                            self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
                            self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                            self.tableWidget.horizontalHeader().setStretchLastSection(True)                          

                            for k,f in enumerate(self.header):        
                                tableItem=QtWidgets.QTableWidgetItem(u"%s" % str(f))
                                tableItem.setFlags(tableItem.flags() ^ Qt.ItemIsEditable)
                                self.tableWidget.setItem(0,k,tableItem)

                        tableItem=QtWidgets.QTableWidgetItem(u"%s" % str(field))
                        tableItem.setFlags(tableItem.flags() ^ Qt.ItemIsEditable)
                        self.tableWidget.setItem(i,j,tableItem)
                if i>10:
                    break
        self.stretchTable(self.tableWidget)
        return len(self.dataNamesList)<=len(self.header)

    def stretchTable(self, table):            
            tableSize = table.width()
            sideHeaderWidth = table.verticalHeader().width()
            tableSize -= sideHeaderWidth
            numberOfColumns = table.columnCount()

            remainingWidth = tableSize % numberOfColumns
            for columnNum in range(table.columnCount()):
                if remainingWidth > 0:
                    table.setColumnWidth(columnNum, int(tableSize / numberOfColumns) + 1)
                    remainingWidth -= 1
                else:
                    table.setColumnWidth(columnNum, int(tableSize / numberOfColumns))

    def resizeEvent(self, event):
        self.stretchTable(self.tableWidget)
        super().resizeEvent(event)  # Restores the original behaviour of the resize event


def exportCsv(listaDeAlunos):
    '''
    listaDeAlunos: lista de Dicionários de alunos
    filename: Caminho do arquivo csv a salvar
    '''
    filename=QFileDialog.getSaveFileName(filter="Arquivo CSV (*.csv)")
    #filename=["/home/matheus/test.csv"]
    if not filename[0]: return

    header=list(listaDeAlunos[0].keys())    
    with open(filename[0], "w") as fo:
        writer = csv.writer(fo, delimiter=DELIMITADOR_CSV, dialect='excel')
        if type(header)==list:
            writer.writerow(header)
        for dic in listaDeAlunos:
            r=list(dic.values())
            writer.writerow(r)



def test1(*args):
    app = QtWidgets.QApplication(*args)
    app.restart=False
    d1={"nome":'majose', "matricula":"ER215", "dataNasc":'12/05/87', "RG":'askfasj1545', "CPF":'15618684',
      "nomeDaMae":'josefina', "nomeDoPai":'Jão', "telefone":'121839128', "endereco":'fksdkf 239j 29r',
 "serie":2, "escola":1, "idade":13, "lat":-19.231, "long":47.12331}
    d2={"nome":'matheus', "matricula":"ER128", "dataNasc":'17/05/87', "RG":'askfasj1545', "CPF":'15618684',
      "nomeDaMae":'josefina', "nomeDoPai":'Jão', "telefone":'121839128', "endereco":'fksdkf 239j 29r',
 "serie":5, "escola":1, "idade":21, "lat":-19.231, "long":47.12331}
    d3={"nome":'carlos', "matricula":"ER125", "dataNasc":'18/05/87', "RG":'askfasj1545', "CPF":'15618684',
      "nomeDaMae":'josefina', "nomeDoPai":'Jão', "telefone":'121839128', "endereco":'fksdkf 239j 29r',
 "serie":8, "escola":3, "idade":15, "lat":-19.231, "long":47.12331}
 
    exportCsv([d1,d2,d3])
    r=app.exec_()        
    return r


def test(*args):  
        app = QtWidgets.QApplication(*args)
        app.restart=False
        win=csvDialog(["nome", "idade", "x"], app)
        win.show()     
        r=app.exec_()        
        print(win.result)
        return r



if __name__ == '__main__':
    import sys
    currentExitCode=test1(sys.argv)
    sys.exit(currentExitCode)


'''class QtWaitingSpinner(QWidget):
    mColor = QtGui.QColor(Qt.gray)
    mRoundness = 100.0
    mMinimumTrailOpacity = 31.4159265358979323846
    mTrailFadePercentage = 50.0
    mRevolutionsPerSecond = 1.57079632679489661923
    mNumberOfLines = 20
    mLineLength = 10
    mLineWidth = 2
    mInnerRadius = 20
    mCurrentCounter = 0
    mIsSpinning = False

    def __init__(self, centerOnParent=True, disableParentWhenSpinning=True, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.mCenterOnParent = centerOnParent
        self.mDisableParentWhenSpinning = disableParentWhenSpinning
        self.initialize()

    def initialize(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.updateSize()
        self.updateTimer()
        self.hide()

    @pyqtSlot()
    def rotate(self):
        self.mCurrentCounter += 1
        if self.mCurrentCounter > self.numberOfLines():
            self.mCurrentCounter = 0
        self.update()

    def updateSize(self):
        size = (self.mInnerRadius + self.mLineLength) * 2
        self.setFixedSize(size, size)

    def updateTimer(self):
        self.timer.setInterval(1000 / (self.mNumberOfLines * self.mRevolutionsPerSecond))

    def updatePosition(self):
        if self.parentWidget() and self.mCenterOnParent:
            self.move(self.parentWidget().width() / 2 - self.width() / 2,
                      self.parentWidget().height() / 2 - self.height() / 2)

    def lineCountDistanceFromPrimary(self, current, primary, totalNrOfLines):
        distance = primary - current
        if distance < 0:
            distance += totalNrOfLines
        return distance

    def currentLineColor(self, countDistance, totalNrOfLines, trailFadePerc, minOpacity, color):
        if countDistance == 0:
            return color

        minAlphaF = minOpacity / 100.0

        distanceThreshold = ceil((totalNrOfLines - 1) * trailFadePerc / 100.0)
        if countDistance > distanceThreshold:
            color.setAlphaF(minAlphaF)

        else:
            alphaDiff = self.mColor.alphaF() - minAlphaF
            gradient = alphaDiff / distanceThreshold + 1.0
            resultAlpha = color.alphaF() - gradient * countDistance
            resultAlpha = min(1.0, max(0.0, resultAlpha))
            color.setAlphaF(resultAlpha)
        return color

    def paintEvent(self, event):
        self.updatePosition()
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.mCurrentCounter > self.mNumberOfLines:
            self.mCurrentCounter = 0
        painter.setPen(Qt.NoPen)

        for i in range(self.mNumberOfLines):
            painter.save()
            painter.translate(self.mInnerRadius + self.mLineLength,
                              self.mInnerRadius + self.mLineLength)
            rotateAngle = 360.0 * i / self.mNumberOfLines
            painter.rotate(rotateAngle)
            painter.translate(self.mInnerRadius, 0)
            distance = self.lineCountDistanceFromPrimary(i, self.mCurrentCounter,
                                                         self.mNumberOfLines)
            color = self.currentLineColor(distance, self.mNumberOfLines,
                                          self.mTrailFadePercentage, self.mMinimumTrailOpacity, self.mColor)
            painter.setBrush(color)
            painter.drawRoundedRect(QRect(0, -self.mLineWidth // 2, self.mLineLength, self.mLineLength),
                                    self.mRoundness, Qt.RelativeSize)
            painter.restore()

    def start(self):
        self.updatePosition()
        self.mIsSpinning = True
        self.show()

        if self.parentWidget() and self.mDisableParentWhenSpinning:
            self.parentWidget().setEnabled(False)

        if not self.timer.isActive():
            self.timer.start()
            self.mCurrentCounter = 0

    def stop(self):
        self.mIsSpinning = False
        self.hide()

        if self.parentWidget() and self.mDisableParentWhenSpinning:
            self.parentWidget().setEnabled(True)

        if self.timer.isActive():
            self.timer.stop()
            self.mCurrentCounter = 0

    def setNumberOfLines(self, lines):
        self.mNumberOfLines = lines
        self.updateTimer()

    def setLineLength(self, length):
        self.mLineLength = length
        self.updateSize()

    def setLineWidth(self, width):
        self.mLineWidth = width
        self.updateSize()

    def setInnerRadius(self, radius):
        self.mInnerRadius = radius
        self.updateSize()

    def color(self):
        return self.mColor

    def roundness(self):
        return self.mRoundness

    def minimumTrailOpacity(self):
        return self.mMinimumTrailOpacity

    def trailFadePercentage(self):
        return self.mTrailFadePercentage

    def revolutionsPersSecond(self):
        return self.mRevolutionsPerSecond

    def numberOfLines(self):
        return self.mNumberOfLines

    def lineLength(self):
        return self.mLineLength

    def lineWidth(self):
        return self.mLineWidth

    def innerRadius(self):
        return self.mInnerRadius

    def isSpinning(self):
        return self.mIsSpinning

    def setRoundness(self, roundness):
        self.mRoundness = min(0.0, max(100, roundness))

    def setColor(self, color):
        self.mColor = color

    def setRevolutionsPerSecond(self, revolutionsPerSecond):
        self.mRevolutionsPerSecond = revolutionsPerSecond
        self.updateTimer()

    def setTrailFadePercentage(self, trail):
        self.mTrailFadePercentage = trail

    def setMinimumTrailOpacity(self, minimumTrailOpacity):
        self.mMinimumTrailOpacity = minimumTrailOpacity

'''
if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    dial = QDialog()
    w = QtWaitingSpinner(dial)
    dial.show()
    w.start()
    QTimer.singleShot(1000, w.stop)
    sys.exit(app.exec_())