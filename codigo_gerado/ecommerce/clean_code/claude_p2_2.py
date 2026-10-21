"""
Sistema de Processamento e Checkout de Pedidos de E-commerce
==============================================================

Arquitetura orientada a SRP (Single Responsibility Principle) e OCP
(Open/Closed Principle):

- Gestão de estoque:            RepositorioEstoque, ValidadorDeEstoque,
                                 AtualizadorDeEstoque
- Taxas de categoria de item:   RegistroDeTaxasPorCategoria (+ calculadoras)
- Descontos de cliente:         FabricaDeDescontoDeCliente (+ estratégias)
- Descontos de pagamento:       FabricaDeDescontoDePagamento (+ estratégias)
- Cálculo de frete:             RegistroDeFretePorRegiao (+ calculadoras)
- Regra de frete grátis:        RegraDeFreteGratis
- Orquestração de preços:       CalculadoraDePedido
- Geração de comprovante:       GeradorDeComprovante
- Orquestração do checkout:     ServicoDeCheckout

Novas regiões, categorias ou regras de desconto são adicionadas
registrando novos componentes nos registries/fábricas, sem alterar
nenhuma classe existente.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Dict, List, Optional, Protocol


# ---------------------------------------------------------------------------
# Exceções de domínio
# ---------------------------------------------------------------------------

class ErroDePedido(Exception):
    """Exceção base para todos os erros de domínio do checkout."""


class DadosDoItemInvalidosError(ErroDePedido):
    def __init__(self, id_produto: str, motivo: str) -> None:
        super().__init__(f"Item '{id_produto}' possui dados inválidos: {motivo}")


class EstoqueInsuficienteError(ErroDePedido):
    def __init__(self, itens_indisponiveis: Dict[str, int]) -> None:
        detalhes = ", ".join(
            f"{id_produto} (faltam {quantidade_faltante} un.)"
            for id_produto, quantidade_faltante in itens_indisponiveis.items()
        )
        super().__init__(f"Estoque insuficiente para os itens: {detalhes}")
        self.itens_indisponiveis = itens_indisponiveis


class RegiaoNaoSuportadaError(ErroDePedido):
    def __init__(self, regiao: str) -> None:
        super().__init__(f"Região de entrega não suportada: '{regiao}'")


class FormaPagamentoNaoSuportadaError(ErroDePedido):
    def __init__(self, forma_pagamento: str) -> None:
        super().__init__(f"Forma de pagamento não suportada: '{forma_pagamento}'")


class TipoClienteNaoSuportadoError(ErroDePedido):
    def __init__(self, tipo_cliente: str) -> None:
        super().__init__(f"Tipo de cliente não suportado: '{tipo_cliente}'")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TipoCliente(str, Enum):
    COMUM = "COMUM"
    VIP = "VIP"
    CORPORATIVO = "CORPORATIVO"


class Regiao(str, Enum):
    SP = "SP"
    RJ = "RJ"
    OUTROS = "OUTROS"


class FormaPagamento(str, Enum):
    CARTAO_CREDITO = "Cartão de Crédito"
    PIX = "PIX"
    BOLETO = "Boleto"


class OpcaoDeBeneficio(str, Enum):
    DESCONTOS_APLICADOS = "DESCONTOS_DE_PRODUTO_COM_FRETE_INTEGRAL"
    FRETE_GRATIS_SEM_DESCONTOS = "FRETE_GRATIS_SEM_DESCONTOS_DE_PRODUTO"


class StatusPedido(str, Enum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"


# ---------------------------------------------------------------------------
# Utilitário monetário
# ---------------------------------------------------------------------------

def _arredondar_moeda(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _formatar_moeda(valor: Optional[Decimal]) -> str:
    if valor is None:
        return "-"
    return f"R$ {valor:.2f}"


# ---------------------------------------------------------------------------
# Entidades do pedido
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ItemPedido:
    id_produto: str
    nome: str
    preco_unitario: Decimal
    quantidade: int
    categoria: str

    def __post_init__(self) -> None:
        if self.preco_unitario <= 0:
            raise DadosDoItemInvalidosError(self.id_produto, "preço deve ser maior que zero")
        if self.quantidade <= 0:
            raise DadosDoItemInvalidosError(self.id_produto, "quantidade deve ser maior que zero")

    @property
    def subtotal(self) -> Decimal:
        return _arredondar_moeda(self.preco_unitario * self.quantidade)


@dataclass(frozen=True)
class DadosPedido:
    id_pedido: str
    itens: List[ItemPedido]
    tipo_cliente: TipoCliente
    regiao: Regiao
    forma_pagamento: FormaPagamento


# ---------------------------------------------------------------------------
# Interpretação de dados de entrada (strings -> Enums do domínio)
# ---------------------------------------------------------------------------

def interpretar_tipo_cliente(valor: str) -> TipoCliente:
    try:
        return TipoCliente(valor)
    except ValueError as erro:
        raise TipoClienteNaoSuportadoError(valor) from erro


def interpretar_regiao(valor: str) -> Regiao:
    try:
        return Regiao(valor)
    except ValueError as erro:
        raise RegiaoNaoSuportadaError(valor) from erro


def interpretar_forma_pagamento(valor: str) -> FormaPagamento:
    try:
        return FormaPagamento(valor)
    except ValueError as erro:
        raise FormaPagamentoNaoSuportadaError(valor) from erro


# ---------------------------------------------------------------------------
# SRP: Gestão de estoque
# ---------------------------------------------------------------------------

class RepositorioEstoque:
    """Responsável exclusivamente por manter e consultar o saldo de estoque."""

    def __init__(self, saldo_inicial: Dict[str, int]) -> None:
        self._saldo: Dict[str, int] = dict(saldo_inicial)

    def saldo_disponivel(self, id_produto: str) -> int:
        return self._saldo.get(id_produto, 0)

    def debitar(self, id_produto: str, quantidade: int) -> None:
        self._saldo[id_produto] = self.saldo_disponivel(id_produto) - quantidade


class ValidadorDeEstoque:
    """Responsável exclusivamente por validar a disponibilidade dos itens do pedido."""

    def __init__(self, repositorio_estoque: RepositorioEstoque) -> None:
        self._repositorio_estoque = repositorio_estoque

    def validar(self, itens: List[ItemPedido]) -> None:
        itens_indisponiveis: Dict[str, int] = {}
        for item in itens:
            saldo = self._repositorio_estoque.saldo_disponivel(item.id_produto)
            if saldo < item.quantidade:
                itens_indisponiveis[item.id_produto] = item.quantidade - saldo
        if itens_indisponiveis:
            raise EstoqueInsuficienteError(itens_indisponiveis)


class AtualizadorDeEstoque:
    """Responsável exclusivamente por debitar do estoque os itens comprados."""

    def __init__(self, repositorio_estoque: RepositorioEstoque) -> None:
        self._repositorio_estoque = repositorio_estoque

    def confirmar_saida(self, itens: List[ItemPedido]) -> None:
        for item in itens:
            self._repositorio_estoque.debitar(item.id_produto, item.quantidade)


# ---------------------------------------------------------------------------
# OCP: Taxas de manuseio por categoria de item
# ---------------------------------------------------------------------------

class CalculadoraDeTaxaDeCategoria(Protocol):
    def calcular(self, item: ItemPedido) -> Decimal:
        ...


class SemTaxaAdicional:
    def calcular(self, item: ItemPedido) -> Decimal:
        return Decimal("0.00")


class TaxaDeManuseioPorUnidade:
    def __init__(self, valor_por_unidade: Decimal) -> None:
        self._valor_por_unidade = valor_por_unidade

    def calcular(self, item: ItemPedido) -> Decimal:
        return _arredondar_moeda(self._valor_por_unidade * item.quantidade)


class RegistroDeTaxasPorCategoria:
    """Mapeia categorias de produto para suas calculadoras de taxa.

    Novas categorias são adicionadas via `registrar`, sem alterar
    nenhuma classe existente (OCP).
    """

    def __init__(self) -> None:
        self._calculadora_padrao: CalculadoraDeTaxaDeCategoria = SemTaxaAdicional()
        self._calculadoras: Dict[str, CalculadoraDeTaxaDeCategoria] = {}

    def registrar(self, categoria: str, calculadora: CalculadoraDeTaxaDeCategoria) -> None:
        self._calculadoras[categoria] = calculadora

    def calcular_taxa_total(self, itens: List[ItemPedido]) -> Decimal:
        total = Decimal("0.00")
        for item in itens:
            calculadora = self._calculadoras.get(item.categoria, self._calculadora_padrao)
            total += calculadora.calcular(item)
        return _arredondar_moeda(total)


# ---------------------------------------------------------------------------
# OCP: Descontos por tipo de cliente
# ---------------------------------------------------------------------------

class EstrategiaDeDescontoDeCliente(Protocol):
    def calcular_desconto(self, subtotal_produtos: Decimal) -> Decimal:
        ...


class SemDescontoDeCliente:
    def calcular_desconto(self, subtotal_produtos: Decimal) -> Decimal:
        return Decimal("0.00")


class DescontoClienteVip:
    PERCENTUAL = Decimal("0.10")

    def calcular_desconto(self, subtotal_produtos: Decimal) -> Decimal:
        return _arredondar_moeda(subtotal_produtos * self.PERCENTUAL)


class DescontoClienteCorporativo:
    PERCENTUAL = Decimal("0.15")
    SUBTOTAL_MINIMO_ELEGIVEL = Decimal("1000.00")

    def calcular_desconto(self, subtotal_produtos: Decimal) -> Decimal:
        if subtotal_produtos <= self.SUBTOTAL_MINIMO_ELEGIVEL:
            return Decimal("0.00")
        return _arredondar_moeda(subtotal_produtos * self.PERCENTUAL)


class FabricaDeDescontoDeCliente:
    """Resolve a estratégia de desconto a partir do tipo de cliente.

    Novos tipos de cliente exigem apenas uma nova entrada neste
    mapeamento, sem alterar nenhuma classe existente (OCP).
    """

    _ESTRATEGIAS: Dict[TipoCliente, EstrategiaDeDescontoDeCliente] = {
        TipoCliente.COMUM: SemDescontoDeCliente(),
        TipoCliente.VIP: DescontoClienteVip(),
        TipoCliente.CORPORATIVO: DescontoClienteCorporativo(),
    }

    @classmethod
    def obter(cls, tipo_cliente: TipoCliente) -> EstrategiaDeDescontoDeCliente:
        return cls._ESTRATEGIAS[tipo_cliente]


# ---------------------------------------------------------------------------
# OCP: Descontos por forma de pagamento
# ---------------------------------------------------------------------------

class EstrategiaDeDescontoDePagamento(Protocol):
    def calcular_desconto(self, valor_restante_dos_produtos: Decimal) -> Decimal:
        ...


class SemDescontoDePagamento:
    def calcular_desconto(self, valor_restante_dos_produtos: Decimal) -> Decimal:
        return Decimal("0.00")


class DescontoPagamentoPix:
    PERCENTUAL = Decimal("0.05")

    def calcular_desconto(self, valor_restante_dos_produtos: Decimal) -> Decimal:
        return _arredondar_moeda(valor_restante_dos_produtos * self.PERCENTUAL)


class FabricaDeDescontoDePagamento:
    _ESTRATEGIAS: Dict[FormaPagamento, EstrategiaDeDescontoDePagamento] = {
        FormaPagamento.CARTAO_CREDITO: SemDescontoDePagamento(),
        FormaPagamento.PIX: DescontoPagamentoPix(),
        FormaPagamento.BOLETO: SemDescontoDePagamento(),
    }

    @classmethod
    def obter(cls, forma_pagamento: FormaPagamento) -> EstrategiaDeDescontoDePagamento:
        return cls._ESTRATEGIAS[forma_pagamento]


# ---------------------------------------------------------------------------
# OCP: Frete por região
# ---------------------------------------------------------------------------

class CalculadoraDeFrete(Protocol):
    def calcular(self) -> Decimal:
        ...


class FreteComValorFixo:
    def __init__(self, valor: Decimal) -> None:
        self._valor = valor

    def calcular(self) -> Decimal:
        return self._valor


class RegistroDeFretePorRegiao:
    """Mapeia regiões para suas calculadoras de frete.

    Novas regiões são adicionadas via `registrar`, sem alterar
    nenhuma classe existente (OCP).
    """

    def __init__(self) -> None:
        self._calculadoras: Dict[Regiao, CalculadoraDeFrete] = {}

    def registrar(self, regiao: Regiao, calculadora: CalculadoraDeFrete) -> None:
        self._calculadoras[regiao] = calculadora

    def calcular_frete(self, regiao: Regiao) -> Decimal:
        try:
            return self._calculadoras[regiao].calcular()
        except KeyError as erro:
            raise RegiaoNaoSuportadaError(str(regiao.value)) from erro


@dataclass(frozen=True)
class RegraDeFreteGratis:
    """Define o valor mínimo, após descontos, para o pedido se
    tornar elegível à alternativa de frete grátis (ver `CalculadoraDePedido`).
    """

    valor_minimo_para_elegibilidade: Decimal = Decimal("300.00")

    def elegivel(self, valor_produtos_com_descontos: Decimal) -> bool:
        return valor_produtos_com_descontos > self.valor_minimo_para_elegibilidade


# ---------------------------------------------------------------------------
# Resultado da precificação
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResultadoPrecificacao:
    subtotal_produtos: Decimal
    taxa_categoria_total: Decimal
    desconto_cliente: Decimal
    desconto_pagamento: Decimal
    valor_frete: Decimal
    opcao_selecionada: OpcaoDeBeneficio
    total_final: Decimal


# ---------------------------------------------------------------------------
# SRP: Orquestração exclusiva do cálculo de preços
# ---------------------------------------------------------------------------

class CalculadoraDePedido:
    """Calcula os valores de um pedido aplicando taxas de categoria,
    descontos de cliente/pagamento e frete.

    Regra de não cumulatividade: os descontos de produto/pagamento não
    são cumulativos com o benefício de frete grátis. Quando o pedido é
    elegível a frete grátis (valor dos produtos após descontos de
    cliente/pagamento superior ao mínimo definido em `RegraDeFreteGratis`),
    as duas alternativas são calculadas e a mais barata para o cliente é
    automaticamente selecionada.
    """

    def __init__(
        self,
        registro_taxa_categoria: RegistroDeTaxasPorCategoria,
        registro_frete: RegistroDeFretePorRegiao,
        regra_frete_gratis: RegraDeFreteGratis,
    ) -> None:
        self._registro_taxa_categoria = registro_taxa_categoria
        self._registro_frete = registro_frete
        self._regra_frete_gratis = regra_frete_gratis

    def calcular(self, pedido: DadosPedido) -> ResultadoPrecificacao:
        subtotal_produtos = self._somar_subtotal_dos_itens(pedido.itens)
        taxa_categoria_total = self._registro_taxa_categoria.calcular_taxa_total(pedido.itens)
        frete_regional = self._registro_frete.calcular_frete(pedido.regiao)

        desconto_cliente = FabricaDeDescontoDeCliente.obter(pedido.tipo_cliente).calcular_desconto(
            subtotal_produtos
        )
        valor_apos_desconto_cliente = subtotal_produtos - desconto_cliente

        desconto_pagamento = FabricaDeDescontoDePagamento.obter(pedido.forma_pagamento).calcular_desconto(
            valor_apos_desconto_cliente
        )
        valor_produtos_com_descontos = _arredondar_moeda(valor_apos_desconto_cliente - desconto_pagamento)

        opcao_com_descontos = self._montar_opcao_com_descontos(
            subtotal_produtos=subtotal_produtos,
            valor_produtos_com_descontos=valor_produtos_com_descontos,
            taxa_categoria_total=taxa_categoria_total,
            desconto_cliente=desconto_cliente,
            desconto_pagamento=desconto_pagamento,
            frete_regional=frete_regional,
        )

        if not self._regra_frete_gratis.elegivel(valor_produtos_com_descontos):
            return opcao_com_descontos

        opcao_frete_gratis = self._montar_opcao_frete_gratis(
            subtotal_produtos=subtotal_produtos,
            taxa_categoria_total=taxa_categoria_total,
        )

        return min(opcao_com_descontos, opcao_frete_gratis, key=lambda opcao: opcao.total_final)

    @staticmethod
    def _somar_subtotal_dos_itens(itens: List[ItemPedido]) -> Decimal:
        total = Decimal("0.00")
        for item in itens:
            total += item.subtotal
        return _arredondar_moeda(total)

    @staticmethod
    def _montar_opcao_com_descontos(
        subtotal_produtos: Decimal,
        valor_produtos_com_descontos: Decimal,
        taxa_categoria_total: Decimal,
        desconto_cliente: Decimal,
        desconto_pagamento: Decimal,
        frete_regional: Decimal,
    ) -> ResultadoPrecificacao:
        total_final = _arredondar_moeda(valor_produtos_com_descontos + taxa_categoria_total + frete_regional)
        return ResultadoPrecificacao(
            subtotal_produtos=subtotal_produtos,
            taxa_categoria_total=taxa_categoria_total,
            desconto_cliente=desconto_cliente,
            desconto_pagamento=desconto_pagamento,
            valor_frete=frete_regional,
            opcao_selecionada=OpcaoDeBeneficio.DESCONTOS_APLICADOS,
            total_final=total_final,
        )

    @staticmethod
    def _montar_opcao_frete_gratis(
        subtotal_produtos: Decimal,
        taxa_categoria_total: Decimal,
    ) -> ResultadoPrecificacao:
        total_final = _arredondar_moeda(subtotal_produtos + taxa_categoria_total)
        return ResultadoPrecificacao(
            subtotal_produtos=subtotal_produtos,
            taxa_categoria_total=taxa_categoria_total,
            desconto_cliente=Decimal("0.00"),
            desconto_pagamento=Decimal("0.00"),
            valor_frete=Decimal("0.00"),
            opcao_selecionada=OpcaoDeBeneficio.FRETE_GRATIS_SEM_DESCONTOS,
            total_final=total_final,
        )


# ---------------------------------------------------------------------------
# SRP: Geração de comprovante
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Comprovante:
    id_pedido: str
    status: StatusPedido
    mensagem: str
    subtotal_produtos: Optional[Decimal] = None
    taxa_categoria_total: Optional[Decimal] = None
    desconto_cliente: Optional[Decimal] = None
    desconto_pagamento: Optional[Decimal] = None
    valor_frete: Optional[Decimal] = None
    opcao_beneficio_selecionada: Optional[str] = None
    total_final: Optional[Decimal] = None

    def imprimir(self) -> str:
        linhas = [
            "=" * 56,
            f"COMPROVANTE DO PEDIDO #{self.id_pedido}",
            "=" * 56,
            f"Status ......................... {self.status.value}",
        ]
        if self.status == StatusPedido.FALHA:
            linhas.append(f"Motivo .......................... {self.mensagem}")
        else:
            linhas.extend(
                [
                    f"Subtotal dos produtos ........... {_formatar_moeda(self.subtotal_produtos)}",
                    f"Taxa de categoria ................ {_formatar_moeda(self.taxa_categoria_total)}",
                    f"Desconto de cliente .............. -{_formatar_moeda(self.desconto_cliente)}",
                    f"Desconto de pagamento ............ -{_formatar_moeda(self.desconto_pagamento)}",
                    f"Frete ............................. {_formatar_moeda(self.valor_frete)}",
                    f"Opção de benefício aplicada ...... {self.opcao_beneficio_selecionada}",
                    "-" * 56,
                    f"TOTAL FINAL ....................... {_formatar_moeda(self.total_final)}",
                ]
            )
        linhas.append("=" * 56)
        return "\n".join(linhas)


class GeradorDeComprovante:
    """Responsável exclusivamente por traduzir o resultado do
    processamento do pedido em um comprovante estruturado."""

    def gerar_sucesso(self, id_pedido: str, resultado: ResultadoPrecificacao) -> Comprovante:
        return Comprovante(
            id_pedido=id_pedido,
            status=StatusPedido.SUCESSO,
            mensagem="Pedido processado com sucesso.",
            subtotal_produtos=resultado.subtotal_produtos,
            taxa_categoria_total=resultado.taxa_categoria_total,
            desconto_cliente=resultado.desconto_cliente,
            desconto_pagamento=resultado.desconto_pagamento,
            valor_frete=resultado.valor_frete,
            opcao_beneficio_selecionada=resultado.opcao_selecionada.value,
            total_final=resultado.total_final,
        )

    def gerar_falha(self, id_pedido: str, erro: ErroDePedido) -> Comprovante:
        return Comprovante(
            id_pedido=id_pedido,
            status=StatusPedido.FALHA,
            mensagem=str(erro),
        )


# ---------------------------------------------------------------------------
# SRP: Orquestração do checkout (não conhece regras de negócio internas)
# ---------------------------------------------------------------------------

class ServicoDeCheckout:
    """Coordena as etapas do checkout: validação de estoque, cálculo de
    preços, baixa de estoque e emissão do comprovante. Nunca implementa
    regras de negócio diretamente — apenas orquestra os componentes
    especializados injetados."""

    def __init__(
        self,
        validador_de_estoque: ValidadorDeEstoque,
        calculadora_de_pedido: CalculadoraDePedido,
        atualizador_de_estoque: AtualizadorDeEstoque,
        gerador_de_comprovante: GeradorDeComprovante,
    ) -> None:
        self._validador_de_estoque = validador_de_estoque
        self._calculadora_de_pedido = calculadora_de_pedido
        self._atualizador_de_estoque = atualizador_de_estoque
        self._gerador_de_comprovante = gerador_de_comprovante

    def processar(self, pedido: DadosPedido) -> Comprovante:
        try:
            self._validador_de_estoque.validar(pedido.itens)
            resultado = self._calculadora_de_pedido.calcular(pedido)
            self._atualizador_de_estoque.confirmar_saida(pedido.itens)
            return self._gerador_de_comprovante.gerar_sucesso(pedido.id_pedido, resultado)
        except ErroDePedido as erro:
            return self._gerador_de_comprovante.gerar_falha(pedido.id_pedido, erro)


# ---------------------------------------------------------------------------
# Composição padrão do sistema (raiz de composição / wiring)
# ---------------------------------------------------------------------------

def construir_servico_de_checkout_padrao(repositorio_estoque: RepositorioEstoque) -> ServicoDeCheckout:
    """Monta um `ServicoDeCheckout` com as regras de negócio vigentes.

    Para adicionar uma nova região, categoria com taxa especial, ou
    forma de pagamento, basta registrar o novo componente aqui — nenhuma
    classe do domínio precisa ser alterada (OCP).
    """
    registro_taxa_categoria = RegistroDeTaxasPorCategoria()
    registro_taxa_categoria.registrar("Eletrônicos", TaxaDeManuseioPorUnidade(Decimal("10.00")))

    registro_frete = RegistroDeFretePorRegiao()
    registro_frete.registrar(Regiao.SP, FreteComValorFixo(Decimal("15.00")))
    registro_frete.registrar(Regiao.RJ, FreteComValorFixo(Decimal("20.00")))
    registro_frete.registrar(Regiao.OUTROS, FreteComValorFixo(Decimal("35.00")))

    calculadora_de_pedido = CalculadoraDePedido(
        registro_taxa_categoria=registro_taxa_categoria,
        registro_frete=registro_frete,
        regra_frete_gratis=RegraDeFreteGratis(),
    )

    return ServicoDeCheckout(
        validador_de_estoque=ValidadorDeEstoque(repositorio_estoque),
        calculadora_de_pedido=calculadora_de_pedido,
        atualizador_de_estoque=AtualizadorDeEstoque(repositorio_estoque),
        gerador_de_comprovante=GeradorDeComprovante(),
    )


# ---------------------------------------------------------------------------
# Exemplo de uso executável
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    repositorio_estoque = RepositorioEstoque(
        saldo_inicial={
            "SKU-NOTEBOOK": 5,
            "SKU-MOUSE": 10,
            "SKU-CADEIRA": 2,
        }
    )
    servico_de_checkout = construir_servico_de_checkout_padrao(repositorio_estoque)

    print("### CASO 1: FLUXO DE SUCESSO (Cliente VIP, pagamento via PIX, região SP) ###\n")
    pedido_com_sucesso = DadosPedido(
        id_pedido="PED-001",
        itens=[
            ItemPedido("SKU-NOTEBOOK", "Notebook Gamer", Decimal("3500.00"), 1, "Eletrônicos"),
            ItemPedido("SKU-MOUSE", "Mouse sem fio", Decimal("120.00"), 2, "Eletrônicos"),
        ],
        tipo_cliente=interpretar_tipo_cliente("VIP"),
        regiao=interpretar_regiao("SP"),
        forma_pagamento=interpretar_forma_pagamento("PIX"),
    )
    comprovante_de_sucesso = servico_de_checkout.processar(pedido_com_sucesso)
    print(comprovante_de_sucesso.imprimir())
    print(f"\nSaldo restante de SKU-NOTEBOOK após a compra: {repositorio_estoque.saldo_disponivel('SKU-NOTEBOOK')}")

    print("\n\n### CASO 2: FALHA POR ESTOQUE INSUFICIENTE ###\n")
    pedido_com_falha = DadosPedido(
        id_pedido="PED-002",
        itens=[
            ItemPedido("SKU-CADEIRA", "Cadeira de Escritório", Decimal("800.00"), 5, "Móveis"),
        ],
        tipo_cliente=interpretar_tipo_cliente("COMUM"),
        regiao=interpretar_regiao("RJ"),
        forma_pagamento=interpretar_forma_pagamento("Boleto"),
    )
    comprovante_de_falha = servico_de_checkout.processar(pedido_com_falha)
    print(comprovante_de_falha.imprimir())
    print(f"\nSaldo de SKU-CADEIRA permanece inalterado: {repositorio_estoque.saldo_disponivel('SKU-CADEIRA')}")