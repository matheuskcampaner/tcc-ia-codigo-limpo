import random


def p(a, b, c, d, e, f):
    try:
        if not isinstance(a, list):
            raise Exception("Pedido inválido")

        if not isinstance(b, dict):
            raise Exception("Cliente inválido")

        if not isinstance(c, str):
            raise Exception("Região inválida")

        if not isinstance(d, str):
            raise Exception("Pagamento inválido")

        x = 0
        y = 0
        z = 0
        t = 0
        v = 0
        q = 0
        flag = True
        res = []
        aux = []

        if c != "SP" and c != "RJ" and c != "OUTROS":
            raise Exception("Região não permitida")

        if d != "Cartão de Crédito" and d != "PIX" and d != "Boleto":
            raise Exception("Forma de pagamento não permitida")

        if "tipo" not in b:
            raise Exception("Tipo de cliente não informado")

        if b["tipo"] != "COMUM" and b["tipo"] != "VIP" and b["tipo"] != "CORPORATIVO":
            raise Exception("Tipo de cliente inválido")

        if c == "SP":
            v = 15
        else:
            if c == "RJ":
                v = 20
            else:
                v = 35

        if not isinstance(e, dict):
            raise Exception("Estoque inválido")

        for i in a:
            if not isinstance(i, dict):
                raise Exception("Item inválido")

            if "id" not in i or "nome" not in i or "preco" not in i or "quantidade" not in i or "categoria" not in i:
                raise Exception("Item com dados incompletos")

            if not isinstance(i["id"], int):
                raise Exception("ID inválido")

            if not isinstance(i["nome"], str):
                raise Exception("Nome inválido")

            if not isinstance(i["preco"], (int, float)) or isinstance(i["preco"], bool):
                raise Exception("Preço inválido")

            if not isinstance(i["quantidade"], int) or isinstance(i["quantidade"], bool):
                raise Exception("Quantidade inválida")

            if i["preco"] < 0:
                raise Exception("Preço não pode ser negativo")

            if i["quantidade"] <= 0:
                raise Exception("Quantidade deve ser maior que zero")

            if i["categoria"] == "":
                raise Exception("Categoria inválida")

            if i["id"] not in e:
                raise Exception("Produto não encontrado no estoque: " + str(i["id"]))

            if not isinstance(e[i["id"]], (int, float)):
                raise Exception("Saldo de estoque inválido")

            if e[i["id"]] < 0:
                raise Exception("Estoque negativo")

            if e[i["id"]] < i["quantidade"]:
                flag = False
                raise Exception(
                    "Estoque insuficiente para o produto "
                    + str(i["id"])
                    + ". Disponível: "
                    + str(e[i["id"]])
                    + ", solicitado: "
                    + str(i["quantidade"])
                )

            x = x + (i["preco"] * i["quantidade"])

            if i["categoria"] == "Eletrônicos":
                y = y + (10 * i["quantidade"])

            res.append({
                "id": i["id"],
                "nome": i["nome"],
                "quantidade": i["quantidade"],
                "preco": i["preco"],
                "categoria": i["categoria"],
                "total": i["preco"] * i["quantidade"]
            })

        if x < 0 or y < 0:
            raise Exception("Valores calculados inválidos")

        if x > 300:
            q = 0
        else:
            q = v

        z = x

        if b["tipo"] == "VIP":
            z = z - (z * 0.10)
        else:
            if b["tipo"] == "CORPORATIVO":
                if x > 1000:
                    z = z - (z * 0.15)
                else:
                    z = z
            else:
                z = z

        if d == "PIX":
            z = z - (z * 0.05)

        if z < 0:
            raise Exception("Desconto resultou em valor inválido")

        z = z + y + q

        t = x

        if b["tipo"] == "VIP":
            t = t - (t * 0.10)
        else:
            if b["tipo"] == "CORPORATIVO":
                if x > 1000:
                    t = t - (t * 0.15)
                else:
                    t = t
            else:
                t = t

        if d == "PIX":
            t = t - (t * 0.05)

        t = t + y

        if x > 300:
            t = t + 0
        else:
            t = t + v

        aux.append(t)

        if x > 300:
            t2 = x
            t2 = t2 + y
            t2 = t2 + 0
        else:
            t2 = x
            t2 = t2 + y
            t2 = t2 + v

        if x > 300:
            w = x + y
        else:
            w = x + y + v

        if w < 0:
            raise Exception("Valor da opção B inválido")

        if x > 300:
            opcao_b = x + y
        else:
            opcao_b = x + y

        opcao_a = z

        if opcao_a <= opcao_b:
            final = opcao_a
            escolhida = "A"
        else:
            final = opcao_b
            escolhida = "B"

        if final < 0:
            raise Exception("Valor final inválido")

        if isinstance(f, dict):
            if f.get("confirmar") is False:
                raise Exception("Operação cancelada pelo cliente")
        else:
            raise Exception("Dados de confirmação inválidos")

        for i in a:
            if i["id"] in e:
                if e[i["id"]] >= i["quantidade"]:
                    e[i["id"]] = e[i["id"]] - i["quantidade"]
                else:
                    raise Exception("Erro ao atualizar estoque")
            else:
                raise Exception("Erro ao localizar produto durante atualização")

        n = random.randint(100000, 999999)

        print("\n================ COMPROVANTE ================")
        print("Pedido:", n)
        print("Cliente:", b["tipo"])
        print("Região:", c)
        print("Pagamento:", d)
        print("---------------------------------------------")

        for i in res:
            print(
                "ID:",
                i["id"],
                "| Produto:",
                i["nome"],
                "| Categoria:",
                i["categoria"],
                "| Quantidade:",
                i["quantidade"],
                "| Unitário: R$",
                format(i["preco"], ".2f"),
                "| Total: R$",
                format(i["total"], ".2f")
            )

        print("---------------------------------------------")
        print("Subtotal dos produtos: R$", format(x, ".2f"))
        print("Taxa de manuseio: R$", format(y, ".2f"))

        if b["tipo"] == "VIP":
            print("Desconto de cliente: 10%")
        else:
            if b["tipo"] == "CORPORATIVO":
                if x > 1000:
                    print("Desconto de cliente: 15%")
                else:
                    print("Desconto de cliente: 0%")
            else:
                print("Desconto de cliente: 0%")

        if d == "PIX":
            print("Desconto PIX: 5%")
        else:
            print("Desconto PIX: 0%")

        print("Frete normal: R$", format(v, ".2f"))

        if x > 300:
            print("Frete grátis: SIM")
        else:
            print("Frete grátis: NÃO")

        print("Opção A: R$", format(opcao_a, ".2f"))
        print("Opção B: R$", format(opcao_b, ".2f"))
        print("Opção escolhida:", escolhida)
        print("VALOR FINAL: R$", format(final, ".2f"))
        print("---------------------------------------------")
        print("Estoque atualizado:")
        
        for k in e:
            print("Produto", k, "->", e[k], "unidades")

        print("Status: PEDIDO PROCESSADO COM SUCESSO")
        print("=============================================\n")

        return {
            "pedido": n,
            "opcao": escolhida,
            "valor": final,
            "estoque": e
        }

    except ValueError as err:
        print("Erro de valor:", err)
        return None

    except TypeError as err:
        print("Erro de tipo:", err)
        return None

    except Exception as err:
        print("Erro no processamento:", err)
        return None


estoque = {
    101: 10,
    102: 5,
    103: 20
}

pedido = [
    {
        "id": 101,
        "nome": "Notebook",
        "preco": 2500.00,
        "quantidade": 1,
        "categoria": "Eletrônicos"
    },
    {
        "id": 102,
        "nome": "Mouse",
        "preco": 100.00,
        "quantidade": 2,
        "categoria": "Periféricos"
    }
]

cliente = {
    "tipo": "VIP"
}

pagamento = "PIX"

configuracao = {
    "confirmar": True
}

print("TESTE 1 - FLUXO DE SUCESSO")

resultado = p(
    pedido,
    cliente,
    "SP",
    pagamento,
    estoque,
    configuracao
)

print("Resultado retornado:", resultado)


print("\nTESTE 2 - FALHA POR ESTOQUE INSUFICIENTE")

pedido_com_erro = [
    {
        "id": 103,
        "nome": "Teclado",
        "preco": 200.00,
        "quantidade": 50,
        "categoria": "Periféricos"
    }
]

resultado_erro = p(
    pedido_com_erro,
    {
        "tipo": "COMUM"
    },
    "RJ",
    "Boleto",
    estoque,
    {
        "confirmar": True
    }
)

print("Resultado retornado:", resultado_erro)


print("\nTESTE 3 - FALHA POR DADO NUMÉRICO INVÁLIDO")

pedido_invalido = [
    {
        "id": 101,
        "nome": "Notebook",
        "preco": "2500",
        "quantidade": 1,
        "categoria": "Eletrônicos"
    }
]

resultado_invalido = p(
    pedido_invalido,
    {
        "tipo": "COMUM"
    },
    "OUTROS",
    "Cartão de Crédito",
    estoque,
    {
        "confirmar": True
    }
)

print("Resultado retornado:", resultado_invalido)