from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol


class PedidoError(Exception):
    """Exceção base para erros relacionados ao processamento do pedido."""


class EstoqueInsuficienteError(PedidoError):
    def __init__(self, itens_indisponiveis: list[str]) -> None:
        self.itens_indisponiveis = itens_indisponiveis

        mensagem = (
            "Estoque insuficiente para os seguintes itens: "
            + ", ".join(itens_indisponiveis)
        )

        super().__init__(mensagem)


class DadoNumericoInvalidoError(PedidoError):
    pass


class RegiaoNaoSuportadaError(PedidoError):
    pass


class FormaPagamentoNaoSuportadaError(PedidoError):
    pass


class TipoContaNaoSuportadoError(PedidoError):
    pass


@dataclass(frozen=True)
class ItemPedido:
    id: str
    nome: str
    preco_unitario: Decimal
    quantidade: int
    categoria: str

    @property
    def subtotal(self) -> Decimal:
        return self.preco_unitario * self.quantidade


@dataclass(frozen=True)
class Cliente:
    id: str
    nome: str
    tipo_conta: str


@dataclass(frozen=True)
class Pedido:
    id: str
    cliente: Cliente
    itens: list[ItemPedido]
    regiao_entrega: str
    forma_pagamento: str


@dataclass(frozen=True)
class DescontoAplicado:
    descricao: str
    percentual: Decimal
    valor: Decimal


@dataclass(frozen=True)
class ResultadoDescontos:
    subtotal_original: Decimal
    descontos: list[DescontoAplicado]
    valor_final_produtos: Decimal

    @property
    def total_descontos(self) -> Decimal:
        return sum(
            (desconto.valor for desconto in self.descontos),
            Decimal("0.00"),
        )


@dataclass(frozen=True)
class CalculoCategoria:
    descricao: str
    valor: Decimal


@dataclass(frozen=True)
class OpcaoCheckout:
    nome: str
    valor_produtos: Decimal
    taxas_categoria: Decimal
    frete: Decimal
    total: Decimal


@dataclass(frozen=True)
class Comprovante:
    id_pedido: str
    status: str
    subtotal: Decimal
    taxas_categoria: Decimal
    descontos: list[DescontoAplicado]
    frete: Decimal
    opcao_beneficio: str
    total_final: Decimal
    mensagem: str


class ValidadorPedido:
    """Responsável exclusivamente pela validação dos dados do pedido."""

    FORMAS_PAGAMENTO_SUPORTADAS = {
        "Cartão de Crédito",
        "PIX",
        "Boleto",
    }

    REGIOES_SUPORTADAS = {
        "SP",
        "RJ",
        "OUTROS",
    }

    TIPOS_CONTA_SUPORTADOS = {
        "COMUM",
        "VIP",
        "CORPORATIVO",
    }

    def validar(self, pedido: Pedido) -> None:
        self._validar_itens(pedido.itens)
        self._validar_pagamento(pedido.forma_pagamento)
        self._validar_regiao(pedido.regiao_entrega)
        self._validar_tipo_conta(pedido.cliente.tipo_conta)

    def _validar_itens(self, itens: list[ItemPedido]) -> None:
        for item in itens:
            if item.preco_unitario <= Decimal("0"):
                raise DadoNumericoInvalidoError(
                    f"O preço do item '{item.nome}' deve ser maior que zero."
                )

            if item.quantidade <= 0:
                raise DadoNumericoInvalidoError(
                    f"A quantidade do item '{item.nome}' deve ser maior que zero."
                )

    def _validar_pagamento(self, forma_pagamento: str) -> None:
        if forma_pagamento not in self.FORMAS_PAGAMENTO_SUPORTADAS:
            raise FormaPagamentoNaoSuportadaError(
                f"Forma de pagamento não suportada: {forma_pagamento}"
            )

    def _validar_regiao(self, regiao: str) -> None:
        if regiao not in self.REGIOES_SUPORTADAS:
            raise RegiaoNaoSuportadaError(
                f"Região não suportada: {regiao}"
            )

    def _validar_tipo_conta(self, tipo_conta: str) -> None:
        if tipo_conta not in self.TIPOS_CONTA_SUPORTADOS:
            raise TipoContaNaoSuportadoError(
                f"Tipo de conta não suportado: {tipo_conta}"
            )


class EstoqueRepository(Protocol):
    def verificar_disponibilidade(
        self,
        itens: list[ItemPedido],
    ) -> list[str]:
        ...

    def reservar(self, itens: list[ItemPedido]) -> None:
        ...


class EstoqueEmMemoria:
    """Responsável exclusivamente pela consulta e atualização do estoque."""

    def __init__(self, saldos: dict[str, int]) -> None:
        self._saldos = saldos.copy()

    def verificar_disponibilidade(
        self,
        itens: list[ItemPedido],
    ) -> list[str]:
        itens_indisponiveis: list[str] = []

        for item in itens:
            saldo_disponivel = self._saldos.get(item.id, 0)

            if saldo_disponivel < item.quantidade:
                itens_indisponiveis.append(
                    f"{item.id} - {item.nome} "
                    f"(solicitado: {item.quantidade}, "
                    f"disponível: {saldo_disponivel})"
                )

        return itens_indisponiveis

    def reservar(self, itens: list[ItemPedido]) -> None:
        itens_indisponiveis = self.verificar_disponibilidade(itens)

        if itens_indisponiveis:
            raise EstoqueInsuficienteError(itens_indisponiveis)

        for item in itens:
            self._saldos[item.id] -= item.quantidade

    def consultar_saldo(self, item_id: str) -> int:
        return self._saldos.get(item_id, 0)


class RegraDesconto(ABC):
    """Abstração para novas regras de desconto."""

    @abstractmethod
    def calcular(
        self,
        pedido: Pedido,
        subtotal_atual: Decimal,
    ) -> DescontoAplicado | None:
        pass


class DescontoClienteVip(RegraDesconto):
    def calcular(
        self,
        pedido: Pedido,
        subtotal_atual: Decimal,
    ) -> DescontoAplicado | None:
        if pedido.cliente.tipo_conta != "VIP":
            return None

        valor_desconto = subtotal_atual * Decimal("0.10")

        return DescontoAplicado(
            descricao="Desconto de cliente VIP",
            percentual=Decimal("10"),
            valor=valor_desconto,
        )


class DescontoCorporativo(RegraDesconto):
    def calcular(
        self,
        pedido: Pedido,
        subtotal_atual: Decimal,
    ) -> DescontoAplicado | None:
        if pedido.cliente.tipo_conta != "CORPORATIVO":
            return None

        if subtotal_atual <= Decimal("1000.00"):
            return None

        valor_desconto = subtotal_atual * Decimal("0.15")

        return DescontoAplicado(
            descricao="Desconto corporativo",
            percentual=Decimal("15"),
            valor=valor_desconto,
        )


class DescontoPix(RegraDesconto):
    def calcular(
        self,
        pedido: Pedido,
        subtotal_atual: Decimal,
    ) -> DescontoAplicado | None:
        if pedido.forma_pagamento != "PIX":
            return None

        valor_desconto = subtotal_atual * Decimal("0.05")

        return DescontoAplicado(
            descricao="Desconto por pagamento via PIX",
            percentual=Decimal("5"),
            valor=valor_desconto,
        )


class MotorDescontos:
    """
    Orquestra as regras de desconto.

    Novas promoções podem ser adicionadas por composição,
    sem modificar esta classe.
    """

    def __init__(self, regras: list[RegraDesconto]) -> None:
        self._regras = regras

    def calcular(self, pedido: Pedido) -> ResultadoDescontos:
        subtotal_original = sum(
            (item.subtotal for item in pedido.itens),
            Decimal("0.00"),
        )

        subtotal_atual = subtotal_original
        descontos_aplicados: list[DescontoAplicado] = []

        for regra in self._regras:
            desconto = regra.calcular(pedido, subtotal_atual)

            if desconto is None:
                continue

            descontos_aplicados.append(desconto)
            subtotal_atual -= desconto.valor

        return ResultadoDescontos(
            subtotal_original=subtotal_original,
            descontos=descontos_aplicados,
            valor_final_produtos=subtotal_atual,
        )


class RegraTaxaCategoria(ABC):
    """Abstração para regras de taxas relacionadas às categorias."""

    @abstractmethod
    def calcular(self, item: ItemPedido) -> Decimal:
        pass

    @abstractmethod
    def corresponde_ao_item(self, item: ItemPedido) -> bool:
        pass


class TaxaEletronicos(RegraTaxaCategoria):
    TAXA_POR_UNIDADE = Decimal("10.00")

    def corresponde_ao_item(self, item: ItemPedido) -> bool:
        return item.categoria == "Eletrônicos"

    def calcular(self, item: ItemPedido) -> Decimal:
        return self.TAXA_POR_UNIDADE * item.quantidade


class CalculadoraTaxasCategoria:
    """
    Calcula taxas adicionais por categoria.

    Novas categorias podem ser adicionadas criando novas
    implementações de RegraTaxaCategoria.
    """

    def __init__(
        self,
        regras: list[RegraTaxaCategoria],
    ) -> None:
        self._regras = regras

    def calcular(self, itens: list[ItemPedido]) -> list[CalculoCategoria]:
        resultados: list[CalculoCategoria] = []

        for item in itens:
            for regra in self._regras:
                if not regra.corresponde_ao_item(item):
                    continue

                valor = regra.calcular(item)

                resultados.append(
                    CalculoCategoria(
                        descricao=(
                            f"Taxa de categoria: {item.nome}"
                        ),
                        valor=valor,
                    )
                )

        return resultados


class CalculadoraFrete(ABC):
    """Abstração para estratégias de cálculo de frete."""

    @abstractmethod
    def suporta(self, regiao: str) -> bool:
        pass

    @abstractmethod
    def calcular(self) -> Decimal:
        pass


class FreteSaoPaulo(CalculadoraFrete):
    def suporta(self, regiao: str) -> bool:
        return regiao == "SP"

    def calcular(self) -> Decimal:
        return Decimal("15.00")


class FreteRioDeJaneiro(CalculadoraFrete):
    def suporta(self, regiao: str) -> bool:
        return regiao == "RJ"

    def calcular(self) -> Decimal:
        return Decimal("20.00")


class FreteOutrasRegioes(CalculadoraFrete):
    def suporta(self, regiao: str) -> bool:
        return regiao == "OUTROS"

    def calcular(self) -> Decimal:
        return Decimal("35.00")


class CalculadoraFretePorRegiao:
    """
    Localiza a estratégia de frete apropriada para a região.

    Novas regiões podem ser incluídas adicionando uma nova
    implementação de CalculadoraFrete.
    """

    def __init__(
        self,
        estrategias: list[CalculadoraFrete],
    ) -> None:
        self._estrategias = estrategias

    def calcular(self, regiao: str) -> Decimal:
        for estrategia in self._estrategias:
            if estrategia.suporta(regiao):
                return estrategia.calcular()

        raise RegiaoNaoSuportadaError(
            f"Não existe estratégia de frete para a região: {regiao}"
        )


class SeletorBeneficioFrete:
    """
    Compara as duas alternativas permitidas pela regra de negócio.

    Opção A:
    Produtos com descontos + taxas de categoria + frete integral.

    Opção B:
    Produtos sem descontos + taxas de categoria + frete grátis.

    A Opção B somente existe quando os produtos após os descontos
    ultrapassam R$ 300,00.
    """

    LIMITE_FRETE_GRATIS = Decimal("300.00")

    def selecionar(
        self,
        subtotal_original: Decimal,
        valor_produtos_com_desconto: Decimal,
        taxas_categoria: Decimal,
        frete_integral: Decimal,
    ) -> OpcaoCheckout:
        opcao_a = self._criar_opcao_a(
            valor_produtos_com_desconto,
            taxas_categoria,
            frete_integral,
        )

        if valor_produtos_com_desconto <= self.LIMITE_FRETE_GRATIS:
            return opcao_a

        opcao_b = self._criar_opcao_b(
            subtotal_original,
            taxas_categoria,
        )

        return min(
            (opcao_a, opcao_b),
            key=lambda opcao: opcao.total,
        )

    def _criar_opcao_a(
        self,
        valor_produtos: Decimal,
        taxas_categoria: Decimal,
        frete: Decimal,
    ) -> OpcaoCheckout:
        total = valor_produtos + taxas_categoria + frete

        return OpcaoCheckout(
            nome="A - Descontos + frete integral",
            valor_produtos=valor_produtos,
            taxas_categoria=taxas_categoria,
            frete=frete,
            total=total,
        )

    def _criar_opcao_b(
        self,
        subtotal_original: Decimal,
        taxas_categoria: Decimal,
    ) -> OpcaoCheckout:
        total = subtotal_original + taxas_categoria

        return OpcaoCheckout(
            nome="B - Frete grátis + produtos sem descontos",
            valor_produtos=subtotal_original,
            taxas_categoria=taxas_categoria,
            frete=Decimal("0.00"),
            total=total,
        )


class GeradorComprovante:
    """Responsável exclusivamente pela criação do comprovante."""

    def gerar_sucesso(
        self,
        pedido: Pedido,
        resultado_descontos: ResultadoDescontos,
        taxas_categoria: list[CalculoCategoria],
        opcao: OpcaoCheckout,
    ) -> Comprovante:
        return Comprovante(
            id_pedido=pedido.id,
            status="SUCESSO",
            subtotal=resultado_descontos.subtotal_original,
            taxas_categoria=sum(
                (taxa.valor for taxa in taxas_categoria),
                Decimal("0.00"),
            ),
            descontos=resultado_descontos.descontos,
            frete=opcao.frete,
            opcao_beneficio=opcao.nome,
            total_final=opcao.total,
            mensagem="Pedido processado com sucesso.",
        )

    def gerar_falha(
        self,
        pedido_id: str,
        erro: Exception,
    ) -> Comprovante:
        return Comprovante(
            id_pedido=pedido_id,
            status="FALHA",
            subtotal=Decimal("0.00"),
            taxas_categoria=Decimal("0.00"),
            descontos=[],
            frete=Decimal("0.00"),
            opcao_beneficio="NENHUMA",
            total_final=Decimal("0.00"),
            mensagem=str(erro),
        )


class CheckoutService:
    """
    Orquestra o processo de checkout.

    Esta classe não conhece os detalhes das regras de negócio.
    Ela apenas coordena os componentes especializados.
    """

    def __init__(
        self,
        validador: ValidadorPedido,
        estoque: EstoqueRepository,
        motor_descontos: MotorDescontos,
        calculadora_taxas: CalculadoraTaxasCategoria,
        calculadora_frete: CalculadoraFretePorRegiao,
        seletor_beneficio: SeletorBeneficioFrete,
        gerador_comprovante: GeradorComprovante,
    ) -> None:
        self._validador = validador
        self._estoque = estoque
        self._motor_descontos = motor_descontos
        self._calculadora_taxas = calculadora_taxas
        self._calculadora_frete = calculadora_frete
        self._seletor_beneficio = seletor_beneficio
        self._gerador_comprovante = gerador_comprovante

    def processar(self, pedido: Pedido) -> Comprovante:
        self._validador.validar(pedido)

        itens_indisponiveis = self._estoque.verificar_disponibilidade(
            pedido.itens
        )

        if itens_indisponiveis:
            raise EstoqueInsuficienteError(itens_indisponiveis)

        resultado_descontos = self._motor_descontos.calcular(pedido)

        taxas_categoria = self._calculadora_taxas.calcular(
            pedido.itens
        )

        total_taxas_categoria = sum(
            (taxa.valor for taxa in taxas_categoria),
            Decimal("0.00"),
        )

        frete_integral = self._calculadora_frete.calcular(
            pedido.regiao_entrega
        )

        opcao_selecionada = self._seletor_beneficio.selecionar(
            subtotal_original=resultado_descontos.subtotal_original,
            valor_produtos_com_desconto=(
                resultado_descontos.valor_final_produtos
            ),
            taxas_categoria=total_taxas_categoria,
            frete_integral=frete_integral,
        )

        self._estoque.reservar(pedido.itens)

        return self._gerador_comprovante.gerar_sucesso(
            pedido=pedido,
            resultado_descontos=resultado_descontos,
            taxas_categoria=taxas_categoria,
            opcao=opcao_selecionada,
        )


def decimal(valor: str) -> Decimal:
    """Converte valores monetários para Decimal."""
    try:
        return Decimal(valor)
    except InvalidOperation as erro:
        raise DadoNumericoInvalidoError(
            f"Valor numérico inválido: {valor}"
        ) from erro


def criar_checkout(estoque: EstoqueRepository) -> CheckoutService:
    """Monta as dependências da aplicação."""

    validador = ValidadorPedido()

    motor_descontos = MotorDescontos(
        regras=[
            DescontoClienteVip(),
            DescontoCorporativo(),
            DescontoPix(),
        ]
    )

    calculadora_taxas = CalculadoraTaxasCategoria(
        regras=[
            TaxaEletronicos(),
        ]
    )

    calculadora_frete = CalculadoraFretePorRegiao(
        estrategias=[
            FreteSaoPaulo(),
            FreteRioDeJaneiro(),
            FreteOutrasRegioes(),
        ]
    )

    seletor_beneficio = SeletorBeneficioFrete()
    gerador_comprovante = GeradorComprovante()

    return CheckoutService(
        validador=validador,
        estoque=estoque,
        motor_descontos=motor_descontos,
        calculadora_taxas=calculadora_taxas,
        calculadora_frete=calculadora_frete,
        seletor_beneficio=seletor_beneficio,
        gerador_comprovante=gerador_comprovante,
    )


def exibir_comprovante(comprovante: Comprovante) -> None:
    print("\nCOMPROVANTE")
    print(f"Pedido: {comprovante.id_pedido}")
    print(f"Status: {comprovante.status}")
    print(f"Subtotal: R$ {comprovante.subtotal:.2f}")
    print(
        f"Taxas de categoria: "
        f"R$ {comprovante.taxas_categoria:.2f}"
    )

    if comprovante.descontos:
        print("Descontos:")

        for desconto in comprovante.descontos:
            print(
                f"  {desconto.descricao}: "
                f"- R$ {desconto.valor:.2f}"
            )
    else:
        print("Descontos: nenhum")

    print(f"Frete: R$ {comprovante.frete:.2f}")
    print(
        f"Benefício selecionado: "
        f"{comprovante.opcao_beneficio}"
    )
    print(f"Total final: R$ {comprovante.total_final:.2f}")
    print(f"Mensagem: {comprovante.mensagem}")


def exemplo_sucesso() -> None:
    estoque = EstoqueEmMemoria(
        saldos={
            "P001": 10,
            "P002": 20,
            "P003": 5,
        }
    )

    checkout = criar_checkout(estoque)

    cliente = Cliente(
        id="C001",
        nome="Matheus",
        tipo_conta="VIP",
    )

    pedido = Pedido(
        id="PED-001",
        cliente=cliente,
        itens=[
            ItemPedido(
                id="P001",
                nome="Notebook",
                preco_unitario=decimal("2500.00"),
                quantidade=1,
                categoria="Eletrônicos",
            ),
            ItemPedido(
                id="P002",
                nome="Mouse",
                preco_unitario=decimal("100.00"),
                quantidade=2,
                categoria="Acessórios",
            ),
        ],
        regiao_entrega="SP",
        forma_pagamento="PIX",
    )

    comprovante = checkout.processar(pedido)

    exibir_comprovante(comprovante)

    print(
        f"\nSaldo restante do Notebook: "
        f"{estoque.consultar_saldo('P001')}"
    )


def exemplo_falha_estoque() -> None:
    estoque = EstoqueEmMemoria(
        saldos={
            "P001": 2,
        }
    )

    checkout = criar_checkout(estoque)

    cliente = Cliente(
        id="C002",
        nome="Cliente Teste",
        tipo_conta="COMUM",
    )

    pedido = Pedido(
        id="PED-002",
        cliente=cliente,
        itens=[
            ItemPedido(
                id="P001",
                nome="Notebook",
                preco_unitario=decimal("3000.00"),
                quantidade=5,
                categoria="Eletrônicos",
            ),
        ],
        regiao_entrega="RJ",
        forma_pagamento="Boleto",
    )

    try:
        checkout.processar(pedido)

    except EstoqueInsuficienteError as erro:
        gerador = GeradorComprovante()

        comprovante = gerador.gerar_falha(
            pedido_id=pedido.id,
            erro=erro,
        )

        exibir_comprovante(comprovante)


if __name__ == "__main__":
    print("===== FLUXO DE SUCESSO =====")
    exemplo_sucesso()

    print("\n===== FLUXO DE FALHA =====")
    exemplo_falha_estoque()