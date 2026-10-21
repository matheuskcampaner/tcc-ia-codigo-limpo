from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
from uuid import uuid4


class PedidoErro(Exception):
    """Exceção base para erros de processamento do pedido."""


class EstoqueInsuficienteErro(PedidoErro):
    """Indica que um ou mais itens não possuem estoque suficiente."""


class DadosInvalidosErro(PedidoErro):
    """Indica dados numéricos inválidos."""


class OpcaoNaoSuportadaErro(PedidoErro):
    """Indica uma região ou forma de pagamento não suportada."""


class TipoConta(Enum):
    COMUM = "COMUM"
    VIP = "VIP"
    CORPORATIVO = "CORPORATIVO"


class FormaPagamento(Enum):
    CARTAO = "Cartão de Crédito"
    PIX = "PIX"
    BOLETO = "Boleto"


class StatusPedido(Enum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"


@dataclass
class ItemPedido:
    id: str
    nome: str
    preco_unitario: float
    quantidade: int
    categoria: str


@dataclass
class Cliente:
    tipo_conta: TipoConta


@dataclass
class Pedido:
    id: str
    itens: List[ItemPedido]
    cliente: Cliente
    regiao_entrega: str
    forma_pagamento: FormaPagamento


@dataclass
class DetalhamentoValores:
    subtotal: float = 0.0
    taxas_categoria: float = 0.0
    desconto_cliente: float = 0.0
    desconto_pix: float = 0.0
    frete: float = 0.0
    total: float = 0.0
    opcao_beneficio: str = ""


@dataclass
class Comprovante:
    id_pedido: str
    status: StatusPedido
    valores: DetalhamentoValores = field(default_factory=DetalhamentoValores)
    mensagem: str = ""


class Estoque:
    def __init__(self, saldo: Dict[str, int]):
        self._saldo = saldo.copy()

    def validar_disponibilidade(self, itens: List[ItemPedido]) -> None:
        indisponiveis = []

        for item in itens:
            disponivel = self._saldo.get(item.id, 0)

            if disponivel < item.quantidade:
                indisponiveis.append(
                    f"{item.id} - {item.nome} "
                    f"(solicitado: {item.quantidade}, disponível: {disponivel})"
                )

        if indisponiveis:
            mensagem = (
                "Estoque insuficiente para os seguintes itens: "
                + "; ".join(indisponiveis)
            )
            raise EstoqueInsuficienteErro(mensagem)

    def reservar(self, itens: List[ItemPedido]) -> None:
        self.validar_disponibilidade(itens)

        for item in itens:
            self._saldo[item.id] -= item.quantidade

    def consultar(self, item_id: str) -> int:
        return self._saldo.get(item_id, 0)


class ValidadorPedido:
    REGIOES_SUPORTADAS = {"SP", "RJ", "OUTROS"}

    PAGAMENTOS_SUPORTADOS = {
        FormaPagamento.CARTAO,
        FormaPagamento.PIX,
        FormaPagamento.BOLETO,
    }

    def validar(self, pedido: Pedido) -> None:
        if not pedido.itens:
            raise DadosInvalidosErro("O pedido deve possuir pelo menos um item.")

        if pedido.regiao_entrega not in self.REGIOES_SUPORTADAS:
            raise OpcaoNaoSuportadaErro(
                f"Região de entrega não suportada: {pedido.regiao_entrega}"
            )

        if pedido.forma_pagamento not in self.PAGAMENTOS_SUPORTADOS:
            raise OpcaoNaoSuportadaErro(
                f"Forma de pagamento não suportada: {pedido.forma_pagamento}"
            )

        for item in pedido.itens:
            if item.preco_unitario <= 0:
                raise DadosInvalidosErro(
                    f"O preço do item '{item.nome}' deve ser maior que zero."
                )

            if item.quantidade <= 0:
                raise DadosInvalidosErro(
                    f"A quantidade do item '{item.nome}' deve ser maior que zero."
                )


class CalculadoraValores:
    FRETES = {
        "SP": 15.00,
        "RJ": 20.00,
        "OUTROS": 35.00,
    }

    TAXA_ELETRONICOS = 10.00
    LIMITE_FRETE_GRATIS = 300.00

    def calcular_subtotal(self, itens: List[ItemPedido]) -> float:
        return sum(
            item.preco_unitario * item.quantidade
            for item in itens
        )

    def calcular_taxas_categoria(self, itens: List[ItemPedido]) -> float:
        return sum(
            self.TAXA_ELETRONICOS * item.quantidade
            for item in itens
            if item.categoria.lower() == "eletrônicos"
        )

    def calcular_desconto_cliente(
        self,
        subtotal: float,
        cliente: Cliente,
    ) -> float:
        if cliente.tipo_conta == TipoConta.VIP:
            return subtotal * 0.10

        if (
            cliente.tipo_conta == TipoConta.CORPORATIVO
            and subtotal > 1000.00
        ):
            return subtotal * 0.15

        return 0.0

    def calcular_desconto_pix(
        self,
        valor_apos_desconto_cliente: float,
        forma_pagamento: FormaPagamento,
    ) -> float:
        if forma_pagamento == FormaPagamento.PIX:
            return valor_apos_desconto_cliente * 0.05

        return 0.0

    def calcular_frete(self, regiao: str) -> float:
        return self.FRETES[regiao]

    def calcular_opcao_a(
        self,
        pedido: Pedido,
    ) -> DetalhamentoValores:
        subtotal = self.calcular_subtotal(pedido.itens)
        taxas_categoria = self.calcular_taxas_categoria(pedido.itens)

        desconto_cliente = self.calcular_desconto_cliente(
            subtotal,
            pedido.cliente,
        )

        valor_apos_cliente = subtotal - desconto_cliente

        desconto_pix = self.calcular_desconto_pix(
            valor_apos_cliente,
            pedido.forma_pagamento,
        )

        valor_produtos_com_descontos = (
            valor_apos_cliente - desconto_pix
        )

        frete = self.calcular_frete(pedido.regiao_entrega)

        total = (
            valor_produtos_com_descontos
            + taxas_categoria
            + frete
        )

        return DetalhamentoValores(
            subtotal=subtotal,
            taxas_categoria=taxas_categoria,
            desconto_cliente=desconto_cliente,
            desconto_pix=desconto_pix,
            frete=frete,
            total=total,
            opcao_beneficio="A - Descontos de produtos/pagamento + frete integral",
        )

    def calcular_opcao_b(
        self,
        pedido: Pedido,
    ) -> DetalhamentoValores:
        subtotal = self.calcular_subtotal(pedido.itens)
        taxas_categoria = self.calcular_taxas_categoria(pedido.itens)

        total = subtotal + taxas_categoria

        return DetalhamentoValores(
            subtotal=subtotal,
            taxas_categoria=taxas_categoria,
            desconto_cliente=0.0,
            desconto_pix=0.0,
            frete=0.0,
            total=total,
            opcao_beneficio="B - Frete grátis + produtos sem descontos",
        )

    def calcular_melhor_opcao(
        self,
        pedido: Pedido,
    ) -> DetalhamentoValores:
        opcao_a = self.calcular_opcao_a(pedido)

        frete_gratis_elegivel = (
            (
                opcao_a.subtotal
                - opcao_a.desconto_cliente
                - opcao_a.desconto_pix
            )
            > self.LIMITE_FRETE_GRATIS
        )

        if not frete_gratis_elegivel:
            return opcao_a

        opcao_b = self.calcular_opcao_b(pedido)

        if opcao_b.total < opcao_a.total:
            return opcao_b

        return opcao_a


class ProcessadorPedido:
    def __init__(self, estoque: Estoque):
        self.estoque = estoque
        self.validador = ValidadorPedido()
        self.calculadora = CalculadoraValores()

    def processar(self, pedido: Pedido) -> Comprovante:
        try:
            self.validador.validar(pedido)

            # A validação ocorre antes de qualquer alteração no estoque.
            self.estoque.validar_disponibilidade(pedido.itens)

            valores = self.calculadora.calcular_melhor_opcao(pedido)

            # Somente depois de todas as validações e do cálculo
            # definitivo o estoque é efetivamente atualizado.
            self.estoque.reservar(pedido.itens)

            return Comprovante(
                id_pedido=pedido.id,
                status=StatusPedido.SUCESSO,
                valores=valores,
                mensagem="Pedido processado e estoque atualizado com sucesso.",
            )

        except PedidoErro as erro:
            return Comprovante(
                id_pedido=pedido.id,
                status=StatusPedido.FALHA,
                mensagem=str(erro),
            )


def imprimir_comprovante(comprovante: Comprovante) -> None:
    print("\n" + "=" * 60)
    print("COMPROVANTE DO PEDIDO")
    print("=" * 60)

    print(f"ID do pedido: {comprovante.id_pedido}")
    print(f"Status: {comprovante.status.value}")

    if comprovante.status == StatusPedido.SUCESSO:
        valores = comprovante.valores

        print(f"Subtotal: R$ {valores.subtotal:.2f}")
        print(f"Taxas de categoria: R$ {valores.taxas_categoria:.2f}")
        print(f"Desconto do cliente: R$ {valores.desconto_cliente:.2f}")
        print(f"Desconto PIX: R$ {valores.desconto_pix:.2f}")
        print(f"Frete: R$ {valores.frete:.2f}")
        print(f"Benefício selecionado: {valores.opcao_beneficio}")
        print(f"Total final: R$ {valores.total:.2f}")

    print(f"Mensagem: {comprovante.mensagem}")
    print("=" * 60)


def gerar_id_pedido() -> str:
    return str(uuid4())


if __name__ == "__main__":
    estoque = Estoque(
        {
            "P001": 10,
            "P002": 5,
            "P003": 2,
        }
    )

    processador = ProcessadorPedido(estoque)

    pedido_sucesso = Pedido(
        id=gerar_id_pedido(),
        itens=[
            ItemPedido(
                id="P001",
                nome="Notebook",
                preco_unitario=1200.00,
                quantidade=1,
                categoria="Eletrônicos",
            ),
            ItemPedido(
                id="P002",
                nome="Mouse",
                preco_unitario=100.00,
                quantidade=2,
                categoria="Acessórios",
            ),
        ],
        cliente=Cliente(tipo_conta=TipoConta.VIP),
        regiao_entrega="SP",
        forma_pagamento=FormaPagamento.PIX,
    )

    comprovante_sucesso = processador.processar(pedido_sucesso)
    imprimir_comprovante(comprovante_sucesso)

    print("\nEstoque após pedido:")
    print(f"P001: {estoque.consultar('P001')}")
    print(f"P002: {estoque.consultar('P002')}")
    print(f"P003: {estoque.consultar('P003')}")

    pedido_falha = Pedido(
        id=gerar_id_pedido(),
        itens=[
            ItemPedido(
                id="P003",
                nome="Monitor",
                preco_unitario=900.00,
                quantidade=5,
                categoria="Eletrônicos",
            ),
        ],
        cliente=Cliente(tipo_conta=TipoConta.COMUM),
        regiao_entrega="RJ",
        forma_pagamento=FormaPagamento.BOLETO,
    )

    comprovante_falha = processador.processar(pedido_falha)
    imprimir_comprovante(comprovante_falha)

    print("\nEstoque após tentativa do pedido com falha:")
    print(f"P003: {estoque.consultar('P003')}")