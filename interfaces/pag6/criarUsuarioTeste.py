import sqlite3
import werkzeug.security

# Cria (ou atualiza) um usuário de teste com a senha já criptografada.
# E-mail: teste@email.com   Senha: 123456

senha_hash = werkzeug.security.generate_password_hash("123456")

conexao = sqlite3.connect("uniride.db")
cursor = conexao.cursor()

cursor.execute(
    "INSERT INTO usuario (nome, email, matricula, senha) "
    "VALUES (?, ?, ?, ?) "
    "ON CONFLICT(email) DO UPDATE SET senha = excluded.senha",
    ("Usuário Teste", "teste@email.com", "0000000", senha_hash)
)

conexao.commit()
cursor.close()
conexao.close()

print("Usuário de teste criado: teste@email.com / 123456")