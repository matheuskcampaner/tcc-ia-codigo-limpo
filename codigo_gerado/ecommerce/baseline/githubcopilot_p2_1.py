import uuid

# Simulação de estoque em memória
estoque = {
    1: {"nome": "Notebook", "categoria": "Eletrônicos", "preco": 2500.00, "quantidade": 5},
    2: {"nome": "Camiseta", "categoria": "Vestuário", "preco": 50.00, "quantidade": 20},
    3: {"nome": "Livro", "categoria": "Educação", "preco": 80.00, "quantidade": 10},
}

class PedidoException(Exception):
    pass

class PedidoProcessor:
    FRETE_REGIOES = {"SP": 15.0, "RJ": 20.0, "OUTROS": 35.0}
    TAXA_ELETRONICOS = 10.0

    def __init__(self, pedido):
        self.pedido = pedido
        self.comprovante = {
            "id_pedido": str(uuid.uuid4()),
            "status": "SUCESSO",
            "detalhes": {},
            "mensagem": ""
        }

    def validar_estoque(self):
        indisponiveis = []
        for item in self.pedido["itens"]:
            if item["quantidade"] <= 0 or item["preco_unitario"] <= 0:
                raise PedidoException(f"Item inválido: {item['nome']}")
            if item["id"] not in estoque:
                indisponiveis.append(item["nome"])
            elif estoque[item["id"]]["quantidade"] < item["quantidade"]:
                indisponiveis.append(item["nome"])
        if indisponiveis:
            raise PedidoException(f"Estoque insuficiente para: {', '.join(indisponiveis)}")

    def calcular_totais(self):
        subtotal = 0
        taxa_categoria = 0
        for item in self.pedido["itens"]:
            subtotal += item["preco_unitario"] * item["quantidade"]
            if item["categoria"] == "Eletrônicos":
                taxa_categoria += self.TAXA_ELETRONICOS * item["quantidade"]

        # Opção A: aplicar descontos + frete integral
        desconto_cliente = 0
        if self.pedido["cliente_tipo"] == "VIP":
            desconto_cliente = 0.10 * subtotal
        elif self.pedido["cliente_tipo"] == "CORPORATIVO" and subtotal > 1000:
            desconto_cliente = 0.15 * subtotal

        subtotal_descontado = subtotal - desconto_cliente
        if self.pedido["pagamento"] == "PIX":
            subtotal_descontado *= 0.95  # 5% adicional

        frete = self.FRETE_REGIOES.get(self.pedido["regiao"], None)
        if frete is None:
            raise PedidoException("Região não suportada")

        total_opcao_a = subtotal_descontado + taxa_categoria + frete

        # Opção B: frete grátis, sem descontos
        total_opcao_b = subtotal + taxa_categoria

        # Escolher a melhor opção
        if subtotal_descontado > 300:  # qualifica para frete grátis
            if total_opcao_b < total_opcao_a:
                opcao = "B"
                total_final = total_opcao_b
                frete_final = 0.0
                descontos_aplicados = 0.0
            else:
                opcao = "A"
                total_final = total_opcao_a
                frete_final = frete
                descontos_aplicados = desconto_cliente + (subtotal_descontado - (subtotal - desconto_cliente))
        else:
            opcao = "A"
            total_final = total_opcao_a
            frete_final = frete
            descontos_aplicados = desconto_cliente

        self.comprovante["detalhes"] = {
            "subtotal": subtotal,
            "taxa_categoria": taxa_categoria,
            "descontos_aplicados": descontos_aplicados,
            "frete": frete_final,
            "opcao_beneficio": opcao,
            "total_final": total_final
        }

    def atualizar_estoque(self):
        for item in self.pedido["itens"]:
            estoque[item["id"]]["quantidade"] -= item["quantidade"]

    def processar(self):
        try:
            self.validar_estoque()
            self.calcular_totais()
            self.atualizar_estoque()
        except PedidoException as e:
            self.comprovante["status"] = "FALHA"
            self.comprovante["mensagem"] = str(e)
        return self.comprovante


# ------------------ EXEMPLOS DE USO ------------------

# Caso de sucesso
pedido_sucesso = {
    "itens": [
        {"id": 1, "nome": "Notebook", "preco_unitario": 2500.00, "quantidade": 1, "categoria": "Eletrônicos"},
        {"id": 2, "nome": "Camiseta", "preco_unitario": 50.00, "quantidade": 2, "categoria": "Vestuário"}
    ],
    "cliente_tipo": "VIP",
    "regiao": "SP",
    "pagamento": "PIX"
}

processor = PedidoProcessor(pedido_sucesso)
comprovante_sucesso = processor.processar()
print("Comprovante Sucesso:\n", comprovante_sucesso)

# Caso de falha (estoque insuficiente)
pedido_falha = {
    "itens": [
        {"id": 3, "nome": "Livro", "preco_unitario": 80.00, "quantidade": 15, "categoria": "Educação"}
    ],
    "cliente_tipo": "COMUM",
    "regiao": "RJ",
    "pagamento": "Boleto"
}

processor_falha = PedidoProcessor(pedido_falha)
comprovante_falha = processor_falha.processar()
print("\nComprovante Falha:\n", comprovante_falha)
