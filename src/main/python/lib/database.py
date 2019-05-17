import persistent
import ZODB, ZODB.FileStorage
import account, BTrees.OOBTree

class listaEscolas(persistent.Persistent):
    def __init__(self, item):
        self.escolas=item
 
class listaAlunos(persistent.Persistent):
    def __init__(self, item):
        self.escolas=item

class dbHandler():
    def __init__(self, location:str):
        pass

    def create():
        self.storage = ZODB.FileStorage.FileStorage(self.location)
        self.db = ZODB.DB(self.storage)
        self.connection = self.db.open()
        self.root = self.connection.root


    def save(self):
        self.root.accounts = BTrees.OOBTree.BTree()
        self.root.accounts['account-1'] = Account()