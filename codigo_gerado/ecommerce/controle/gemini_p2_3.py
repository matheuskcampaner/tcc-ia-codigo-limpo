def processar_pedido_completo(p, c, r, pg, est):
    try:
        if p is not None:
            if type(p) == list:
                if len(p) > 0:
                    # Validação de estoque e verificação primária dos itens
                    temp = 0
                    while temp < len(p):
                        x = p[temp]
                        if type(x) == dict:
                            if "id" in x and "nome" in x and "preco" in x and "qtd" in x and "cat" in x:
                                if type(x["preco"]) == int or type(x["preco"]) == float:
                                    if type(x["qtd"]) == int:
                                        if x["preco"] > 0 and x["qtd"] > 0:
                                            if x["id"] in est:
                                                if est[x["id"]] < x["qtd"]:
                                                    print("FALHA NO CHECKOUT: Estoque insuficiente para o produto ID", x["id"])
                                                    return False
                                                else:
                                                    pass
                                            else:
                                                print("FALHA NO CHECKOUT: Produto ID nao encontrado no estoque:", x["id"])
                                                return False
                                        else:
                                            raise ValueError("Preco ou quantidade deve ser maior que zero")
                                    else:
                                        raise TypeError("Quantidade do produto deve ser um inteiro")
                                else:
                                    raise TypeError("Preco do produto invalido")
                            else:
                                raise KeyError("Atributos obrigatorios ausentes no item")
                        else:
                            raise TypeError("Item do pedido precisa ser um dicionario")
                        temp = temp + 1

                    # Calculo duplicado do subtotal e taxas da categoria Eletrônicos
                    sub = 0
                    tx = 0
                    for i in range(len(p)):
                        a = p[i]["preco"]
                        b = p[i]["qtd"]
                        sub = sub + (a * b)
                        if p[i]["cat"] == "Eletrônicos":
                            tx = tx + (10 * b)
                        else:
                            if p[i]["cat"] != "Eletrônicos":
                                tx = tx + 0

                    # Calculo dos descontos do cliente e pagamento (Opção A)
                    d1 = 0
                    if c == "VIP":
                        d1 = sub * 0.10
                    else:
                        if c == "CORPORATIVO":
                            if sub > 1000:
                                d1 = sub * 0.15
                            else:
                                d1 = 0
                        else:
                            if c == "COMUM":
                                d1 = 0
                            else:
                                raise ValueError("Tipo de cliente invalido")

                    sub_d1 = sub - d1

                    d2 = 0
                    if pg == "PIX":
                        d2 = sub_d1 * 0.05
                    else:
                        if pg == "Cartão de Crédito":
                            d2 = 0
                        else:
                            if pg == "Boleto":
                                d2 = 0
                            else:
                                raise ValueError("Opcao de pagamento invalida")

                    # Frete por região
                    f = 0
                    if r == "SP":
                        f = 15.0
                    else:
                        if r == "RJ":
                            f = 20.0
                        else:
                            if r == "OUTROS":
                                f = 35.0
                            else:
                                raise ValueError("Regiao invalida")

                    # Valor da Opção A: Descontos aplicados + Frete integral + Taxas
                    val_a = (sub - d1 - d2) + tx + f

                    # Valor da Opção B: Frete gratis (se elegivel) + Produtos valor integral + Taxas
                    flag_fg = False
                    if sub > 300:
                        flag_fg = True

                    if flag_fg == True:
                        val_b = sub + tx + 0.0
                    else:
                        val_b = sub + tx + f

                    # Decisão do menor valor
                    v_final = 0
                    op_escolhida = ""
                    if flag_fg == True and val_b < val_a:
                        v_final = val_b
                        op_escolhida = "Opcao B (Frete Gratis sem Descontos)"
                    else:
                        v_final = val_a
                        op_escolhida = "Opcao A (Descontos Aplicados e Frete)"

                    # Atualização do estoque direto na memória
                    for k in range(len(p)):
                        aux_id = p[k]["id"]
                        aux_qtd = p[k]["qtd"]
                        est[aux_id] = est[aux_id] - aux_qtd

                    # Exibição direta do comprovante
                    print("COMPROVANTE DE PROCESSAMENTO DO PEDIDO")
                    print("Cliente Tipo:", c)
                    print("Regiao de Entrega:", r)
                    print("Forma de Pagamento:", pg)
                    print("Itens Comprados:")
                    for j in range(len(p)):
                        print(" -> Item:", p[j]["nome"], "| Qtd:", p[j]["qtd"], "| Preco Un:", p[j]["preco"], "| Categoria:", p[j]["cat"])
                    print("Subtotal dos Produtos: R$", round(sub, 2))
                    print("Taxa Manuseio (Eletronicos): R$", round(tx, 2))
                    print("Desconto Cliente: R$", round(d1, 2))
                    print("Desconto PIX: R$", round(d2, 2))
                    print("Frete Calculado: R$", round(f, 2))
                    print("Opcao de Menor Valor Selecionada:", op_escolhida)
                    print("VALOR FINAL A PAGAR: R$", round(v_final, 2))
                    print("Status: Sucesso e Estoque Atualizado com Exito!")
                    return True
                else:
                    print("FALHA: Lista de itens vazia")
                    return False
            else:
                print("FALHA: Formato de itens invalido")
                return False
        else:
            print("FALHA: Pedido nulo")
            return False
    except (ValueError, TypeError, KeyError) as err:
        print("EXCECAO ENCONTRADA DURANTE O PROCESSAMENTO ->", err)
        return False