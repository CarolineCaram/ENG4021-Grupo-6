import sqlite3

# Cria o arquivo uniride.db com todas as tabelas do arquivo banco_sqlite.sql

arquivo = open("banco_sqlite.sql", "r")
script = arquivo.read()
arquivo.close()

conexao = sqlite3.connect("uniride.db")
conexao.executescript(script)
conexao.commit()
conexao.close()

print("Banco uniride.db criado com sucesso!")