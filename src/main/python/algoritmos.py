import lib.constants
from sqlitedb import DB
from lib.osmNet import netHandler
from lib import constants
from pathlib import Path
import csv
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtCore 
from PyQt5.QtCore import pyqtSignal


# Nomes dos atributos:
IDADE='idade'
PASTA_ALUNOS='alunos'
SERIE='serie'
ESCOLA_SERIES='series'  #lista de modalidades ou séries separadas por virgula em formato string
COLORS=["blue", "green", "yellow", "red", "black"] #em ordem de proximidade
DB_FILEPATH='/home/matheus/test.db'
TABLE_ESCOLAS="escolas"
TABLE_SERIES="series"
SERIES_ATTR= ['idDaEscola' ,'serie' ,'vagas', 'nDeAlunos']
DELIMITADOR_CSV=';'


class calcularRotasThread(QtCore.QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)

    def run(self):
        count = 0
        db= DB(str(confPath() /Path(CAMINHO['escola'])), TABLE_NAME['escola'], ATRIBUTOS['escola'])

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
            self.countChanged.emit(int(count/len(tdodd)*100))
            alunoFolder=alunosFolder / aluno['id']
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
                saveFile=alunoFolder / Path(escola['id']+".geojson")            
                net.save_geojson(str(saveFile), COLORS[i if i < len(COLORS) else -1])

                if not count:
                    db=DB(DB_FILEPATH, TABLE_SERIES, SERIES_ATTR)
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
                

   

def test1():
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

def test2():
    pass



if __name__ == "__main__":
    test1()
