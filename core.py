import anthropic
import os
import sqlite3
from datetime import datetime

# Conecta à API da Anthropic usando a chave salva nas variáveis de ambiente
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Lista dos dias da semana em português, indexada igual ao weekday() do Python (0 = segunda)
DIAS_PT = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

# Limite de trocas antes de comprimir (1 troca = 1 user + 1 assistant = 2 entradas)
LIMITE_TROCAS = 20
MENSAGENS_RECENTES = 10

DB_FILE = "dados.db"


# Cria o banco e as três tabelas se ainda não existirem.
# Seguro rodar sempre na inicialização por causa do IF NOT EXISTS.
def inicializar_banco():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            data     TEXT NOT NULL,
            estudado TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            role    TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    # Tabela config armazena pares chave/valor simples, como ultima_abertura
    cur.execute("""
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    con.commit()
    con.close()


# Lê todas as mensagens da tabela historico ordenadas por id.
# Retorna lista de dicts no formato que a API da Anthropic espera.
def carregar_historico():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT role, content FROM historico ORDER BY id")
    rows = cur.fetchall()
    con.close()
    return [{"role": r[0], "content": r[1]} for r in rows]


# Substitui todo o conteúdo da tabela historico pelo histórico atual.
# DELETE + INSERT replica o comportamento de sobrescrever o arquivo JSON inteiro.
def salvar_historico(historico):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("DELETE FROM historico")
    cur.executemany(
        "INSERT INTO historico (role, content) VALUES (?, ?)",
        [(m["role"], m["content"]) for m in historico]
    )
    con.commit()
    con.close()


# Lê ultima_abertura da tabela config e todas as sessões de estudo.
# Retorna o dict padrão {"ultima_abertura": ..., "sessoes": [...]} usado em todo o código.
def carregar_estado():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT valor FROM config WHERE chave = 'ultima_abertura'")
    row = cur.fetchone()
    ultima_abertura = row[0] if row else None
    cur.execute("SELECT data, estudado FROM sessoes ORDER BY id")
    sessoes = [{"data": r[0], "estudado": r[1]} for r in cur.fetchall()]
    con.close()
    return {"ultima_abertura": ultima_abertura, "sessoes": sessoes}


# Persiste ultima_abertura e sincroniza as sessões de estudo no banco.
# INSERT OR REPLACE faz upsert na config sem duplicar a chave.
def salvar_estado(estado):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO config (chave, valor) VALUES ('ultima_abertura', ?)",
        (estado["ultima_abertura"],)
    )
    # Reescreve as sessões para manter consistência com o estado em memória
    cur.execute("DELETE FROM sessoes")
    cur.executemany(
        "INSERT INTO sessoes (data, estudado) VALUES (?, ?)",
        [(s["data"], s["estudado"]) for s in estado.get("sessoes", [])]
    )
    con.commit()
    con.close()


# Detecta em qual bloco da rotina do Lucas o horário atual se encaixa.
# Hora é convertida para decimal para facilitar comparações (ex: 8h05 = 8.08).
def bloco_do_dia():
    agora = datetime.now()
    dia = agora.weekday()  # 0=seg, 6=dom
    hora = agora.hour + agora.minute / 60

    if hora >= 22.5 or hora < 6.67:
        return "horário de dormir (22h30 às 6h40)"
    if dia < 5 and 8.08 <= hora < 17.42:
        return "período escolar (8h05 às 17h25)"
    if dia in [0, 2, 4] and 18.33 <= hora < 19.25:
        return "jiu-jitsu (18h20 às 19h15)"
    if dia in [1, 3] and 19.0 <= hora < 20.0:
        return "academia (19h às 20h)"
    return "tempo livre"


# Calcula quantos dias se passaram desde a última abertura do agente.
# Retorna 0 se for a primeira vez.
def dias_ausente(estado):
    if not estado["ultima_abertura"]:
        return 0
    ultima = datetime.fromisoformat(estado["ultima_abertura"])
    return (datetime.now() - ultima).days


# Formata as últimas 5 sessões de estudo para incluir no system prompt,
# dando ao agente contexto sobre o que o Lucas tem estudado recentemente.
def resumo_sessoes(estado):
    sessoes = estado.get("sessoes", [])
    if not sessoes:
        return ""
    ultimas = sessoes[-5:]
    linhas = []
    for s in ultimas:
        data = datetime.fromisoformat(s["data"]).strftime("%d/%m %H:%M")
        linhas.append(f"- {data}: {s['estudado']}")
    return "Histórico das últimas sessões de estudo do Lucas:\n" + "\n".join(linhas)


# Monta o system prompt dinamicamente combinando:
# - Personalidade base do agente
# - Horário atual e bloco da rotina
# - Cobrança por ausência (se passaram 2+ dias)
# - Resumo das últimas sessões de estudo
def construir_system(estado):
    # Lê o texto base do arquivo externo, que é ignorado pelo git para não expor dados pessoais
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        base = f.read().strip()

    # Injeta data, hora e bloco atual da rotina no contexto
    agora = datetime.now()
    dia_nome = DIAS_PT[agora.weekday()]
    bloco = bloco_do_dia()
    contexto_tempo = (
        f"\n\nContexto atual: são {agora.strftime('%H:%M')} de {dia_nome}, {agora.strftime('%d/%m/%Y')}. "
        f"Bloco da rotina do Lucas agora: {bloco}. Use isso para contextualizar seus conselhos."
    )

    # Se ficou 2 ou mais dias sem abrir, instrui o agente a cobrar
    ausencia = dias_ausente(estado)
    contexto_ausencia = ""
    if ausencia >= 2:
        contexto_ausencia = (
            f"\n\nAtenção: Lucas ficou {ausencia} dias sem abrir o agente. "
            f"No início da conversa, cobre ele por isso de forma direta e sem papas na língua."
        )

    # Inclui o histórico de sessões de estudo para o agente ter continuidade
    resumo = resumo_sessoes(estado)
    contexto_sessoes = f"\n\n{resumo}" if resumo else ""

    return base + contexto_tempo + contexto_ausencia + contexto_sessoes


# Comprime o histórico quando ultrapassa o limite de trocas.
# Gera um resumo via API e substitui o histórico por [par resumo] + últimas MENSAGENS_RECENTES.
# O par user/assistant é obrigatório porque a API exige alternância entre os dois roles.
def comprimir_historico(historico):
    print("\n[Comprimindo histórico...]")
    resumo_msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system="Você é um assistente de resumo. Seja direto e objetivo.",
        messages=historico + [{
            "role": "user",
            "content": "Resuma essa troca de mensagens com os pontos mais fundamentais. Seja direto e conciso."
        }]
    )
    resumo = resumo_msg.content[0].text

    par_resumo = [
        {"role": "user", "content": f"[Resumo automático da conversa anterior]\n{resumo}"},
        {"role": "assistant", "content": "Entendido, tenho esse contexto em mente."},
    ]

    return par_resumo + historico[-MENSAGENS_RECENTES:]
