# Simulação de estoque em memória
estoque = {
    1: 5,   # Item ID 1 tem 5 unidades
    2: 10,  # Item ID 2 tem 10 unidades
    3: 0    # Item ID 3 está sem estoque
}

def checkout(pedido, cliente, regiao, pagamento):
    try:
        x = 0
        temp = 0
        a = 0
        b = 0
        aux = 0
        d1 = 0
        d2 = 0
        flag = False
        res = 0
        v = 0
        comprovante = []

        # Validação de estoque
        for item in pedido:
            if item["id"] in estoque:
                if estoque[item["id"]] < item["quantidade"]:
                    print("ERRO: Estoque insuficiente para o item:", item["nome"])
                    return
            else:
                print("ERRO: Item não encontrado no estoque:", item["nome"])
                return

        # Cálculo subtotal
        for item in pedido:
            if item["categoria"] == "Eletrônicos":
                temp += (item["preco"] * item["quantidade"]) + (10 * item["quantidade"])
            else:
                temp += item["preco"] * item["quantidade"]

        # Regras de desconto
        if cliente == "VIP":
            d1 = temp * 0.9
        elif cliente == "CORPORATIVO":
            if temp > 1000:
                d1 = temp * 0.85
            else:
                d1 = temp
        else:
            d1 = temp

        if pagamento == "PIX":
            d1 = d1 * 0.95

        # Frete
        if regiao == "SP":
            frete = 15
        elif regiao == "RJ":
            frete = 20
        else:
            frete = 35

        if temp > 300:
            frete_gratis = True
        else:
            frete_gratis = False

        # Opção A: descontos + frete integral
        a = d1 + frete

        # Opção B: frete grátis + sem descontos (mas com taxa de categoria)
        b = temp if frete_gratis else temp + frete

        # Escolha do menor valor
        if a < b:
            res = a
            flag = True
        else:
            res = b
            flag = False

        # Atualização de estoque
        for item in pedido:
            estoque[item["id"]] -= item["quantidade"]

        # Comprovante
        comprovante.append("===== COMPROVANTE =====")
        comprovante.append("Cliente: " + cliente)
        comprovante.append("Região: " + regiao)
        comprovante.append("Pagamento: " + pagamento)
        comprovante.append("Itens:")
        for item in pedido:
            comprovante.append(f"- {item['nome']} x{item['quantidade']} (R${item['preco']:.2f})")
        comprovante.append("Subtotal: R$ {:.2f}".format(temp))
        comprovante.append("Opção A (descontos + frete): R$ {:.2f}".format(a))
        comprovante.append("Opção B (frete grátis sem descontos): R$ {:.2f}".format(b))
        comprovante.append("Escolhido: " + ("Opção A" if flag else "Opção B"))
        comprovante.append("TOTAL FINAL: R$ {:.2f}".format(res))
        comprovante.append("=======================")

        for linha in comprovante:
            print(linha)

    except Exception as e:
        print("ERRO CRÍTICO:", str(e))


# Exemplo de uso - fluxo de sucesso
pedido_sucesso = [
    {"id": 1, "nome": "Celular", "preco": 1200.0, "quantidade": 1, "categoria": "Eletrônicos"},
    {"id": 2, "nome": "Livro", "preco": 50.0, "quantidade": 2, "categoria": "Outros"}
]

checkout(pedido_sucesso, "VIP", "SP", "PIX")

print("\n---\n")

# Exemplo de uso - fluxo de falha (estoque insuficiente)
pedido_falha = [
    {"id": 3, "nome": "Notebook", "preco": 3000.0, "quantidade": 1, "categoria": "Eletrônicos"}
]

checkout(pedido_falha, "CORPORATIVO", "RJ", "Cartão de Crédito")
