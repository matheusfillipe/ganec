import sqlite3
from pathlib import Path

class DB():
    def __init__(self, caminhoDoArquivo, tableName, dataNameList):    
            '''caminhoDoArquivo: String com o caminho do arquivo
               tableName: String com o nome da tabela
               dataNameList: Lista de strings com  os nomes de cada atributo
            '''
            self.filepath=caminhoDoArquivo
            self.tableName=tableName
            self.dataNameList=dataNameList
            self.checkIfExistsIfNotCreate()

    def toDict(self, data):        
            return {n : data[i] for i, n in enumerate(self.dataNameList)}
            
    def toList(self, data):
            return [data[n] for n in self.dataNameList]


    def checkIfExistsIfNotCreate(self):				
            self.connect()
            self.cursor.execute("CREATE TABLE IF NOT EXISTS " + self.tableName + 
                    " (id INTEGER primary key AUTOINCREMENT,"+ str(self.dataNameList)[1:-1] +")")
            self.close()
    
    def connect(self):
            self.connection = sqlite3.connect(self.filepath)
            self.cursor = self.connection.cursor()
            self.connected = True
    
    def close(self):
            self.connection.commit()
            self.connection.close()
            self.connected = False
    
    def _salvarDado(self, dado):
            self.cursor.execute("INSERT INTO "+self.tableName+" ("+str(self.dataNameList)[1:-1] +")VALUES (" + (len(self.dataNameList)*"?,")[:-1]+")", dado)		

    def salvarDado(self, dado):
            dado=self.toList(dado)
            assert len(dado)==len(self.dataNameList), "ERRO: O dado deve ter o tamanho " + str(len(self.dataNameList))
            self.connect()
            self._salvarDado(dado)
            self.close()

    def salvarDados(self, lista): 
            self.connect()
            [self._salvarDado(dado) for dado in lista]
            self.close()

    def _getDado(self, id):
            return self.toDict(list(list(self.cursor.execute("SELECT * FROM " + self.tableName + " WHERE id = ?", (id,)))[0])[1:])
                    
    def getDado(self, id):
            self.connect()
            dado=self._getDado(id)
            self.close()
            return dado
                    
    def acharDado(self, key, nome): 
            self.connect()					
            idList=[[list(dado)[0], self.toDict(list(dado)[1:])[key]] 
            for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName)) 
            if nome in self.toDict(list(dado)[1:])[key]]
            self.close()			
            return [x[0] for x in sorted(idList, key=lambda x: x[1])]

    def getDados(self, listaDeIds):
            return [self.getDado(id) for id in listaDeIds]
    
    def acharDados(self, key, nome):
            return sorted(self.getDados(self.acharDado(key, nome)), key=lambda x: x[key])


    def apagarDado(self, id):
            self.connect()
            self.cursor.execute("DELETE FROM "+ self.tableName +" WHERE ID = ?", (id,))		
            self.close()			

    def apagarTabela(self):
            self.connect()
            self.cursor.execute("DROP TABLE IF EXISTS "+ self.tableName)		
            self.close()			       

    def apagarTudo(self):	
            Path(self.filepath).unlink()