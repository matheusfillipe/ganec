import sqlite3

import datetime
import persistent
from lib.constants import *
from lib.hidden.constants import API_KEY

from lib.osm import MapWidget
from lib.gmaps import *

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

class Aluno(persistent.Persistent):
    def __init__(self, name="", dataDeNascimento=None, rua="", numero="", bairro="",complemento="", matricula="", additional="", nomePai="", nomeMae="", RG = "", CPF = "", telefone = "", serie = -1):
        self.name=name    
        self.dataDeNascimento=dataDeNascimento
        self.rua=rua
        self.numero=numero
        self.bairro=bairro
        self.complemento=complemento
        self.RG=RG
        self.CPF=CPF
        self.telefone=telefone
        self.complemento=complemento
        self.matricula=matricula
        self.nomePai=nomePai
        self.nomeMae=nomeMae
        self.serie=serie

class definirEscola(persistent.Persistent):

    def __init__(self, dados=[]):
        self.dados=dados
        self.salvarDados()
    
    def salvarDados(self):

        DADOS = self.dados
        lista = []
        dadosSalvos = sqlite3.connect("dadosAlunos.db")
        cursor = dadosSalvos.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS dados (matricula text, nome text, dataNasc text, RG text, CPF text, nomeDaMae text, nomeDoPai text, telefone text, endereco text, serie int, escola int, lat doble, long doble, Id int)""")

        IdAluno = 1
        j = 0
        ids = []

        for i in cursor.execute("SELECT rowid, * FROM dados ORDER BY Id"):
            ids.append(i[14])
            j += 1
        
        podeIr = True
        while IdAluno <= j and podeIr:
                for i in ids:
                    print(ids)
                    if i == IdAluno:
                        IdAluno+=1
                    else:
                        podeIr = False

        coordenadas_ = GeoCoder().geocode(DADOS[8], API_KEY)

        #print(numero)

        DADOS.append(self.definirEscola())

        DADOS.append(coordenadas_[0])
        DADOS.append(coordenadas_[1])       

        DADOS.append(IdAluno)

        # insere múltiplos registros de uma só vez usando o método "?", que é mais seguro
        cursor.executemany("INSERT INTO dados VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [DADOS])
        dadosSalvos.commit()

        #apenas para testes
        #print("\nAqui a lista de todos os registros na tabela:\n")
        for row in cursor.execute("SELECT rowid, * FROM dados ORDER BY nome"):
            #print(row)
            lista.append(row)

        dadosSalvos.close()

        return lista
    
    def definirEscolas(self):

        EnderecoAluno = self.dados[8]
        escola = 6

        #encontrar a escola mais próxima
        '''_aqui_'''
        return escola

class manipularDB(persistent.Persistent):
    def __init__(self, stringDados):
        self.dados = stringDados

        self.dados = self.dados.replace("Nome: ","")
        self.dados = self.dados.replace("  - Matrícula: ","´")
        self.dados = self.dados.replace("\n","´")
        self.dados = self.dados.replace("Data de Nascimento: ","´")
        self.dados = self.dados.replace("RG: ","´")
        self.dados = self.dados.replace("  - CPF: ","´")
        self.dados = self.dados.replace("Mãe: ","´")
        self.dados = self.dados.replace("  - Pai: ","´")
        self.dados = self.dados.replace("Telefone: ","´")
        self.dados = self.dados.replace("Endereço: ","´")
        self.dados = self.dados.replace("ID: ","´")
        self.dados = self.dados.replace("Escola: ","´")
        self.dados = self.dados.split("´")

        print(self.dados)

        self.ID = self.dados[18]
    
    def setarAluno(self):

        dadosSalvos = sqlite3.connect("dadosAlunos.db")
        cursor = dadosSalvos.cursor()

        lista = []
        row = 0
        lista_ = []

        for i in cursor.execute("SELECT rowid, * FROM dados ORDER BY nome"):
            lista.append(i)
            
            nasc = lista[row][3].split()
            nascimento = nasc[2] + "/" + nasc[1] + "/" + nasc[3]

            if lista[row][14] == int(self.ID):
                lista_.append(lista[row][2])
                lista_.append(lista[row][1])
                lista_.append(lista[row][4])
                lista_.append(lista[row][5])
                lista_.append(lista[row][6])
                lista_.append(lista[row][7])
                lista_.append(lista[row][8])
                lista_.append(lista[row][9])
                lista_.append(lista[row][10])
                lista_.append(nascimento)
                lista_.append(self.ID)
            row = row + 1

        dadosSalvos.close()

        return lista_
    
    def editarAluno(self, DADOS): #Retorna 1 se tudo ok, 2 se o indereço está errado

        dadosSalvos = sqlite3.connect("dadosAlunos.db")
        cursor = dadosSalvos.cursor()

        if DADOS[7] != "":
            coordenadas_ = GeoCoder().geocode(DADOS[7], API_KEY)

            #encontrar a escola mais próxima
            '''_aqui_'''

            escola = 6

            cursor.execute("""UPDATE dados SET nome = ?, matricula = ?, RG = ?, CPF = ?, nomeDaMae = ?, nomeDoPai = ?, telefone = ?, endereco = ?, serie = ?, escola = ? , lat = ?, long = ? WHERE ID = ? """, (DADOS[0], DADOS[1], DADOS[2], DADOS[3], DADOS[4], DADOS[5], DADOS[6], DADOS[7], int(DADOS[8]), escola, coordenadas_[0], coordenadas_[1], self.ID))
            dadosSalvos.commit()
            dadosSalvos.close()

        else:

            dadosSalvos.close()
            return 2

        return 1

    def excluirAluno(self):

        dadosSalvos = sqlite3.connect("dadosAlunos.db")
        cursor = dadosSalvos.cursor()

        cursor.execute("""DELETE FROM dados WHERE ID = ?""", (self.ID,))

        dadosSalvos.commit()
        dadosSalvos.close()

        return True

class buscaAvancadaAluno(persistent.Persistent):
    def __init__(self, busca):

        self.buscar = busca
    
    def buscando(self):

        #matricula, nome, dataNasc , RG , CPF , nomeDaMae , nomeDoPai , telefone , endereco , serie , escola , lat , long , Id int
        dadosSalvos = sqlite3.connect("dadosAlunos.db")
        cursor = dadosSalvos.cursor()
        
        def buscar(self, buscar):
            busca = self.buscar
            if buscar[0].count(busca) > 0 :#or buscar[1].count(busca) > 0 or buscar[3].count(busca) > 0 or buscar[4].count(busca) > 0 or buscar[5].count(busca) > 0 or buscar[6].count(busca) > 0 or buscar[7].count(busca) > 0 or buscar[8].count(busca) > 0 or listaDeSeries[buscar[9]].count(busca) > 0 or str(buscar[14]).count(busca) > 0:
                return True
            else:
                return False
        
        lista=[]

        for row in cursor.execute("SELECT rowid, * FROM dados ORDER BY nome"):
            lista.append(row)

        lista_valida = list(filter(buscar, lista))

        print(lista_valida)

        dadosSalvos.close()

        return lista_valida










    


 

       