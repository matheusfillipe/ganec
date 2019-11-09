#PROJETO LEVEL

NAME="ZONEA"
UI_FILES_PATH="./src/main/python/ui/"
CONF_PATH=''
BASEPATHS=["./src/main/resources/base/", "./"]

#UI CONSTANTS

UI_FILTER1=["Alunos", "Escolas"]
UI_FILTER2_ALUNO=["Nome", "Endereço", "Matrícula", "Escola", "Idade", "Modalidade", "Turma"]
UI_FILTER2_ESCOLA=["Nome", "Endereço", "Modalidade", "Turma", "Idade"]
UI_ORDEM=["Crescente", "Decrescente"]


#DATABASE STRINGS

DB_CONFIG="config"
DB_ALUNO_TEMP="sfdlkjhjset75"
DB_MODALIDADES_BASE="modalidades_base"
DB_ADD_ALUNO="alunos"
DB_ADD_ESCOLA="escolas"


#CONSTANTES DB

CAMINHO = {'aluno':"aluno.db", 'escola':"escola.db", 'strings':'strings.db', 'ano':"ano.db"}
TABLE_NAME = {'aluno':"ALUNOS", 'escola':"ESCOLAS", 'series':'SERIES', 'ano':'ANO'}

ATRIBUTOS = {
	'aluno':["nome",
			 "matricula", 
			 "dataNasc", 
			 "RG", 
			 "CPF", 
			 "nomeDaMae", 
			 "nomeDoPai", 
			 "telefone", 
			 "endereco", 
			 "serie", 
			 "escola", 
			 "idade", 
			 "lat", 
			 "long"],

		'escola':["nome",
				 "endereco" ,
		  		 "lat",
		   		 "long",
				 "series"],

		'modalidade':[],
		
		'series':['idDaEscola',
			  'serie', 
			  'vagas', 
			  'nDeAlunos'],
		
		'ano':['ano']
}

ATRIBUTOS_STRING = {
	'aluno':["Buscar por:", 
			 "Nome", 
			 "Matrícula", 
			 "Data de Nascimento", 
			 "RG", 
			 "CPF", 
			 "Nome da Mãe", 
			 "Nome do Pai", 
			 "Telefone", 
			 "Endereço"],

	'escola':["Buscar por:", 
			  "Nome",
			  "Endereco", 
			  "Series"],

	'modalidade':["Buscar por:"],

	'series':["Buscar por:"]
}

SEPARADOR_SERIES = ","
CSV_SEPARATOR=","

#UTILS

dataEmNumero = {
	'jan':1,
	'fev':2,
	'mar':3,
	'abr':4,
	'mai':5,
	'jun':6,
	'jul':7,
	'ago':8,
	'set':9,
	'out':10,
	'nov':11,
	'dez':12
}

#CSV DATA IMPORTS

CSV_ALUNOS=["nome",
			 "matricula", 
			 "dataNasc", 
			 "RG", 
			 "CPF", 
			 "nomeDaMae", 
			 "nomeDoPai", 
			 "telefone", 
			 "endereco", 
			 "serie"
             ]

CSV_ESCOLAS=['nome', 'endereco', 'series']
