"""
Sistema de Processamento e Checkout de Pedidos - E-commerce
=============================================================

Implementa validação de estoque, precificação por categoria, descontos por
tipo de cliente e forma de pagamento, cálculo de frete e a regra de
prevalência (não cumulatividade) entre descontos de produto e frete grátis.

Autor: gerado sob demanda.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Enumerações
# ---------------------------------------------------------------------------

class TipoConta(str, Enum):
    COMUM = "COMUM"
    VIP = "VIP"
    CORPORATIVO = "CORPORATIVO"


class FormaPagamento(str, Enum):
    CARTAO_CREDITO = "CARTAO_CREDITO"
    PIX = "PIX"
    BOLETO = "BOLETO"


class Regiao(str, Enum):
    SP = "SP"
    RJ = "RJ"
    OUTROS = "OUTROS"


class StatusPedido(str, Enum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"


# ---------------------------------------------------------------------------
# Exceções customizadas
# ---------------------------------------------------------------------------

class PedidoError(Exception):
    """Classe base para todos os erros de processamento de pedido."""


class DadosInvalidosError(PedidoError):
    """Levantada quando preço ou quantidade são inválidos (<= 0)."""


class EstoqueInsuficienteError(PedidoError):
    """Levantada quando um ou mais itens não possuem saldo suficiente."""

    def __init__(self, itens_indisponiveis: List["ItemIndisponivel"]):
        self.itens_indisponiveis = itens_indisponiveis
        detalhes = ", ".join(
            f"{i.item_id} ({i.nome}): solicitado={i.quantidade_solicitada}, "
            f"disponível={i.quantidade_disponivel}"
            for i in itens_indisponiveis
        )
        super().__init__(f"Estoque insuficiente para os itens: {detalhes}")


class PagamentoNaoSuportadoError(PedidoError):
    """Levantada quando a forma de pagamento informada não é suportada."""


class RegiaoNaoSuportadaError(PedidoError):
    """Levantada quando a região de entrega informada não é suportada."""


class ItemNaoCadastradoError(PedidoError):
    """Levantada quando um item do pedido não existe no cadastro de estoque."""


# ---------------------------------------------------------------------------
# Entidades de domínio
# ---------------------------------------------------------------------------

@dataclass
class ItemIndisponivel:
    item_id: str
    nome: str
    quantidade_solicitada: int
    quantidade_disponivel: int


@dataclass
class ItemPedido:
    item_id: str
    nome: str
    preco_unitario: float
    quantidade: int
    categoria: str

    def validar(self) -> None:
        if self.preco_unitario <= 0:
            raise DadosInvalidosError(
                f"Preço unitário inválido para o item '{self.item_id}': "
                f"{self.preco_unitario}. Deve ser maior que zero."
            )
        if self.quantidade <= 0:
            raise DadosInvalidosError(
                f"Quantidade inválida para o item '{self.item_id}': "
                f"{self.quantidade}. Deve ser maior que zero."
            )

    @property
    def valor_total(self) -> float:
        return round(self.preco_unitario * self.quantidade, 2)

    @property
    def eh_eletronico(self) -> bool:
        return self.categoria.strip().upper() == "ELETRÔNICOS" or \
            self.categoria.strip().upper() == "ELETRONICOS"


@dataclass
class Cliente:
    nome: str
    tipo_conta: TipoConta


@dataclass
class Pedido:
    pedido_id: str
    cliente: Cliente
    itens: List[ItemPedido]
    regiao: Regiao
    forma_pagamento: FormaPagamento


@dataclass
class Comprovante:
    pedido_id: str
    status: StatusPedido
    subtotal: float = 0.0
    taxa_categoria: float = 0.0
    desconto_cliente: float = 0.0
    desconto_pix: float = 0.0
    valor_frete: float = 0.0
    opcao_selecionada: Optional[str] = None  # "A" (descontos) ou "B" (frete grátis)
    total_final: float = 0.0
    mensagem_erro: Optional[str] = None

    def imprimir(self) -> None:
        print("=" * 55)
        print(f"Comprovante do Pedido: {self.pedido_id}")
        print(f"Status: {self.status.value}")
        if self.status == StatusPedido.FALHA:
            print(f"Motivo: {self.mensagem_erro}")
        else:
            print(f"Subtotal dos produtos:      R$ {self.subtotal:.2f}")
            print(f"Taxa de categoria:           R$ {self.taxa_categoria:.2f}")
            print(f"Desconto de cliente:        -R$ {self.desconto_cliente:.2f}")
            print(f"Desconto PIX:               -R$ {self.desconto_pix:.2f}")
            print(f"Frete:                       R$ {self.valor_frete:.2f}")
            print(f"Opção vantajosa aplicada:    {self.opcao_selecionada}")
            print(f"TOTAL FINAL:                 R$ {self.total_final:.2f}")
        print("=" * 55)


# ---------------------------------------------------------------------------
# Serviço de estoque (simulado em memória)
# ---------------------------------------------------------------------------

class EstoqueService:
    def __init__(self, estoque_inicial: Dict[str, int]):
        # item_id -> quantidade disponível
        self._estoque: Dict[str, int] = dict(estoque_inicial)

    def consultar(self, item_id: str) -> int:
        if item_id not in self._estoque:
            raise ItemNaoCadastradoError(
                f"Item '{item_id}' não encontrado no cadastro de estoque."
            )
        return self._estoque[item_id]

    def validar_disponibilidade(self, itens: List[ItemPedido]) -> None:
        indisponiveis: List[ItemIndisponivel] = []
        for item in itens:
            disponivel = self.consultar(item.item_id)
            if disponivel < item.quantidade:
                indisponiveis.append(
                    ItemIndisponivel(
                        item_id=item.item_id,
                        nome=item.nome,
                        quantidade_solicitada=item.quantidade,
                        quantidade_disponivel=disponivel,
                    )
                )
        if indisponiveis:
            raise EstoqueInsuficienteError(indisponiveis)

    def deduzir(self, itens: List[ItemPedido]) -> None:
        for item in itens:
            self._estoque[item.item_id] -= item.quantidade

    def snapshot(self) -> Dict[str, int]:
        return dict(self._estoque)


# ---------------------------------------------------------------------------
# Processador de pedidos (regras de negócio)
# ---------------------------------------------------------------------------

class ProcessadorPedidos:
    TAXA_ELETRONICO_UNITARIO = 10.00
    LIMIAR_FRETE_GRATIS = 300.00
    LIMIAR_DESCONTO_CORPORATIVO = 1000.00
    PERCENTUAL_DESCONTO_VIP = 0.10
    PERCENTUAL_DESCONTO_CORPORATIVO = 0.15
    PERCENTUAL_DESCONTO_PIX = 0.05

    FRETE_POR_REGIAO = {
        Regiao.SP: 15.00,
        Regiao.RJ: 20.00,
        Regiao.OUTROS: 35.00,
    }

    def __init__(self, estoque_service: EstoqueService):
        self.estoque_service = estoque_service

    # -- Validações -----------------------------------------------------

    def _validar_pedido(self, pedido: Pedido) -> None:
        if not pedido.itens:
            raise DadosInvalidosError("O pedido não possui itens.")

        for item in pedido.itens:
            item.validar()

        if pedido.forma_pagamento not in FormaPagamento:
            raise PagamentoNaoSuportadoError(
                f"Forma de pagamento não suportada: {pedido.forma_pagamento}"
            )

        if pedido.regiao not in self.FRETE_POR_REGIAO:
            raise RegiaoNaoSuportadaError(
                f"Região de entrega não suportada: {pedido.regiao}"
            )

    # -- Cálculos ---------------------------------------------------------

    def _calcular_subtotal(self, itens: List[ItemPedido]) -> float:
        return round(sum(item.valor_total for item in itens), 2)

    def _calcular_taxa_categoria(self, itens: List[ItemPedido]) -> float:
        total = sum(
            self.TAXA_ELETRONICO_UNITARIO * item.quantidade
            for item in itens
            if item.eh_eletronico
        )
        return round(total, 2)

    def _calcular_desconto_cliente(
        self, subtotal: float, tipo_conta: TipoConta
    ) -> float:
        if tipo_conta == TipoConta.VIP:
            return round(subtotal * self.PERCENTUAL_DESCONTO_VIP, 2)
        if tipo_conta == TipoConta.CORPORATIVO:
            if subtotal > self.LIMIAR_DESCONTO_CORPORATIVO:
                return round(subtotal * self.PERCENTUAL_DESCONTO_CORPORATIVO, 2)
        return 0.0

    def _montar_opcao_a(self, pedido: Pedido, subtotal: float, taxa_categoria: float):
        """Opção A: aplica descontos de cliente/PIX + frete integral da região."""
        desconto_cliente = self._calcular_desconto_cliente(
            subtotal, pedido.cliente.tipo_conta
        )
        valor_pos_cliente = subtotal - desconto_cliente

        desconto_pix = 0.0
        if pedido.forma_pagamento == FormaPagamento.PIX:
            desconto_pix = round(valor_pos_cliente * self.PERCENTUAL_DESCONTO_PIX, 2)

        valor_produtos_final = round(valor_pos_cliente - desconto_pix, 2)
        frete = self.FRETE_POR_REGIAO[pedido.regiao]
        total = round(valor_produtos_final + taxa_categoria + frete, 2)

        return {
            "opcao": "A",
            "desconto_cliente": desconto_cliente,
            "desconto_pix": desconto_pix,
            "frete": frete,
            "total": total,
        }

    def _montar_opcao_b(self, pedido: Pedido, subtotal: float, taxa_categoria: float):
        """Opção B: frete grátis (se elegível), produtos em valor integral."""
        elegivel_frete_gratis = subtotal > self.LIMIAR_FRETE_GRATIS
        frete = 0.0 if elegivel_frete_gratis else self.FRETE_POR_REGIAO[pedido.regiao]
        total = round(subtotal + taxa_categoria + frete, 2)

        return {
            "opcao": "B",
            "desconto_cliente": 0.0,
            "desconto_pix": 0.0,
            "frete": frete,
            "total": total,
        }

    # -- Orquestração -----------------------------------------------------

    def processar_pedido(self, pedido: Pedido) -> Comprovante:
        """
        Processa o pedido de ponta a ponta. Levanta as exceções específicas
        (DadosInvalidosError, EstoqueInsuficienteError,
        PagamentoNaoSuportadoError, RegiaoNaoSuportadaError,
        ItemNaoCadastradoError) em caso de falha.
        """
        # 1. Validações estruturais e de dados
        self._validar_pedido(pedido)

        # 2. Validação e reserva de estoque (tudo ou nada)
        self.estoque_service.validar_disponibilidade(pedido.itens)

        # 3. Cálculo de subtotal e taxa de categoria
        subtotal = self._calcular_subtotal(pedido.itens)
        taxa_categoria = self._calcular_taxa_categoria(pedido.itens)

        # 4. Monta as duas opções concorrentes (não cumulativas)
        opcao_a = self._montar_opcao_a(pedido, subtotal, taxa_categoria)
        opcao_b = self._montar_opcao_b(pedido, subtotal, taxa_categoria)

        # 5. Escolhe automaticamente a de menor total (empate -> A)
        melhor = opcao_a if opcao_a["total"] <= opcao_b["total"] else opcao_b

        # 6. Efetiva a baixa de estoque somente após decisão tomada
        self.estoque_service.deduzir(pedido.itens)

        # 7. Gera o comprovante de sucesso
        return Comprovante(
            pedido_id=pedido.pedido_id,
            status=StatusPedido.SUCESSO,
            subtotal=subtotal,
            taxa_categoria=taxa_categoria,
            desconto_cliente=melhor["desconto_cliente"],
            desconto_pix=melhor["desconto_pix"],
            valor_frete=melhor["frete"],
            opcao_selecionada=melhor["opcao"],
            total_final=melhor["total"],
        )

    def checkout_seguro(self, pedido: Pedido) -> Comprovante:
        """
        Wrapper que nunca propaga exceção: captura os erros de negócio
        conhecidos e devolve um Comprovante com status FALHA e mensagem
        explicativa, adequado para camadas de API/apresentação.
        """
        try:
            return self.processar_pedido(pedido)
        except PedidoError as erro:
            return Comprovante(
                pedido_id=pedido.pedido_id,
                status=StatusPedido.FALHA,
                mensagem_erro=str(erro),
            )


# ---------------------------------------------------------------------------
# Exemplo de uso executável
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Cadastro de estoque simulado em memória (item_id -> quantidade)
    estoque_inicial = {
        "SKU-001": 10,   # Notebook (Eletrônicos)
        "SKU-002": 5,    # Mouse (Eletrônicos)
        "SKU-003": 50,   # Camiseta (Vestuário)
        "SKU-004": 2,    # Cadeira Gamer (Eletrônicos)
    }

    estoque_service = EstoqueService(estoque_inicial)
    processador = ProcessadorPedidos(estoque_service)

    print("\n--- CASO 1: Fluxo de SUCESSO (Cliente VIP, pagamento PIX) ---\n")

    cliente_vip = Cliente(nome="Ana Silva", tipo_conta=TipoConta.VIP)
    pedido_sucesso = Pedido(
        pedido_id="PED-1001",
        cliente=cliente_vip,
        itens=[
            ItemPedido("SKU-001", "Notebook", 3500.00, 1, "Eletrônicos"),
            ItemPedido("SKU-002", "Mouse sem fio", 150.00, 2, "Eletrônicos"),
            ItemPedido("SKU-003", "Camiseta Básica", 60.00, 3, "Vestuário"),
        ],
        regiao=Regiao.SP,
        forma_pagamento=FormaPagamento.PIX,
    )

    comprovante_sucesso = processador.processar_pedido(pedido_sucesso)
    comprovante_sucesso.imprimir()
    print(f"Estoque após a compra: {estoque_service.snapshot()}\n")

    print("\n--- CASO 2: Fluxo de FALHA (estoque insuficiente) tratado com try/except ---\n")

    cliente_comum = Cliente(nome="Carlos Souza", tipo_conta=TipoConta.COMUM)
    pedido_falha_estoque = Pedido(
        pedido_id="PED-1002",
        cliente=cliente_comum,
        itens=[
            ItemPedido("SKU-004", "Cadeira Gamer", 1200.00, 5, "Eletrônicos"),
        ],
        regiao=Regiao.RJ,
        forma_pagamento=FormaPagamento.BOLETO,
    )

    try:
        processador.processar_pedido(pedido_falha_estoque)
    except EstoqueInsuficienteError as erro:
        print(f"Falha ao processar PED-1002: {erro}")

    print("\n--- CASO 3: Mesmo cenário de falha, usando checkout_seguro (não propaga exceção) ---\n")

    comprovante_falha = processador.checkout_seguro(pedido_falha_estoque)
    comprovante_falha.imprimir()

    print("\n--- CASO 4: FALHA por dado inválido (preço <= 0) ---\n")

    pedido_dado_invalido = Pedido(
        pedido_id="PED-1003",
        cliente=cliente_comum,
        itens=[
            ItemPedido("SKU-003", "Camiseta Básica", -10.00, 1, "Vestuário"),
        ],
        regiao=Regiao.OUTROS,
        forma_pagamento=FormaPagamento.CARTAO_CREDITO,
    )

    comprovante_dado_invalido = processador.checkout_seguro(pedido_dado_invalido)
    comprovante_dado_invalido.imprimir()

    print("\n--- CASO 5: Cliente COMUM sem desconto -> Opção B (frete grátis) vence ---\n")

    # Sem desconto de cliente (COMUM) e sem PIX, a Opção A só teria o frete
    # normal da região. Como o subtotal ultrapassa R$300, a Opção B (frete
    # grátis) resulta em um total menor e é escolhida automaticamente.
    pedido_comum = Pedido(
        pedido_id="PED-1004",
        cliente=cliente_comum,
        itens=[
            ItemPedido("SKU-003", "Camiseta Básica", 60.00, 6, "Vestuário"),  # 360,00
        ],
        regiao=Regiao.OUTROS,
        forma_pagamento=FormaPagamento.CARTAO_CREDITO,
    )

    comprovante_comum = processador.processar_pedido(pedido_comum)
    comprovante_comum.imprimir()

    print("\n--- CASO 6: Cliente CORPORATIVO acima de R$1000 -> desconto (Opção A) vence o frete grátis ---\n")

    cliente_corp = Cliente(nome="Empresa XPTO Ltda", tipo_conta=TipoConta.CORPORATIVO)
    pedido_corp = Pedido(
        pedido_id="PED-1005",
        cliente=cliente_corp,
        itens=[
            ItemPedido("SKU-003", "Camiseta Básica", 60.00, 20, "Vestuário"),  # 1200,00
        ],
        regiao=Regiao.OUTROS,
        forma_pagamento=FormaPagamento.CARTAO_CREDITO,
    )

    comprovante_corp = processador.processar_pedido(pedido_corp)
    comprovante_corp.imprimir()