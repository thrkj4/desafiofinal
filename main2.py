from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import csv
import io

app = Flask(__name__)
app.secret_key = "segredo_top"
CORS(app)

usuarios = {}
transacoes = {}  # {usuario: [ {tipo, valor, descricao} ] }


@app.post("/cadastro")
def cadastro():
    data = request.json
    usuario = data["usuario"]
    senha = data["senha"]

    if usuario in usuarios:
        return jsonify({"erro": "Usuário já existe"}), 400

    usuarios[usuario] = senha
    transacoes[usuario] = []
    return jsonify({"msg": "Cadastro realizado"})


@app.post("/login")
def login():
    data = request.json
    usuario = data["usuario"]
    senha = data["senha"]

    if usuario not in usuarios or usuarios[usuario] != senha:
        return jsonify({"erro": "Credenciais inválidas"}), 400

    session["usuario"] = usuario
    return jsonify({"msg": "Login OK"})


@app.post("/add")
def add_transacao():
    if "usuario" not in session:
        return jsonify({"erro": "Não logado"}), 401

    usuario = session["usuario"]
    data = request.json

    transacoes[usuario].append({
        "tipo": data["tipo"],
        "valor": data["valor"],
        "descricao": data["descricao"]
    })
    return jsonify({"msg": "Transação adicionada"})


@app.get("/listar")
def listar():
    if "usuario" not in session:
        return jsonify({"erro": "Não logado"}), 401

    usuario = session["usuario"]
    return jsonify(transacoes[usuario])


@app.get("/exportar")
def exportar():
    if "usuario" not in session:
        return jsonify({"erro": "Não logado"}), 401

    usuario = session["usuario"]
    dados = transacoes[usuario]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["tipo", "valor", "descricao"])
    writer.writeheader()
    writer.writerows(dados)

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="dados_financeiros.csv"
    )


@app.get("/logout")
def logout():
    session.pop("usuario", None)
    return jsonify({"msg": "Saiu"})


if __name__ == "__main__":
    app.run(debug=True)
