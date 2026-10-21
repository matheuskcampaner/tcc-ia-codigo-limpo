import uuid

def calcular_preco_ingresso(valor_base, idade, dia_semana, es_estudante, eh_professor=False):
    """
    Calcula o preço final do ingresso com base nas regras de desconto.
    Os descontos não são cumulativos (máximo de 50%).
    """
    # Normaliza a string do dia da semana para evitar problemas com maiúsculas/minúsculas
    dia_semana_norm = dia_semana.strip().lower()
    
    # Regra 1: Quarta-feira é metade do preço para todo mundo
    if dia_semana_norm == 'quarta-feira' or dia_semana_norm == 'quarta':
        tem_desconto = True
    # Regra 2: Nos demais dias, o desconto vai para estudantes, crianças (<= 12) e idosos (>= 60)
    elif es_estudante or idade <= 12 or idade >= 60 or eh_professor:
        tem_desconto = True
    else:
        tem_desconto = False

    # Aplica o desconto de 50% se o cliente tiver direito
    if tem_desconto:
        preco_final = valor_base * 0.5
    else:
        preco_final = valor_base

    return preco_final


def emitir_ingresso(valor_base, idade, dia_semana, es_estudante, eh_professor=False):
    """
    Simula a emissão do ingresso exibindo os dados e o ID gerado.
    """
    preco_pago = calcular_preco_ingresso(valor_base, idade, dia_semana, es_estudante, eh_professor)
    
    # Gera um ID único de 8 caracteres para o bilhete
    id_bilhete = str(uuid.uuid4())[:8].upper()
    
    print("-" * 40)
    print("       🎟️  CINEMA - BILHETE EMITIDO 🎟️       ")
    print("-" * 40)
    print(f" ID do Bilhete:  #{id_bilhete}")
    print(f" Dia da Semana:  {dia_semana}")
    print(f" Idade:          {idade} anos")
    print(f" Estudante:      {'Sim' if es_estudante else 'Não'}")
    print(f" Valor Base:     R$ {valor_base:.2f}")
    print(f" Valor Pago:     R$ {preco_pago:.2f}")
    print("-" * 40)
    print(" Sucesso: Ingresso válido. Bom filme!\n")


# --- EXEMPLOS DE USO EXECUTÁVEIS ---
if __name__ == "__main__":
    valor_ingresso_padrao = 40.00

    # Caso 1: Quarta-feira (Todo mundo paga meia)
    print("Cenário 1: Adulto, não estudante, na quarta-feira")
    emitir_ingresso(valor_ingresso_padrao, idade=30, dia_semana="Quarta-feira", es_estudante=False)

    # Caso 2: Estudante em um sábado (Desconto por ser estudante)
    print("Cenário 2: Jovem de 20 anos, estudante, no sábado")
    emitir_ingresso(valor_ingresso_padrao, idade=20, dia_semana="Sábado", es_estudante=True)

    # Caso 3: Idoso em um domingo (Desconto por idade)
    print("Cenário 3: Idoso de 65 anos, não estudante, no domingo")
    emitir_ingresso(valor_ingresso_padrao, idade=65, dia_semana="Domingo", es_estudante=False)

    # Caso 4: Adulto sem desconto na sexta-feira (Preço integral)
    print("Cenário 4: Adulto de 35 anos, não estudante, na sexta-feira")
    emitir_ingresso(valor_ingresso_padrao, idade=35, dia_semana="Sexta-feira", es_estudante=False)