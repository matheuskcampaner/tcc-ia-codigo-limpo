import uuid

def calcular_preco_ingresso(valor_base, idade, dia_semana, estudante):
    # Normaliza o nome do dia para evitar problemas de maiúsculas/minúsculas
    dia_semana = dia_semana.strip().lower()
    
    desconto = 0.0
    
    # Regra de quarta-feira: todos têm 50% de desconto
    if dia_semana == "quarta-feira":
        desconto = 0.5
    else:
        # Nos demais dias, desconto apenas para estudantes, crianças até 12 anos e idosos a partir de 60 anos
        if estudante or idade <= 12 or idade >= 60:
            desconto = 0.5
    
    # Calcula o preço final
    preco_final = valor_base * (1 - desconto)
    return preco_final

def emitir_ingresso(valor_base, idade, dia_semana, estudante):
    preco = calcular_preco_ingresso(valor_base, idade, dia_semana, estudante)
    # Gera um ID único para o bilhete
    bilhete_id = str(uuid.uuid4())
    print(f"Preço final do ingresso: R$ {preco:.2f}")
    print(f"Ingresso emitido com sucesso! ID do bilhete: {bilhete_id}")

# Exemplo de uso
if __name__ == "__main__":
    # Cliente estudante, 20 anos, em uma terça-feira
    emitir_ingresso(valor_base=40.0, idade=20, dia_semana="Terça-feira", estudante=True)

    # Cliente não estudante, 10 anos, em uma sexta-feira
    emitir_ingresso(valor_base=40.0, idade=10, dia_semana="Sexta-feira", estudante=False)

    # Cliente não estudante, 30 anos, em uma quarta-feira
    emitir_ingresso(valor_base=40.0, idade=30, dia_semana="Quarta-feira", estudante=False)
