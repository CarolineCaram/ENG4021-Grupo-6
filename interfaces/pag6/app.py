import os
import sqlite3
import flask
import werkzeug.security

# static_url_path="" faz o style.css, login.js etc. serem acessados direto na raiz
app = flask.Flask(__name__, static_folder="static", static_url_path="")

# Chave usada para assinar o cookie de sessão. Troque por algo grande e secreto.
app.secret_key = "troque-esta-chave-por-uma-bem-grande-e-secreta"

# Caminho do arquivo do banco (fica na mesma pasta do app.py)
pasta_do_projeto = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(pasta_do_projeto, "uniride.db")


def conectar():
    conexao = sqlite3.connect(caminho_banco)
    # Liga a verificação das chaves estrangeiras (no SQLite vem desligada)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


@app.route("/")
def pagina_login():
    return app.send_static_file("index.html")


@app.route("/login", methods=["POST"])
def login():
    dados = flask.request.get_json()

    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")

    if email == "" or senha == "":
        return flask.jsonify({"ok": False, "erro": "Preencha o e-mail e a senha."}), 400

    # Busca o usuário no banco pelo e-mail
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT id_usuario, nome, senha FROM usuario WHERE LOWER(email) = ?",
        (email,)
    )
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()

    # Mesma mensagem para e-mail inexistente e senha errada (não revela qual deu errado)
    mensagem_erro = "E-mail ou senha incorretos."

    if usuario is None:
        return flask.jsonify({"ok": False, "erro": mensagem_erro}), 401

    id_usuario = usuario[0]
    nome = usuario[1]
    senha_hash = usuario[2]

    senha_correta = werkzeug.security.check_password_hash(senha_hash, senha)
    if senha_correta == False:
        return flask.jsonify({"ok": False, "erro": mensagem_erro}), 401

    # Login certo: guarda na sessão quem está logado
    flask.session["id_usuario"] = id_usuario
    flask.session["nome"] = nome

    return flask.jsonify({"ok": True})


@app.route("/me")
def me():
    if "id_usuario" not in flask.session:
        return flask.jsonify({"logado": False}), 401

    return flask.jsonify({
        "logado": True,
        "id_usuario": flask.session["id_usuario"],
        "nome": flask.session["nome"]
    })


@app.route("/logout", methods=["POST"])
def logout():
    flask.session.clear()
    return flask.jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)