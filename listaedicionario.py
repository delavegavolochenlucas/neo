# Neste código, eu juntei tudo que aprendi sobre listas e dicionários, para criar um programa que armazena informações de várias pessoas em uma lista de dicionários.
pessoas = [
    {"nome": "Lucas", "idade": 14},
    {"nome": "Desiree", "idade": 47},
    {"nome": "Daniel", "idade": 42}
]

for pessoa in pessoas: 
    print(f"{pessoa['nome']}, {pessoa['idade']}")

# nesse código, criamos uma lista chamada pessoas, que contém três dicionários, cada um representando uma pessoa com suas informações de nome e idade. Utilizamos um loop for para percorrer cada dicionário na lista, e o print serve para mostrar o nome e a idade de cada pessoa no terminal de forma personalizada utilizando f-string. O for pega cada dicionário da lista pessoas, e coloca na variável escolhida (pessoa nesse caso), e a cada loop ele é atualizado com o próximo dicionário da lista.