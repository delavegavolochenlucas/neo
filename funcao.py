# Função é um pedaço de código que pode ser reutilizado várias vezes, sem ter que escrever tudo de novo.

def saudacao(nome): 
    return f"Olá, {nome}!"
print(saudacao("Lucas"))

# a função é definida com a palavra def, seguida do nome da função (saudacao nesse caso), e entre os parênteses colocamos uma variável (nome nesse caso), que é o que a função vai receber quando for chamada, já o return é utilizado para mostrar para a função o que ela deve retornar quando for chamada, e usa f-string para "nome" virar o valor da variável nome que a função recebe, e nao um texto comum. E o print serve para mostrar o que a função retorna no terminal quando for chamada, e dentro do print chamamos a função e passamos o valor "Lucas" para a variável nome da função.