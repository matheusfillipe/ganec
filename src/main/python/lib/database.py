import ZODB, ZODB.FileStorage,  BTrees.OOBTree, BTrees.OOBTree, transaction
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QShortcut
from copy import deepcopy
from pathlib import Path
import shutil
import pathlib
import os  
from lib.constants import NAME


class DbHandler():
    def __init__(self, location:Path='', memory:bool=False):
        assert len(str(location.absolute())) > 0 or memory == True
        self.location=location         
        self.memory=memory

    def create(self):
        print("creating "+str(self.location))
        self.location.mkdir(parents=True, exist_ok=True)            
        if self.memory:
            self.db=ZODB.DB(None)
        else:
            self.storage = ZODB.FileStorage.FileStorage(str((self.location / "data").absolute()))
            self.db = ZODB.DB(self.storage)

        self.connection = self.db.open()
        self.root = self.connection.root 
        return self 
    
    def open(self):
        self.connection = ZODB.connection(None if self.memory else str((self.location / "data").absolute()))
        self.root = self.connection.root  
        return self 
    
    def clean(self):
        shutil.rmtree(self.location)
       
    def save(self):
        transaction.commit()
        return self




class QInterface(QObject):
    
    updated=pyqtSignal() #sinais   
    changed=pyqtSignal() #em relação ao estado anterior da interface
    notModified=pyqtSignal()#em relação ao banco de dados
    modified=pyqtSignal()

    def __init__(self, data, varManager, name:str, child=False):
        '''
        data: Instância de uma subclasse de persistent.Persistent que funciona como primeiro valor no stack (elements)
        
        varManager:

        name: Key para zodb database, nomes iguais irão se sobreescrever!

        child: Attributo

        sinais emitidos quando:
            updated --> quando qualquer sinal definido em signals pelo método setup ou define é emitido
            changed --> quando o estado da interface muda
            notModified --> quando o estado da interface muda para um igual do que se encontra no banco de dados
            modified --> interface mudou e é diferente do banco de dados
        '''
        QObject.__init__(self)
        self.child=child
        self.data=data
        self.name=name
        self.varManager=varManager
        self.index=0
        self.elements=[]
        self.defined=False
        self.elements.append(data)
        self.wasModified=False


    def setup(self, iface, signals=[], slots=[], properties=[], readers=[], writers=[]):
        '''
        signals: lista de pyqt signals com mesmo tamanho que slots, relacionados 1 a 1, para serem associados em ordem ex: button.pushed

        slots: lista de pyqt slots, ex: qualquer funcao

        properties: lista de strings de nomes das propriedades relacionadas 1 a 1 a cada elemento da readers ex: "nome" para data.nome, "idade" para data.idade...

        readers: lista de métodos (bound method), que não devem necessitar de argumentos, que retornam as propriedades ex: qlineedit.text (pode ser definida com lambda?)

        writers: lista de métodos (bound method), que devem necessitar de um único argumento, para setar pontos desejados da readers gráfica ex: qlinedit.setText

        Observe que os elementos de properties, interfaces e wrirters devem estar todos associados 1 a 1 entre si
        properties, readers e writers são obrigatórias para definir a readers para que os métodos read e write funcionem
        Não coloque parenteses nos writers e properties list!  

        SUGGESTED LAYOUT
        
           \t     self,  
           \t     signals =  [],
           \t     slots   =  [],
           \t     properties=[],
           \t     readers  = [],
           \t     writers  = [] 

           OR SIMPLY

           \t     self,  
           \t     properties=[],
           \t     readers  = [],
           \t     writers  = []               
        '''
        self.define(signals=signals,slots=slots,properties=properties,readers=readers,writers=writers)
        self.bindUndoRedo(iface)
        self.write()  

    def define(self, signals=[], slots=[], properties=[], readers=[], writers=[]):
        '''
        signals: lista de pyqt sinais com mesmo tamanho que slots, relacionados 1 a 1, para serem associados em ordem ex: button.pushed

        slots: lista de pyqt slots, ex: qualquer funcao

        properties: lista de strings de nomes das propriedades relacionadas 1 a 1 a cada elemento da readers ex: "nome" para data.nome, "idade" para data.idade...

        readers: lista de métodos (bound method), que não devem necessitar de argumentos, que retornam as propriedades ex: qlineedit.text (pode ser definida com lambda?)

        writers: lista de métodos (bound method), que devem necessitar de um único argumento, para setar pontos desejados da readers gráfica ex: qlinedit.setText

        Observe que os elementos de properties, interfaces e wrirters devem estar todos associados 1 a 1 entre si
        properties, readers e writers são obrigatórias para definir a readers para que os métodos read e write funcionem
        Não coloque parenteses nos writers e properties list!

        SUGGESTED LAYOUT
        
           \t     self,  
           \t     signals =  [],
           \t     slots   =  [],
           \t     properties=[],
           \t     readers  = [],
           \t     writers  = [] 

           OR SIMPLY

           \t     self,  
           \t     properties=[],
           \t     readers  = [],
           \t     writers  = []               

        '''
        if signals and slots:
            assert len(signals) == len(slots), "Os tamanhos das listas devem ser os mesmos"
            self.signals=signals
            self.slots=slots
            for signal, slot in zip(signals, slots):
                signal.connect(slot)
                signal.connect(self.update)
        if properties:                
            assert len(properties) == len(readers) and len (readers) == len(writers), "Os tamanhos das listas devem ser os mesmos"
            self.properties=properties
            self.interfaces=readers
            self.writers=writers
            self.defined=True

    def addSignal(self, signal, slot):
        '''
        adds a signal and corresponding slot
        The interface has to be defined        
        '''
        assert self.defined, "Interface deve ser definida pelo método setup ou define "
        self.signals.append(signal)
        self.slots.append(slots)
        signal.connect(slot)
        signal.connect(self.update)

    def addProperty(self, propertie:str, reader, writer):
        '''
        adds a property
        The interface has to be defined
        '''
        assert self.defined, "Interface deve ser definida pelo método setup ou define"       
        self.properties.append(propertie)
        self.interfaces.append(reader)
        self.writers.append(writer)       
    

    def disconectAll(self):
        if self.signals:
            for signal, slot in zip(self.signals, self.slots):
                signal.disconnect(slot)
                signal.disconnect(self.update)

    def read(self):
        '''
        Lê da interface se o método define já tiver sido usado com properties e readers não nulos
        retorna se há mudanças e adiciona-as ao stack (elements)  
        Popula o stack (append) com o novo data
        '''
        if self.defined:
            data=deepcopy(self.get())
            different=False
            for propertie, reader in zip(self.properties,self.interfaces):
                setattr(data,propertie,reader())
                if getattr(data,propertie)!=getattr(self.get(),propertie):
                    different=True 
            if different:
                self.append(data)
            return different
        return False    

    def write(self):
        '''
        Lê a ultima data no stack e preenche a readers com ela
        retorna se há diferenças        
        '''
        if self.defined:
            data=self.get()
            different=False
            for propertie, writer, reader in zip(self.properties,self.writers, self.interfaces):
                if getattr(data,propertie)!=reader():
                    writer.__self__.blockSignals(True)
                    writer(getattr(data,propertie))
                    different=True 
                    writer.__self__.blockSignals(False)
            return different           
        else:            
            return False

    def append(self, data):
        assert type(data)==type(self.get()), "Tried to add a different data format than initial!"
        if self.index==len(self.elements)-1:
            self.elements.append(deepcopy(data)) 
        else:
            self.dischart(self.index)
            self.elements.append(deepcopy(data))
        self.index+=1

    def prepend(self, data):
        assert type(data)==type(self.get()), "Tried to add a different data format than initial!"
        self.elements.insert(0,deepcopy(data))

    def dischart(self, index):
        '''
        index: índice do ultimo elemento a ser mantido
        '''
        self.elements=self.elements[0:index+1]     

    
    def update(self): 
        changed=self.read()
        if changed:
            self.changed.emit()
        dbData=self.varManager.read(self.data,self.name).get() if not self.child else self.data
        if str(type(dbData.__eq__))=="<class 'method'>":
            if self.get()==dbData:
                self.notModified.emit()
                self.wasModified=False
            else:
                self.wasModified=True               
        else:
            if self.get().__dict__ == dbData.__dict__ and self.defined:
                self.notModified.emit()
                self.wasModified=False
            else:
                self.wasModified=True
        if self.wasModified and changed:
            self.modified.emit()
        self.updated.emit()   


    def save(self, name:str=None):
        '''
        saves object to database
        '''
        if self.child and name is None:
            self.data.__dict__=self.get().__dict__
            self.varManager.db.save()            
        else:
            if name is None:
                name=self.name                  
            self.varManager.write(self.get(),self.name)                                             


    def next(self):
        '''
        switches to next element on stack (elements)
        returns data
        '''
        self.index+=1 if self.index<len(self.elements)-1 else 0
        self.write()        
        return self.get()

    def previous(self):
        '''
        switches to previous element on stack (elements)
        returns data
        '''
        self.index-=1 if self.index > 0 else 0
        self.write()
        return self.get()

    def getNext(self):
        '''
        returns next data
        '''
        i=self.index + (1 if self.index<len(self.elements)-1 else 0)
        return self.get(i)

    def getPrevious(self):
        '''
        returns previous data
        '''
        i=self.index - (1 if self.index > 0 else 0)
        return self.get(i)


    def get(self,i=None):
        '''
        returns data
        if i is not set, the active element will be returned, which means the last on the stack (elements)
        '''
        if i:
            return self.elements[i]
        else:
            return self.elements[self.index]
    
    def getChild(self, data):
        '''
        returns the corresponding qinterface for a specific data's object attribute        
        '''
        assert self.child==False, "Childs só podem ser criados de interfaces primárias"
        return QInterface(data, self.varManager, self.name, child=data)


    def bindUndoRedo(self, iface:QWidget):
        '''
        iface: parent QWidget
        Ctrl+z e ctrl+shift+z (undo/redo)
        '''
        iface.undoShortcut=QShortcut(QKeySequence("Ctrl+Z"), iface)
        iface.redoShortcut=QShortcut(QKeySequence("Ctrl+Shift+Z"), iface)
        iface.undoShortcut.activated.connect(self.previous)
        iface.redoShortcut.activated.connect(self.next)

    def unBindUndoRedo(self, iface:QWidget):
        '''
        iface: parent QWidget
        unbinds Ctrl+z e ctrl+shift+z (undo/redo)
        '''
        if hasattr(iface,"undoShortcut"):
            iface.undoShortcut.activated.disconnect(self.previous)
        if hasattr(iface,"redoShortcut"):
            iface.redoShortcut.activated.disconnect(self.next)


    def customSlot(self, method:str, *args):
        '''
        Used for binding signals to data slots for the most recent data on the stack (elements) or running methods on the last one
        method: string name of the method
        args: used to pass arguments
        '''
        func=getattr(self.get(), method)
        assert callable(func), "string method should be a data object's callable!"
        if len(args) == 0:
            func()
        else:
            func(args)

     
     
class VariableManager():
    def __init__(self,cfgDir:str):
        '''
        arguments: Config folder path
        '''
        dbFolder=Path(cfgDir+"/GANEC")
        db=DbHandler(dbFolder)
        self.db=db

        if dbFolder.exists():
            db.open()
        else:
            db.create()
        if not hasattr(db.root, 'main'):
            db.root.main=BTrees.OOBTree.BTree()
        self.root=db.root


    def read(self, obj:object, key:str):
        if key in self.root.main and type(self.root.main[key])==type(obj):
            qinterface=QInterface(self.root.main[key], self, key)
            for attr in obj.__dict__:
                if not hasattr(qinterface.get(),attr):
                    setattr(qinterface.get(),attr,getattr(obj,attr))
            return qinterface
        else:
            self.root.main[key]=obj
            return QInterface(self.root.main[key], self, key)
    
    def write(self, obj:object, key:str):
        self.root.main[key]=obj
        self.db.save()

    def removeDatabase(self):
        self.db.clean()
        

