import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Importa toda a lógica compartilhada do core
from core import (
    client, inicializar_banco, carregar_historico, salvar_historico,
    carregar_estado, salvar_estado, construir_system, comprimir_historico,
    registrar_sessao, LIMITE_TROCAS
)

app = Flask(__name__)
app.secret_key = os.environ.get("NEO_SECRET_KEY", "dev-only-secret")

limiter = Limiter(get_remote_address, app=app, default_limits=[])


@app.errorhandler(429)
def rate_limit_exceeded(_):
    return jsonify({"erro": "Limite de mensagens atingido. Aguarde um momento."}), 429


@app.before_request
def verificar_autenticacao():
    if request.endpoint in (None, "static", "login"):
        return
    if not session.get("autenticado"):
        if request.is_json:
            return jsonify({"erro": "Não autorizado"}), 401
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha == os.environ.get("NEO_PASSWORD", ""):
            session["autenticado"] = True
            return redirect(url_for("index"))
        erro = "Senha incorreta."
    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --- Inicialização ---

# Garante que o banco e as tabelas existem antes de qualquer requisição
inicializar_banco()

# Carrega o estado do banco e atualiza a última abertura
estado = carregar_estado()
estado["ultima_abertura"] = datetime.now().isoformat()
salvar_estado(estado)



# Serve a página de chat ao acessar o servidor no navegador
@app.route("/")
def index():
    return render_template("index.html")


# Rota principal do agente. Recebe uma mensagem via POST e devolve a resposta.
# Corpo esperado: { "mensagem": "texto do usuário" }
# Resposta:       { "resposta": "texto do agente" }
@app.route("/chat", methods=["POST"])
@limiter.limit("20 per minute")
def chat():
    data = request.get_json()

    # Valida que o corpo da requisição existe e contém o campo mensagem
    if not data or "mensagem" not in data:
        return jsonify({"erro": "Campo 'mensagem' obrigatório"}), 400

    mensagem = data["mensagem"].strip()
    if not mensagem:
        return jsonify({"erro": "Mensagem não pode ser vazia"}), 400

    # Reconstrói o system prompt a cada requisição para refletir o bloco atual
    # do dia, ausência recente e estatísticas de sessões sempre atualizadas
    estado_atual = carregar_estado()
    system = construir_system(estado_atual)

    # Carrega o histórico atualizado do banco a cada requisição,
    # garantindo que múltiplos clientes vejam sempre o estado mais recente
    historico = carregar_historico()
    historico.append({"role": "user", "content": mensagem})

    # Chama a API sem streaming — o servidor espera a resposta completa
    # antes de devolver o JSON. Streaming via HTTP exigiria SSE ou WebSocket.
    resposta_msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=system,
        messages=historico
    )
    resposta = resposta_msg.content[0].text

    # Adiciona a resposta ao histórico e comprime se necessário
    historico.append({"role": "assistant", "content": resposta})
    if len(historico) >= LIMITE_TROCAS * 2:
        historico = comprimir_historico(historico)

    salvar_historico(historico)

    return jsonify({"resposta": resposta})


@app.route("/encerrar", methods=["POST"])
def encerrar():
    data = request.get_json()
    estudado = (data or {}).get("estudado", "").strip()
    if not estudado:
        return jsonify({"erro": "Campo 'estudado' obrigatório"}), 400
    registrar_sessao(estudado)
    session.clear()
    return jsonify({"ok": True})


if __name__ == "__main__":
    # debug=True reinicia o servidor automaticamente ao salvar o arquivo
    app.run(debug=True)

