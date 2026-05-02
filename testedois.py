# Aqui eu juntei absolutamente tudo que aprendi: variáveis, loops, condicionais, listas, dicionários, inputs e funções. O programa pede para o usuário digitar o nome e a idade de três pessoas, e depois verifica se cada pessoa é adulta ou menor de idade, imprimindo o resultado no terminal.

nome1 = input("Digite o primeiro nome: ")
idade1 = int(input("Digite a primeira idade: "))

nome2 = input("Digite o segundo nome: ")
idade2 = int(input("Digite a segunda idade: "))

nome3 = input("Digite o terceiro nome: ")
idade3 = int(input("Digite a terceira idade: "))

pessoas = [
    {"nome": nome1, "idade": idade1},
    {"nome": nome2, "idade": idade2},
    {"nome": nome3, "idade": idade3} 
]

for pessoa in pessoas:
    if pessoa["idade"] >= 18:
        print(f"{pessoa['nome']} é adulto.")
    else:
        print(f"{pessoa['nome']} é menor de idade.")

# O programa começa pedindo para o usuário digitar o nome e a idade de três pessoas, usando a função input() para obter as informações e a função int() para converter as idades em números inteiros. Em seguida, as informações são armazenadas em uma lista de dicionários, onde cada dicionário representa uma pessoa com seu nome e idade. Por fim, o programa usa um loop for para iterar sobre a lista de pessoas e uma estrutura condicional if-else para verificar se cada pessoa é adulta (idade maior ou igual a 18) ou menor de idade, imprimindo o resultado no terminal.