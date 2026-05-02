# Neste código, eu juntei input junto com o que aprendi hoje, para criar um programa que recebe o nome, a idade e o objetivo do usuário, e mostra essas informações no terminal de forma personalizada. O input é utilizado para receber as informações do usuário, e o print serve para mostrar essas informações no terminal de forma personalizada utilizando f-string.

nome = input("Digite seu nome: ")
print(f"Olá, {nome}!")

idade = int(input("Digite sua idade: "))
print(f"Você tem {idade} anos.")

objetivo = input("Qual é o seu maior objetivo? ")
print(f"Seu maior objetivo é: {objetivo}, vá atrás dele! Todo dia, de forma consistente, você chegará lá!")

