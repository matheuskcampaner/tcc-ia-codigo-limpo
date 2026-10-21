from abc import ABC, abstractmethod
from typing import Protocol


# -----------------------------
# Estrutura de dados do ingresso
# -----------------------------
class Ticket:
    def __init__(self, base_price: float, age: int, weekday: str, is_student: bool) -> None:
        self.base_price = base_price
        self.age = age
        self.weekday = weekday.lower()
        self.is_student = is_student


# -----------------------------
# Interface para regras de desconto
# -----------------------------
class DiscountRule(ABC):
    @abstractmethod
    def is_applicable(self, ticket: Ticket) -> bool:
        """Verifica se a regra se aplica ao ingresso."""
        pass

    @abstractmethod
    def apply_discount(self, ticket: Ticket) -> float:
        """Aplica o desconto e retorna o valor final."""
        pass


# -----------------------------
# Implementações concretas de regras
# -----------------------------
class WednesdayDiscount(DiscountRule):
    def is_applicable(self, ticket: Ticket) -> bool:
        return ticket.weekday == "quarta-feira"

    def apply_discount(self, ticket: Ticket) -> float:
        return ticket.base_price * 0.5


class StudentDiscount(DiscountRule):
    def is_applicable(self, ticket: Ticket) -> bool:
        return ticket.is_student

    def apply_discount(self, ticket: Ticket) -> float:
        return ticket.base_price * 0.5


class ChildDiscount(DiscountRule):
    def is_applicable(self, ticket: Ticket) -> bool:
        return ticket.age <= 12

    def apply_discount(self, ticket: Ticket) -> float:
        return ticket.base_price * 0.5


class SeniorDiscount(DiscountRule):
    def is_applicable(self, ticket: Ticket) -> bool:
        return ticket.age >= 60

    def apply_discount(self, ticket: Ticket) -> float:
        return ticket.base_price * 0.5


# -----------------------------
# Calculadora de preço
# -----------------------------
class TicketPriceCalculator:
    def __init__(self, discount_rules: list[DiscountRule]) -> None:
        self.discount_rules = discount_rules

    def calculate_final_price(self, ticket: Ticket) -> float:
        for rule in self.discount_rules:
            if rule.is_applicable(ticket):
                return rule.apply_discount(ticket)
        return ticket.base_price


# -----------------------------
# Exemplo de uso
# -----------------------------
if __name__ == "__main__":
    rules = [WednesdayDiscount(), StudentDiscount(), ChildDiscount(), SeniorDiscount()]
    calculator = TicketPriceCalculator(rules)

    ingresso = Ticket(base_price=40.0, age=20, weekday="quarta-feira", is_student=False)
    print(f"Preço final: R$ {calculator.calculate_final_price(ingresso):.2f}")
