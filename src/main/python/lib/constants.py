#PROJETO LEVEL

NAME="GANEC"
UI_FILES_PATH="./src/main/python/ui/"
CONF_PATH=''

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

#CONSTANTED DB

CAMINHO = {'aluno':"aluno.db", 'escola':"escola.db"}

TABLE_NAME = {'aluno':"ALUNOS", 'escola':"ESCOLAS"}

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
		  "modalidade", 
		  "lat",
		   "long",
			"series"],

		'modalidade':[],
		
		'series':['idDaEscola',
			  'serie', 
			  'vagas', 
			  'nDeAlunos']
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

#usado para definir todas as séries que existem. E assim alocar cada aluno numa escola em que a série que ele está existe;

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


listaDeModalidades  = ["Ensino Infantil",
						"Ensino Fundamental", 
						"Ensino Médio",  
						"INDEFINIDO"]

cidade = "Carmo Do Paranaíba"

#Transformar data de meses jul, jun, etc em numero:

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

#IMPORTS

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
