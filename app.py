from flask import Flask, request, jsonify, render_template
from datetime import datetime

# Importa toda a lógica compartilhada do core
from core import (
    client, inicializar_banco, carregar_historico, salvar_historico,
    carregar_estado, salvar_estado, construir_system, comprimir_historico,
    LIMITE_TROCAS
)

app = Flask(__name__)

# --- Inicialização ---

# Garante que o banco e as tabelas existem antes de qualquer requisição
inicializar_banco()

# Carrega o estado do banco e atualiza a última abertura
estado = carregar_estado()
estado["ultima_abertura"] = datetime.now().isoformat()
salvar_estado(estado)

# Constrói o system prompt uma vez ao subir o servidor.
# Se quiser que ele se atualize a cada requisição (ex: bloco do dia muda),
# basta mover construir_system(estado) para dentro da rota /chat.
system = construir_system(estado)


# Serve a página de chat ao acessar o servidor no navegador
@app.route("/")
def index():
    return render_template("index.html")


# Rota principal do agente. Recebe uma mensagem via POST e devolve a resposta.
# Corpo esperado: { "mensagem": "texto do usuário" }
# Resposta:       { "resposta": "texto do agente" }
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    # Valida que o corpo da requisição existe e contém o campo mensagem
    if not data or "mensagem" not in data:
        return jsonify({"erro": "Campo 'mensagem' obrigatório"}), 400

    mensagem = data["mensagem"].strip()
    if not mensagem:
        return jsonify({"erro": "Mensagem não pode ser vazia"}), 400

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


if __name__ == "__main__":
    # debug=True reinicia o servidor automaticamente ao salvar o arquivo
    app.run(debug=True)
