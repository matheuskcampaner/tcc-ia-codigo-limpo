"""
Sistema de Venda de Ingressos de Cinema
========================================
Arquitetura orientada aos princípios SOLID, com ênfase em SRP e OCP.

Design escolhido: Strategy Pattern via Protocol + Composição
------------------------------------------------------------
Cada regra de desconto é uma classe autônoma que implementa o protocolo
`DiscountRule`. Novas regras são adicionadas criando novas classes — sem
alterar nenhuma linha de código existente (OCP). A classe `Ticket` armazena
apenas dados; toda lógica de desconto reside em `DiscountEvaluator` (SRP).

Redução da complexidade ciclomática
-------------------------------------
Em vez de uma cadeia if/elif com N ramificações (complexidade = N+1),
cada regra é uma função de predicado com complexidade 1.
O `DiscountEvaluator` percorre a lista e retorna no primeiro match:
  → complexidade ciclomática total do avaliador = 2 (loop + retorno)
  → complexidade de CADA regra = 2 (uma única condição booleana)
  → adicionar N regras NÃO aumenta a complexidade de nenhum módulo existente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence


# ---------------------------------------------------------------------------
# Camada de Dados — apenas estrutura, zero lógica de negócio  (SRP)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TicketPurchaseRequest:
    """Dados brutos fornecidos pelo ponto de venda."""

    base_price: float
    customer_age: int
    day_of_week: str       # ex.: "segunda", "quarta", "sábado"
    is_student: bool


@dataclass(frozen=True)
class PricedTicket:
    """Resultado imutável após aplicação das regras de negócio."""

    base_price: float
    final_price: float
    applied_discount_label: str | None

    @property
    def has_discount(self) -> bool:
        return self.applied_discount_label is not None


# ---------------------------------------------------------------------------
# Protocolo de Regra de Desconto  (OCP / Polimorfismo)
# ---------------------------------------------------------------------------

class DiscountRule(Protocol):
    """
    Contrato que toda regra de desconto deve satisfazer.

    Qualquer classe com `label` e `is_applicable` obedece automaticamente
    ao protocolo (duck typing estrutural via typing.Protocol).
    """

    @property
    def label(self) -> str:
        """Nome legível da regra, usado em logs e recibos."""
        ...

    def is_applicable(self, request: TicketPurchaseRequest) -> bool:
        """Retorna True se esta regra se aplica à compra informada."""
        ...


# ---------------------------------------------------------------------------
# Regras de Desconto Concretas  (SRP — cada classe tem UM único motivo)
# ---------------------------------------------------------------------------

class WednesdayDiscountRule:
    """Desconto válido toda quarta-feira, independente do perfil do cliente."""

    @property
    def label(self) -> str:
        return "Desconto de quarta-feira"

    def is_applicable(self, request: TicketPurchaseRequest) -> bool:
        return request.day_of_week.strip().lower() == "quarta"


class StudentDiscountRule:
    """Desconto para portadores de carteira de estudante válida."""

    @property
    def label(self) -> str:
        return "Desconto de estudante"

    def is_applicable(self, request: TicketPurchaseRequest) -> bool:
        return request.is_student


class ChildDiscountRule:
    """Desconto para crianças com até 12 anos de idade."""

    MAXIMUM_CHILD_AGE: int = 12

    @property
    def label(self) -> str:
        return "Desconto infantil (até 12 anos)"

    def is_applicable(self, request: TicketPurchaseRequest) -> bool:
        return request.customer_age <= self.MAXIMUM_CHILD_AGE


class SeniorDiscountRule:
    """Desconto para clientes na terceira idade (60 anos ou mais)."""

    MINIMUM_SENIOR_AGE: int = 60

    @property
    def label(self) -> str:
        return "Desconto para terceira idade (60+)"

    def is_applicable(self, request: TicketPurchaseRequest) -> bool:
        return request.customer_age >= self.MINIMUM_SENIOR_AGE


# ---------------------------------------------------------------------------
# Constante de Desconto  (isolada para fácil ajuste futuro)
# ---------------------------------------------------------------------------

HALF_PRICE_DISCOUNT_RATE: float = 0.50


# ---------------------------------------------------------------------------
# Avaliador de Desconto  (SRP — orquestra regras, não as conhece)
# ---------------------------------------------------------------------------

@dataclass
class DiscountEvaluator:
    """
    Percorre as regras registradas e aplica o primeiro desconto elegível.

    O desconto é NÃO-CUMULATIVO: somente a primeira regra que se aplicar
    é considerada. A ordem da lista `rules` determina a prioridade.

    Para adicionar uma nova regra basta instanciá-la e incluí-la na lista —
    esta classe nunca precisa ser modificada  (OCP).
    """

    rules: Sequence[DiscountRule] = field(
        default_factory=lambda: [
            WednesdayDiscountRule(),
            StudentDiscountRule(),
            ChildDiscountRule(),
            SeniorDiscountRule(),
        ]
    )

    def evaluate(self, request: TicketPurchaseRequest) -> PricedTicket:
        """Retorna um PricedTicket com o preço final calculado."""
        for rule in self.rules:
            if rule.is_applicable(request):
                discounted_price = request.base_price * (1 - HALF_PRICE_DISCOUNT_RATE)
                return PricedTicket(
                    base_price=request.base_price,
                    final_price=discounted_price,
                    applied_discount_label=rule.label,
                )

        return PricedTicket(
            base_price=request.base_price,
            final_price=request.base_price,
            applied_discount_label=None,
        )


# ---------------------------------------------------------------------------
# Ponto de entrada público — API simplificada para o cliente do módulo
# ---------------------------------------------------------------------------

def calculate_ticket_price(
    base_price: float,
    customer_age: int,
    day_of_week: str,
    is_student: bool,
    evaluator: DiscountEvaluator | None = None,
) -> PricedTicket:
    """
    Função de fachada que oculta os detalhes de construção dos objetos.

    Parameters
    ----------
    base_price    : Valor cheio do ingresso em reais.
    customer_age  : Idade do cliente em anos completos.
    day_of_week   : Dia da semana em português, ex. "quarta".
    is_student    : True se o cliente apresentou carteira de estudante.
    evaluator     : Instância personalizada de DiscountEvaluator (opcional;
                    útil para injeção de dependência em testes).

    Returns
    -------
    PricedTicket com o preço final e a etiqueta do desconto aplicado.
    """
    request = TicketPurchaseRequest(
        base_price=base_price,
        customer_age=customer_age,
        day_of_week=day_of_week,
        is_student=is_student,
    )
    active_evaluator = evaluator or DiscountEvaluator()
    return active_evaluator.evaluate(request)