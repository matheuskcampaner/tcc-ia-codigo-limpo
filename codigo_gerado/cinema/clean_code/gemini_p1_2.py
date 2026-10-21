from abc import ABC, abstractmethod
from enum import Enum, auto


class DiaSemana(Enum):
    SEGUNDA = auto()
    TERCA = auto()
    QUARTA = auto()
    QUINTA = auto()
    SEXTA = auto()
    SABADO = auto()
    DOMINGO = auto()


class Cliente:
    """Dados do cliente encapsulados, garantindo a coesão."""
    def __init__(self, idade: int, eh_estudante: bool) -> None:
        self.idade = idade
        self.eh_estudante = eh_estudante


class Sessao:
    """Dados do contexto da sessão de cinema."""
    def __init__(self, valor_base: float, dia_da_semana: DiaSemana) -> None:
        self.valor_base = valor_base
        self.dia_da_semana = dia_da_semana


class RegraDesconto(ABC):
    """Interface (Abstração) para as estratégias de desconto (OCP)."""
    @abstractmethod
    def se_aplica(self, cliente: Cliente, sessao: Sessao) -> bool:
        pass

    @abstractmethod
    def calcular_desconto(self, valor_base: float) -> float:
        pass


# --- Implementações das Regras de Desconto (SRP) ---

class DescontoQuartaFeira(RegraDesconto):
    def se_aplica(self, cliente: Cliente, sessao: Sessao) -> bool:
        return sessao.dia_da_semana == DiaSemana.QUARTA

    def calcular_desconto(self, valor_base: float) -> float:
        return valor_base * 0.50


class DescontoEstudante(RegraDesconto):
    def se_aplica(self, cliente: Cliente, sessao: Sessao) -> bool:
        return cliente.eh_estudante

    def calcular_desconto(self, valor_base: float) -> float:
        return valor_base * 0.50


class DescontoIdade(RegraDesconto):
    def se_aplica(self, cliente: Cliente, sessao: Sessao) -> bool:
        return cliente.idade <= 12 or cliente.idade >= 60

    def calcular_desconto(self, valor_base: float) -> float:
        return valor_base * 0.50


# --- Calculadora de Ingressos (Orquestradora) ---

class CalculadoraPrecoIngresso:
    """
    Responsável apenas por orquestrar a aplicação das regras.
    Não sabe *como* os descontos funcionam, apenas os aplica.
    """
    def __init__(self, regras: list[RegraDesconto]) -> None:
        self._regras = regras

    def calcular_preco_final(self, cliente: Cliente, sessao: Sessao) -> float:
        # Como o desconto é não-cumulativo e todos são de 50%, 
        # a primeira regra que se aplicar define o desconto máximo.
        for regra in self._regras:
            if regra.se_aplica(cliente, sessao):
                desconto = regra.calcular_desconto(sessao.valor_base)
                return sessao.valor_base - desconto
                
        return sessao.valor_base


# --- Exemplo de Uso ---

if __name__ == "__main__":
    # Injeção de dependências: configurando as regras do sistema
    regras_vigentes = [
        DescontoQuartaFeira(),
        DescontoEstudante(),
        DescontoIdade()
    ]
    
    calculadora = CalculadoraPrecoIngresso(regras=regras_vigentes)
    
    # Cenário 1: Cliente idoso (65 anos) na Terça-feira (Valor Base: R$ 40.00)
    cliente_1 = Cliente(idade=65, eh_estudante=False)
    sessao_1 = Sessao(valor_base=40.0, dia_da_semana=DiaSemana.TERCA)
    preco_1 = calculadora.calcular_preco_final(cliente_1, sessao_1)
    print(f"Cenário 1 - Preço Final: R$ {preco_1:.2f}")  # Esperado: R$ 20.00 (Desconto Idade)

    # Cenário 2: Cliente de 25 anos, não estudante, no Sábado (Valor Base: R$ 40.00)
    cliente_2 = Cliente(idade=25, eh_estudante=False)
    sessao_2 = Sessao(valor_base=40.0, dia_da_semana=DiaSemana.SABADO)
    preco_2 = calculadora.calcular_preco_final(cliente_2, sessao_2)
    print(f"Cenário 2 - Preço Final: R$ {preco_2:.2f}")  # Esperado: R$ 40.00 (Sem desconto)