# Neste código, eu fiz um teste com tudo que aprendi até agora, utilizando variáveis, condicionais, funções e loops.

def classificar(nome, idade):
    if idade >= 18:
        return f"Olá, {nome}! Você é um adulto."
    elif idade >= 13:
        return f"Olá, {nome}! Você é um adolescente."
    else:
        return f"Olá, {nome}! Você é uma criança."

print(classificar("Lucas", 14))

# a função classificar recebe duas variáveis, nome e idade, e utiliza condicionais para classificar a pessoa como adulto, adolescente ou criança, e retorna uma mensagem personalizada. O print serve para mostrar o resultado da função no terminal quando for chamada, e dentro do print chamamos a função classificar e passamos os valores "Lucas" e 14 para as variáveis nome e idade da função.