from abc import ABC, abstractmethod
from typing import List, Dict
import uuid


# ------------------ MODELOS DE DOMÍNIO ------------------

class Item:
    def __init__(self, item_id: str, nome: str, preco_unitario: float, quantidade: int, categoria: str):
        if preco_unitario <= 0 or quantidade <= 0:
            raise ValueError("Preço e quantidade devem ser maiores que zero.")
        self.item_id = item_id
        self.nome = nome
        self.preco_unitario = preco_unitario
        self.quantidade = quantidade
        self.categoria = categoria


class Pedido:
    def __init__(self, cliente_tipo: str, regiao: str, pagamento: str, itens: List[Item]):
        self.id = str(uuid.uuid4())
        self.cliente_tipo = cliente_tipo
        self.regiao = regiao
        self.pagamento = pagamento
        self.itens = itens


# ------------------ EXCEÇÕES CUSTOMIZADAS ------------------

class EstoqueInsuficienteException(Exception):
    pass


class RegiaoNaoSuportadaException(Exception):
    pass


class PagamentoNaoSuportadoException(Exception):
    pass


# ------------------ GESTÃO DE ESTOQUE ------------------

class Estoque:
    def __init__(self, saldo_inicial: Dict[str, int]):
        self.saldo = saldo_inicial

    def validar_e_reservar(self, itens: List[Item]) -> None:
        indisponiveis = []
        for item in itens:
            if self.saldo.get(item.item_id, 0) < item.quantidade:
                indisponiveis.append(item.nome)
        if indisponiveis:
            raise EstoqueInsuficienteException(f"Estoque insuficiente para: {', '.join(indisponiveis)}")

        # Reserva
        for item in itens:
            self.saldo[item.item_id] -= item.quantidade


# ------------------ TAXAS POR CATEGORIA ------------------

class TaxaCategoria:
    TAXAS_FIXAS = {
        "Eletrônicos": 10.0
    }

    @staticmethod
    def calcular(itens: List[Item]) -> float:
        total_taxa = 0.0
        for item in itens:
            taxa_unitaria = TaxaCategoria.TAXAS_FIXAS.get(item.categoria, 0.0)
            total_taxa += taxa_unitaria * item.quantidade
        return total_taxa


# ------------------ ESTRATÉGIAS DE DESCONTO ------------------

class DescontoStrategy(ABC):
    @abstractmethod
    def aplicar(self, subtotal: float, pedido: Pedido) -> float:
        pass


class DescontoClienteVIP(DescontoStrategy):
    def aplicar(self, subtotal: float, pedido: Pedido) -> float:
        if pedido.cliente_tipo == "VIP":
            return subtotal * 0.9
        return subtotal


class DescontoClienteCorporativo(DescontoStrategy):
    def aplicar(self, subtotal: float, pedido: Pedido) -> float:
        if pedido.cliente_tipo == "CORPORATIVO" and subtotal > 1000:
            return subtotal * 0.85
        return subtotal


class DescontoPagamentoPIX(DescontoStrategy):
    def aplicar(self, subtotal: float, pedido: Pedido) -> float:
        if pedido.pagamento == "PIX":
            return subtotal * 0.95
        return subtotal


# ------------------ ESTRATÉGIAS DE FRETE ------------------

class FreteStrategy(ABC):
    @abstractmethod
    def calcular(self, pedido: Pedido, valor_produtos: float) -> float:
        pass


class FretePorRegiao(FreteStrategy):
    FRETES = {
        "SP": 15.0,
        "RJ": 20.0,
        "OUTROS": 35.0
    }

    def calcular(self, pedido: Pedido, valor_produtos: float) -> float:
        if pedido.regiao not in self.FRETES:
            raise RegiaoNaoSuportadaException(f"Região não suportada: {pedido.regiao}")
        if valor_produtos > 300:
            return 0.0
        return self.FRETES[pedido.regiao]


# ------------------ GERADOR DE COMPROVANTE ------------------

class Comprovante:
    def __init__(self, pedido: Pedido, status: str, subtotal: float, taxa_categoria: float,
                 descontos: float, frete: float, opcao: str, total_final: float):
        self.pedido_id = pedido.id
        self.status = status
        self.subtotal = subtotal
        self.taxa_categoria = taxa_categoria
        self.descontos = descontos
        self.frete = frete
        self.opcao = opcao
        self.total_final = total_final

    def __str__(self) -> str:
        return (
            f"--- COMPROVANTE ---\n"
            f"Pedido ID: {self.pedido_id}\n"
            f"Status: {self.status}\n"
            f"Subtotal: R$ {self.subtotal:.2f}\n"
            f"Taxa Categoria: R$ {self.taxa_categoria:.2f}\n"
            f"Descontos: R$ {self.descontos:.2f}\n"
            f"Frete: R$ {self.frete:.2f}\n"
            f"Opção Selecionada: {self.opcao}\n"
            f"TOTAL FINAL: R$ {self.total_final:.2f}\n"
        )


# ------------------ CHECKOUT ------------------

class CheckoutProcessor:
    def __init__(self, estoque: Estoque, desconto_strategies: List[DescontoStrategy], frete_strategy: FreteStrategy):
        self.estoque = estoque
        self.desconto_strategies = desconto_strategies
        self.frete_strategy = frete_strategy

    def processar(self, pedido: Pedido) -> Comprovante:
        try:
            self.estoque.validar_e_reservar(pedido.itens)

            subtotal = sum(item.preco_unitario * item.quantidade for item in pedido.itens)
            taxa_categoria = TaxaCategoria.calcular(pedido.itens)

            # Opção A: aplicar descontos + frete
            valor_com_descontos = subtotal
            for strategy in self.desconto_strategies:
                valor_com_descontos = strategy.aplicar(valor_com_descontos, pedido)

            frete_opcao_a = self.frete_strategy.calcular(pedido, valor_com_descontos)
            total_opcao_a = valor_com_descontos + taxa_categoria + frete_opcao_a
            descontos_aplicados = subtotal - valor_com_descontos

            # Opção B: sem descontos, frete grátis
            frete_opcao_b = 0.0
            total_opcao_b = subtotal + taxa_categoria

            if total_opcao_a <= total_opcao_b:
                return Comprovante(pedido, "SUCESSO", subtotal, taxa_categoria,
                                   descontos_aplicados, frete_opcao_a, "Opção A", total_opcao_a)
            else:
                return Comprovante(pedido, "SUCESSO", subtotal, taxa_categoria,
                                   0.0, frete_opcao_b, "Opção B", total_opcao_b)

        except Exception as e:
            return Comprovante(pedido, "FALHA", 0, 0, 0, 0, "N/A", 0)


# ------------------ EXEMPLO DE USO ------------------

if __name__ == "__main__":
    estoque_inicial = {"1": 10, "2": 5}
    estoque = Estoque(estoque_inicial)

    desconto_strategies = [DescontoClienteVIP(), DescontoClienteCorporativo(), DescontoPagamentoPIX()]
    frete_strategy = FretePorRegiao()
    checkout = CheckoutProcessor(estoque, desconto_strategies, frete_strategy)

    # Caso de sucesso
    itens = [Item("1", "Notebook", 2000.0, 1, "Eletrônicos"),
             Item("2", "Mouse", 100.0, 2, "Acessórios")]
    pedido = Pedido("VIP", "SP", "PIX", itens)
    comprovante = checkout.processar(pedido)
    print(comprovante)

    # Caso de falha (estoque insuficiente)
    itens_falha = [Item("1", "Notebook", 2000.0, 20, "Eletrônicos")]
    pedido_falha = Pedido("COMUM", "RJ", "Cartão de Crédito", itens_falha)
    comprovante_falha = checkout.processar(pedido_falha)
    print(comprovante_falha)
