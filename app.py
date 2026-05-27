from flask import Flask, render_template, request, jsonify, redirect
import sqlite3

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user
)

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "devcrm_super_secreto_2026"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Usuario(UserMixin):
    def __init__(self, id, nome, email):
        self.id = str(id)
        self.nome = nome
        self.email = email


def conectar():
    return sqlite3.connect("database.db")


@login_manager.user_loader
def carregar_usuario(user_id):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
    SELECT id, nome, email
    FROM usuarios
    WHERE id = ?
    """, (user_id,))

    usuario = cursor.fetchone()
    banco.close()

    if usuario:
        return Usuario(usuario[0], usuario[1], usuario[2])

    return None


def criar_banco():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tarefas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        dificuldade TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)

    banco.commit()
    banco.close()


@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/roadmaps")
@login_required
def roadmaps():
    return render_template("roadmaps.html")


@app.route("/projetos")
@login_required
def projetos():
    return render_template("projetos.html")


@app.route("/revisoes")
@login_required
def revisoes():
    return render_template("revisoes.html")


@app.route("/ia")
@login_required
def ia():
    return render_template("ia.html")


@app.route("/configuracoes")
@login_required
def configuracoes():
    return render_template("configuracoes.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
        SELECT id, nome, email, senha
        FROM usuarios
        WHERE email = ?
        """, (email,))

        usuario = cursor.fetchone()
        banco.close()

        if usuario and check_password_hash(usuario[3], senha):
            user = Usuario(usuario[0], usuario[1], usuario[2])
            login_user(user)
            return redirect("/")

        return "Email ou senha incorretos"

    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        senha_criptografada = generate_password_hash(senha)

        banco = conectar()
        cursor = banco.cursor()

        try:
            cursor.execute("""
            INSERT INTO usuarios (nome, email, senha)
            VALUES (?, ?, ?)
            """, (nome, email, senha_criptografada))

            banco.commit()
            banco.close()

            return redirect("/login")

        except:
            banco.close()
            return "Esse email já está cadastrado"

    return render_template("cadastro.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/tarefas", methods=["GET"])
@login_required
def listar_tarefas():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
    SELECT id, nome, categoria, dificuldade, status
    FROM tarefas
    """)

    tarefas = cursor.fetchall()
    banco.close()

    return jsonify([
        {
            "id": t[0],
            "nome": t[1],
            "categoria": t[2],
            "dificuldade": t[3],
            "status": t[4]
        }
        for t in tarefas
    ])


@app.route("/tarefas", methods=["POST"])
@login_required
def criar_tarefa():
    dados = request.json

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
    INSERT INTO tarefas (nome, categoria, dificuldade, status)
    VALUES (?, ?, ?, ?)
    """, (
        dados["nome"],
        dados["categoria"],
        dados["dificuldade"],
        "backlog"
    ))

    banco.commit()
    banco.close()

    return jsonify({"mensagem": "Tarefa criada"})


@app.route("/tarefas/<int:id>", methods=["PUT"])
@login_required
def atualizar_tarefa(id):
    dados = request.json

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
    UPDATE tarefas
    SET status = ?
    WHERE id = ?
    """, (dados["status"], id))

    banco.commit()
    banco.close()

    return jsonify({"mensagem": "Tarefa atualizada"})


@app.route("/tarefas/<int:id>", methods=["DELETE"])
@login_required
def excluir_tarefa(id):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
    DELETE FROM tarefas
    WHERE id = ?
    """, (id,))

    banco.commit()
    banco.close()

    return jsonify({"mensagem": "Tarefa excluída"})


if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)