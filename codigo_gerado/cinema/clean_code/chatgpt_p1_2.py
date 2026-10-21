from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Ingresso:
    valor_base: float
    idade_cliente: int
    dia_semana: str
    estudante: bool


class RegraDesconto(ABC):
    @abstractmethod
    def eh_aplicavel(self, ingresso: Ingresso) -> bool:
        pass

    @property
    @abstractmethod
    def percentual_desconto(self) -> float:
        pass


class DescontoQuartaFeira(RegraDesconto):
    def eh_aplicavel(self, ingresso: Ingresso) -> bool:
        return ingresso.dia_semana.lower() == "quarta-feira"

    @property
    def percentual_desconto(self) -> float:
        return 0.50


class DescontoEstudante(RegraDesconto):
    def eh_aplicavel(self, ingresso: Ingresso) -> bool:
        return ingresso.estudante

    @property
    def percentual_desconto(self) -> float:
        return 0.50


class DescontoCrianca(RegraDesconto):
    def eh_aplicavel(self, ingresso: Ingresso) -> bool:
        return ingresso.idade_cliente <= 12

    @property
    def percentual_desconto(self) -> float:
        return 0.50


class DescontoIdoso(RegraDesconto):
    def eh_aplicavel(self, ingresso: Ingresso) -> bool:
        return ingresso.idade_cliente >= 60

    @property
    def percentual_desconto(self) -> float:
        return 0.50


class CalculadoraPrecoIngresso:
    def __init__(self, regras_desconto: List[RegraDesconto]) -> None:
        self.regras_desconto = regras_desconto

    def calcular_preco_final(self, ingresso: Ingresso) -> float:
        possui_desconto = any(
            regra.eh_aplicavel(ingresso)
            for regra in self.regras_desconto
        )

        if possui_desconto:
            return ingresso.valor_base * 0.5

        return ingresso.valor_base


regras = [
    DescontoQuartaFeira(),
    DescontoEstudante(),
    DescontoCrianca(),
    DescontoIdoso()
]

calculadora = CalculadoraPrecoIngresso(regras)

ingresso = Ingresso(
    valor_base=30.0,
    idade_cliente=20,
    dia_semana="Quarta-feira",
    estudante=False
)

preco_final = calculadora.calcular_preco_final(ingresso)

print(f"Preço final: R$ {preco_final:.2f}")