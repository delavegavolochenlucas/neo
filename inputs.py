# Input é uma função que recebe alguma informação do usuário, e armazena essa informação em uma variável.

nome = input("Qual é a seu nome? ")
print(type(nome))

# o input recebe a informação do usuário, e armazena essa informação na variável nome, e o print serve para mostrar o tipo da variável nome no terminal, que é str (string), ou seja, texto. O input sempre retorna uma string, mesmo que o usuário digite um número, por isso é importante usar a função int() para converter a string em um número inteiro quando necessário.