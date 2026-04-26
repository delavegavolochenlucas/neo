# Importa toda a lógica compartilhada do core: banco, histórico, estado, system prompt, compressão
from core import (
    client, inicializar_banco, carregar_historico, salvar_historico,
    carregar_estado, salvar_estado, construir_system, comprimir_historico,
    LIMITE_TROCAS
)
from datetime import datetime


# Encerra a sessão do terminal: pergunta o que foi estudado e salva no banco.
# Essa função é exclusiva do terminal — o app.py tem seu próprio fluxo de encerramento.
def encerrar_sessao(estado):
    print("\nNeo: O que você estudou ou fez de produtivo nessa sessão? (deixe em branco para pular)")
    try:
        estudado = input("Você: ").strip()
    except (KeyboardInterrupt, EOFError):
        estudado = ""

    if estudado:
        estado.setdefault("sessoes", []).append({
            "data": datetime.now().isoformat(),
            "estudado": estudado
        })
        salvar_estado(estado)
        print("Neo: Registrado. Consistência é tudo. Até a próxima.")
    else:
        print("Neo: Ok. Até a próxima.")


# --- Inicialização ---

# Garante que o banco e as tabelas existem antes de qualquer leitura
inicializar_banco()

# Carrega o estado e o histórico salvos no banco
estado = carregar_estado()
historico = carregar_historico()

# Atualiza a última abertura para agora (usado para calcular ausência na próxima sessão)
estado["ultima_abertura"] = datetime.now().isoformat()
salvar_estado(estado)

# Constrói o system prompt com todos os contextos dinâmicos
system = construir_system(estado)


# --- Loop principal ---

while True:
    try:
        pergunta = input("Você: ").strip()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C ou fim de input encerra a sessão normalmente
        print()
        encerrar_sessao(estado)
        break

    # Comandos de saída encerram a sessão e registram o que foi estudado
    if pergunta.lower() in ["sair", "exit", "quit", "tchau"]:
        encerrar_sessao(estado)
        break

    # Ignora mensagens vazias sem quebrar o loop
    if not pergunta:
        continue

    # Adiciona a mensagem do usuário ao histórico antes de enviar
    historico.append({"role": "user", "content": pergunta})

    # Abre o stream e imprime cada token conforme chega, sem esperar a resposta completa.
    # flush=True força o terminal a exibir cada token imediatamente sem esperar buffer encher.
    print("Neo: ", end="", flush=True)
    resposta = ""
    with client.messages.stream(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=system,
        messages=historico
    ) as stream:
        for token in stream.text_stream:
            print(token, end="", flush=True)
            resposta += token

    # Pula linha após o stream terminar e salva a resposta completa no histórico
    print()
    historico.append({"role": "assistant", "content": resposta})

    # Se ultrapassou o limite de trocas, comprime antes de salvar
    if len(historico) >= LIMITE_TROCAS * 2:
        historico = comprimir_historico(historico)

    salvar_historico(historico)
