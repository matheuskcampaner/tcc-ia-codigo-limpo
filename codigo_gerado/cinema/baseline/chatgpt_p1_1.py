import uuid


def calcular_preco_ingresso(valor_base, idade, dia_semana, estudante):
    desconto = False

    if dia_semana.lower() == "quarta-feira":
        desconto = True
    elif estudante or idade <= 12 or idade >= 60:
        desconto = True

    if desconto:
        return valor_base * 0.5

    return valor_base


def emitir_ingresso(valor_base, idade, dia_semana, estudante):
    preco_final = calcular_preco_ingresso(
        valor_base, idade, dia_semana, estudante
    )

    id_ingresso = str(uuid.uuid4())[:8]

    print(f"Valor final do ingresso: R$ {preco_final:.2f}")
    print(f"Ingresso emitido com sucesso! ID: {id_ingresso}")


# Exemplo de uso
valor_base = 30.00
idade = 20
dia_semana = "Quarta-feira"
estudante = False

emitir_ingresso(valor_base, idade, dia_semana, estudante)