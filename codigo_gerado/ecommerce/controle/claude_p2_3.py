import random

# ============================================================
# "SISTEMA" DE CHECKOUT - VERSÃO PROPOSITALMENTE MAL FEITA
# (monolito, nomes ruins, aninhamento profundo, duplicação)
# ============================================================

estoque = {
    1: 50,
    2: 3,
    3: 100,
    4: 10,
    5: 0,
}

def proc(p, c, r, fp, est):
    # p = pedido (lista de itens)
    # c = tipo de cliente
    # r = regiao
    # fp = forma de pagamento
    # est = estoque (dict mutado direto, sem cópia, sem controle)
    res = {}
    x = 0
    temp = 0
    aux = 0
    d1 = 0
    d2 = 0
    flag = False
    itens_ok = []
    linhas = []

    if p == None or len(p) == 0:
        raise Exception("pedido vazio, abortando")

    for i in range(len(p)):
        it = p[i]
        try:
            v = float(it["preco"])
            q = int(it["quantidade"])
        except Exception as e:
            raise Exception("dado numerico invalido no item " + str(it.get("id", "?")) + " -> " + str(e))

        if v < 0:
            raise Exception("preco negativo no item " + str(it.get("id")))
        else:
            if q <= 0:
                raise Exception("quantidade invalida no item " + str(it.get("id")))
            else:
                idd = it["id"]
                if idd in est:
                    if est[idd] >= q:
                        flag = True
                    else:
                        flag = False
                else:
                    flag = False

                if flag == False:
                    raise Exception("estoque insuficiente para item " + str(idd) + " (" + str(it.get("nome")) + ")")
                else:
                    x = x + (v * q)
                    temp = temp + (v * q)  # cálculo duplicado do mesmo subtotal, de proposito
                    if it["categoria"] == "Eletronicos":
                        aux = aux + (10.0 * q)
                    else:
                        if it["categoria"] == "Eletrônicos":
                            aux = aux + (10.0 * q)
                        else:
                            aux = aux + 0
                    itens_ok.append(it)
                    linhas.append(str(idd) + " | " + str(it["nome"]) + " | qtd=" + str(q) + " | unit=" + str(v))

    subtotal = x  # subtotal cru, sem desconto

    # ---------- desconto de produto (OPÇÃO A) ----------
    d1 = 0
    if c == "VIP":
        d1 = subtotal * 0.10
    else:
        if c == "CORPORATIVO":
            if subtotal > 1000.0:
                d1 = subtotal * 0.15
            else:
                d1 = 0
        else:
            if c == "COMUM":
                d1 = 0
            else:
                d1 = 0  # tipo desconhecido, sem tratamento decente

    valorA = subtotal - d1

    if fp == "PIX":
        d2 = valorA * 0.05
        valorA = valorA - d2
    else:
        if fp == "Cartão de Crédito":
            d2 = 0
        else:
            if fp == "Boleto":
                d2 = 0
            else:
                d2 = 0

    # frete opção A - sempre integral, calculado de novo (duplicado)
    freteA = 0
    if r == "SP":
        freteA = 15.0
    else:
        if r == "RJ":
            freteA = 20.0
        else:
            if r == "OUTROS":
                freteA = 35.0
            else:
                freteA = 35.0  # região desconhecida cai no mesmo valor de "OUTROS"

    totalA = valorA + freteA + aux

    # ---------- OPÇÃO B: frete grátis condicional, sem descontos ----------
    freteB = 0
    if subtotal > 300.0:
        freteB = 0
    else:
        if r == "SP":
            freteB = 15.0
        else:
            if r == "RJ":
                freteB = 20.0
            else:
                if r == "OUTROS":
                    freteB = 35.0
                else:
                    freteB = 35.0

    # taxa de categoria recalculada de novo manualmente (duplicação proposital)
    aux2 = 0
    for j in range(len(itens_ok)):
        it2 = itens_ok[j]
        if it2["categoria"] == "Eletronicos" or it2["categoria"] == "Eletrônicos":
            aux2 = aux2 + (10.0 * int(it2["quantidade"]))
        else:
            aux2 = aux2 + 0

    totalB = subtotal + freteB + aux2

    # ---------- escolha do menor valor ----------
    if totalA <= totalB:
        final = totalA
        opcao = "A"
    else:
        final = totalB
        opcao = "B"

    # ---------- atualização direta do estoque (mutação sem função) ----------
    for k in range(len(itens_ok)):
        it3 = itens_ok[k]
        idd3 = it3["id"]
        q3 = int(it3["quantidade"])
        if idd3 in est:
            est[idd3] = est[idd3] - q3
        else:
            pass

    # ---------- montagem do comprovante ----------
    comp = "===== COMPROVANTE =====\n"
    comp = comp + "Cliente: " + str(c) + " | Regiao: " + str(r) + " | Pagamento: " + str(fp) + "\n"
    for m in range(len(linhas)):
        comp = comp + linhas[m] + "\n"
    comp = comp + "------------------------\n"
    comp = comp + "Subtotal bruto: R$ " + str(round(subtotal, 2)) + "\n"
    comp = comp + "Opcao A (descontos+frete integral): R$ " + str(round(totalA, 2)) + "\n"
    comp = comp + "Opcao B (frete gratis condicional): R$ " + str(round(totalB, 2)) + "\n"
    comp = comp + "Opcao escolhida: " + opcao + "\n"
    comp = comp + "TOTAL FINAL: R$ " + str(round(final, 2)) + "\n"
    comp = comp + "========================\n"

    res["total"] = round(final, 2)
    res["opcao"] = opcao
    res["comprovante"] = comp
    res["subtotal"] = round(subtotal, 2)
    print(comp)
    return res


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":

    print(">>> FLUXO DE SUCESSO <<<")
    pedido_ok = [
        {"id": 1, "nome": "Fone Bluetooth", "preco": 150.0, "quantidade": 2, "categoria": "Eletronicos"},
        {"id": 3, "nome": "Camiseta", "preco": 60.0, "quantidade": 4, "categoria": "Vestuario"},
        {"id": 4, "nome": "Mouse Gamer", "preco": 90.0, "quantidade": 1, "categoria": "Eletronicos"},
    ]

    try:
        resultado = proc(pedido_ok, "VIP", "SP", "PIX", estoque)
        print("Estoque apos compra:", estoque)
        print("Resumo:", resultado["opcao"], resultado["total"])
    except Exception as e:
        print("Erro inesperado no fluxo de sucesso:", e)

    print("\n>>> FLUXO DE FALHA (estoque insuficiente) <<<")
    pedido_falho = [
        {"id": 2, "nome": "Smartwatch", "preco": 500.0, "quantidade": 5, "categoria": "Eletronicos"},
    ]

    try:
        resultado2 = proc(pedido_falho, "CORPORATIVO", "RJ", "Boleto", estoque)
        print("Resumo:", resultado2)
    except Exception as e:
        print("Falha no checkout:", e)

    print("\n>>> FLUXO DE FALHA (dado numerico invalido) <<<")
    pedido_invalido = [
        {"id": 3, "nome": "Camiseta", "preco": "abc", "quantidade": 2, "categoria": "Vestuario"},
    ]

    try:
        resultado3 = proc(pedido_invalido, "COMUM", "OUTROS", "Cartão de Crédito", estoque)
        print("Resumo:", resultado3)
    except Exception as e:
        print("Falha no checkout:", e)