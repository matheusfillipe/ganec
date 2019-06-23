import persistent
import ZODB, ZODB.FileStorage
import transaction
from PyQt5.QtCore import pyqtSignal, QObject

class DbHandler():
    def __init__(self, location:str='', memory:bool=False):
        assert len(location) > 0 or memory == True
        self.location=location         
        self.memory=memory

    def create(self):
        if self.memory:
            self.db=ZODB.DB(None)
        else:
            self.storage = ZODB.FileStorage.FileStorage(self.location)
            self.db = ZODB.DB(self.storage)

        self.connection = self.db.open()
        self.root = self.connection.root 
        return self 
    
    def open(self):
        self.connection = ZODB.connection(None if self.memory else self.location)
        self.root = self.connection.root  
        return self 
       
    def save(self):
        transaction.commit()
        return self

class QPersistentList(QObject):
    updated=pyqtSignal()    
    def __init__(handler:DbHandler=DbHandler(memory=True)):
        QObject.__init__(self)
        self.index=0
        self.elements=[]
        self.db=handler
    def update(self):
        self.updated.emit()   
    def save(self, name:str):
        self.db        
    def next(self):
        self.index+=1
        return self.get()
    def previous(self):
        self.index-=1
        return self.get()
    def get(self,i=self.index):
        return self.elements[i]

#TEST
def test():
    from data import aluno,escola
    a=aluno.aluno("test")
    print(a.name)
    l=aluno.ListaAlunos([a])
    db=DbHandler("test.db")
    #db.create()
    db.open()
    print(db.root.alunos.alunos[0].name)
    #db.root.alunos=l
    #db.save()
