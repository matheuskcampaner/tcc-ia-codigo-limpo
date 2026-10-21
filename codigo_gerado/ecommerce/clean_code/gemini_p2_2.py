from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


# ==============================================================================
# DOMÍNIO E ENUMS
# ==============================================================================

class CustomerType(str, Enum):
    COMUM = "COMUM"
    VIP = "VIP"
    CORPORATIVO = "CORPORATIVO"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "Cartão de Crédito"
    PIX = "PIX"
    BOLETO = "Boleto"


class Region(str, Enum):
    SP = "SP"
    RJ = "RJ"
    OUTROS = "OUTROS"


class CheckoutStatus(str, Enum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"


@dataclass(frozen=True)
class OrderItem:
    id: str
    name: str
    unit_price: float
    quantity: int
    category: str

    def __post_init__(self) -> None:
        if self.unit_price <= 0:
            raise InvalidDataError(f"Preço unitário do item '{self.name}' deve ser maior que zero.")
        if self.quantity <= 0:
            raise InvalidDataError(f"Quantidade do item '{self.name}' deve ser maior que zero.")

    @property
    def total_price(self) -> float:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    customer_type: CustomerType


@dataclass(frozen=True)
class Order:
    id: str
    customer: Customer
    items: List[OrderItem]
    region: Region
    payment_method: PaymentMethod


@dataclass(frozen=True)
class Receipt:
    order_id: str
    status: CheckoutStatus
    subtotal: float
    category_fees: float
    discounts: float
    freight: float
    selected_option: str
    total_price: float


# ==============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ==============================================================================

class CheckoutException(Exception):
    """Exceção base para o processo de checkout."""
    pass


class InsufficientStockError(CheckoutException):
    """Lançada quando a quantidade em estoque é insuficiente."""
    pass


class InvalidDataError(CheckoutException):
    """Lançada quando dados numéricos do pedido são inválidos."""
    pass


class UnsupportedPaymentMethodError(CheckoutException):
    """Lançada quando a forma de pagamento não é suportada."""
    pass


class UnsupportedRegionError(CheckoutException):
    """Lançada quando a região de entrega não é suportada."""
    pass


# ==============================================================================
# GESTÃO DE ESTOQUE (SRP)
# ==============================================================================

class StockRepository:
    """Gerencia a consulta e atualização do estoque em memória."""

    def __init__(self, initial_stock: Dict[str, int]) -> None:
        self._stock: Dict[str, int] = dict(initial_stock)

    def validate_and_reserve(self, items: List[OrderItem]) -> None:
        unavailable_items: List[str] = []
        for item in items:
            available_qty = self._stock.get(item.id, 0)
            if available_qty < item.quantity:
                unavailable_items.append(
                    f"Item '{item.name}' (ID: {item.id}) - Solicitado: {item.quantity}, Disponível: {available_qty}"
                )

        if unavailable_items:
            details = "; ".join(unavailable_items)
            raise InsufficientStockError(f"Estoque insuficiente para os itens: {details}")

    def deduct_items(self, items: List[OrderItem]) -> None:
        for item in items:
            self._stock[item.id] -= item.quantity

    def get_available_quantity(self, item_id: str) -> int:
        return self._stock.get(item_id, 0)


# ==============================================================================
# ESTRATÉGIAS DE TAXA POR CATEGORIA (OCP)
# ==============================================================================

class CategoryFeeStrategy(ABC):
    @abstractmethod
    def calculate_fee(self, item: OrderItem) -> float:
        pass


class ElectronicsCategoryFeeStrategy(CategoryFeeStrategy):
    FEE_PER_UNIT: float = 10.00

    def calculate_fee(self, item: OrderItem) -> float:
        return self.FEE_PER_UNIT * item.quantity


class DefaultCategoryFeeStrategy(CategoryFeeStrategy):
    def calculate_fee(self, item: OrderItem) -> float:
        return 0.0


class CategoryFeeCalculator:
    """Mapeia categorias para suas respectivas estratégias de taxa."""

    def __init__(self) -> None:
        self._strategies: Dict[str, CategoryFeeStrategy] = {
            "Eletrônicos": ElectronicsCategoryFeeStrategy()
        }
        self._default_strategy = DefaultCategoryFeeStrategy()

    def calculate_total_fees(self, items: List[OrderItem]) -> float:
        total_fee = 0.0
        for item in items:
            strategy = self._strategies.get(item.category, self._default_strategy)
            total_fee += strategy.calculate_fee(item)
        return total_fee


# ==============================================================================
# ESTRATÉGIAS DE DESCONTO (OCP)
# ==============================================================================

class CustomerDiscountStrategy(ABC):
    @abstractmethod
    def calculate_discount(self, subtotal: float) -> float:
        pass


class VipCustomerDiscountStrategy(CustomerDiscountStrategy):
    DISCOUNT_RATE: float = 0.10

    def calculate_discount(self, subtotal: float) -> float:
        return subtotal * self.DISCOUNT_RATE


class CorporateCustomerDiscountStrategy(CustomerDiscountStrategy):
    DISCOUNT_RATE: float = 0.15
    THRESHOLD: float = 1000.00

    def calculate_discount(self, subtotal: float) -> float:
        if subtotal > self.THRESHOLD:
            return subtotal * self.DISCOUNT_RATE
        return 0.0


class StandardCustomerDiscountStrategy(CustomerDiscountStrategy):
    def calculate_discount(self, subtotal: float) -> float:
        return 0.0


class CustomerDiscountFactory:
    """Cria a estratégia de desconto adequada de acordo com o tipo de cliente."""

    @staticmethod
    def get_strategy(customer_type: CustomerType) -> CustomerDiscountStrategy:
        strategies = {
            CustomerType.VIP: VipCustomerDiscountStrategy(),
            CustomerType.CORPORATIVO: CorporateCustomerDiscountStrategy(),
            CustomerType.COMUM: StandardCustomerDiscountStrategy()
        }
        return strategies.get(customer_type, StandardCustomerDiscountStrategy())


class PaymentDiscountStrategy(ABC):
    @abstractmethod
    def calculate_discount(self, amount: float) -> float:
        pass


class PixPaymentDiscountStrategy(PaymentDiscountStrategy):
    DISCOUNT_RATE: float = 0.05

    def calculate_discount(self, amount: float) -> float:
        return amount * self.DISCOUNT_RATE


class StandardPaymentDiscountStrategy(PaymentDiscountStrategy):
    def calculate_discount(self, amount: float) -> float:
        return 0.0


class PaymentDiscountFactory:
    """Cria a estratégia de desconto associada à forma de pagamento."""

    @staticmethod
    def get_strategy(payment_method: PaymentMethod) -> PaymentDiscountStrategy:
        if payment_method == PaymentMethod.PIX:
            return PixPaymentDiscountStrategy()
        return StandardPaymentDiscountStrategy()


# ==============================================================================
# CÁLCULO DE FRETE (OCP/SRP)
# ==============================================================================

class FreightCalculator:
    """Calcula a taxa de frete com base na região."""

    RATES: Dict[Region, float] = {
        Region.SP: 15.00,
        Region.RJ: 20.00,
        Region.OUTROS: 35.00
    }

    def calculate_freight(self, region: Region) -> float:
        if region not in self.RATES:
            raise UnsupportedRegionError(f"Região de entrega '{region}' não é suportada.")
        return self.RATES[region]


# ==============================================================================
# MOTOR DE AVALIAÇÃO DE PREVALÊNCIA E BENEFÍCIOS (SRP)
# ==============================================================================

@dataclass
class PricingOptionResult:
    option_name: str
    discount_amount: float
    freight_amount: float
    total_price: float


class PricingEngine:
    """
    Compara as duas alternativas de precificação para determinar a mais vantajosa para o cliente:
    
    Opção A: Aplicar todos os descontos válidos e cobrar o frete integral da região.
    Opção B: Isentar o frete (R$ 0,00) e manter os produtos pelo valor integral mais taxa de categoria.
    """

    FREE_FREIGHT_THRESHOLD: float = 300.00

    def __init__(
        self,
        category_fee_calculator: CategoryFeeCalculator,
        freight_calculator: FreightCalculator
    ) -> None:
        self._category_fee_calculator = category_fee_calculator
        self._freight_calculator = freight_calculator

    def evaluate_best_pricing(self, order: Order) -> Tuple[PricingOptionResult, float, float]:
        subtotal = sum(item.total_price for item in order.items)
        category_fees = self._category_fee_calculator.calculate_total_fees(order.items)
        base_freight = self._freight_calculator.calculate_freight(order.region)

        # Cálculo dos descontos da Opção A
        customer_discount_strategy = CustomerDiscountFactory.get_strategy(order.customer.customer_type)
        customer_discount = customer_discount_strategy.calculate_discount(subtotal)
        
        remaining_product_amount = subtotal - customer_discount
        payment_discount_strategy = PaymentDiscountFactory.get_strategy(order.payment_method)
        payment_discount = payment_discount_strategy.calculate_discount(remaining_product_amount)
        
        total_discounts_option_a = customer_discount + payment_discount
        discounted_products_total = subtotal - total_discounts_option_a

        # Opção A: Descontos de produtos + Frete Integral
        total_option_a = discounted_products_total + category_fees + base_freight
        option_a_result = PricingOptionResult(
            option_name="Opção A (Descontos nos produtos + Frete Pago)",
            discount_amount=total_discounts_option_a,
            freight_amount=base_freight,
            total_price=total_option_a
        )

        # Qualificação para a Opção B (Frete Grátis)
        qualifies_for_free_freight = discounted_products_total > self.FREE_FREIGHT_THRESHOLD

        if qualifies_for_free_freight:
            # Opção B: Isenção de frete e produtos pelo valor integral sem descontos
            total_option_b = subtotal + category_fees + 0.0
            option_b_result = PricingOptionResult(
                option_name="Opção B (Isenção de Frete + Valor Integral dos Produtos)",
                discount_amount=0.0,
                freight_amount=0.0,
                total_price=total_option_b
            )

            if option_b_result.total_price < option_a_result.total_price:
                return option_b_result, subtotal, category_fees

        return option_a_result, subtotal, category_fees


# ==============================================================================
# CHECKOUT SERVICE (ORQUESTRADOR DE CHECKOUT)
# ==============================================================================

class CheckoutService:
    """Orquestra as validações, cálculo de valores, atualização do estoque e emissão de comprovante."""

    def __init__(
        self,
        stock_repository: StockRepository,
        pricing_engine: PricingEngine
    ) -> None:
        self._stock_repository = stock_repository
        self._pricing_engine = pricing_engine

    def process_order(self, order: Order) -> Receipt:
        self._validate_order_data(order)

        # 1. Validação e Reserva de Estoque
        self._stock_repository.validate_and_reserve(order.items)

        # 2. Avaliação das Regras de Precificação e Prevalência
        selected_option, subtotal, category_fees = self._pricing_engine.evaluate_best_pricing(order)

        # 3. Finalização e Dedução de Estoque
        self._stock_repository.deduct_items(order.items)

        # 4. Geração do Comprovante Estuturado
        return Receipt(
            order_id=order.id,
            status=CheckoutStatus.SUCESSO,
            subtotal=subtotal,
            category_fees=category_fees,
            discounts=selected_option.discount_amount,
            freight=selected_option.freight_amount,
            selected_option=selected_option.option_name,
            total_price=selected_option.total_price
        )

    def _validate_order_data(self, order: Order) -> None:
        if not order.items:
            raise InvalidDataError("O pedido deve conter ao menos um item.")
        
        if not isinstance(order.payment_method, PaymentMethod):
            raise UnsupportedPaymentMethodError(f"Forma de pagamento '{order.payment_method}' inválida.")

        if not isinstance(order.region, Region):
            raise UnsupportedRegionError(f"Região '{order.region}' inválida.")


# ==============================================================================
# EXEMPLO DE USO EXECUTÁVEL
# ==============================================================================

def print_receipt(receipt: Receipt) -> None:
    print(f"Status do Pedido: {receipt.status.value}")
    print(f"ID do Pedido: {receipt.order_id}")
    print(f"Subtotal dos Produtos: R$ {receipt.subtotal:.2f}")
    print(f"Taxas de Categoria: R$ {receipt.category_fees:.2f}")
    print(f"Descontos Aplicados: R$ {receipt.discounts:.2f}")
    print(f"Taxa de Frete: R$ {receipt.freight:.2f}")
    print(f"Benefício Selecionado: {receipt.selected_option}")
    print(f"Total Final Pago: R$ {receipt.total_price:.2f}")


if __name__ == "__main__":
    # Inicialização dos dados de Estoque em memória (ID_ITEM: QUANTIDADE)
    stock_db = {
        "ITEM_01": 10,  # Notebook (Eletrônico)
        "ITEM_02": 50,  # Camiseta (Vestuário)
        "ITEM_03": 2    # Fone de Ouvido (Eletrônico)
    }

    stock_repo = StockRepository(initial_stock=stock_db)
    category_calculator = CategoryFeeCalculator()
    freight_calculator = FreightCalculator()
    pricing_engine = PricingEngine(category_calculator, freight_calculator)
    checkout_service = CheckoutService(stock_repo, pricing_engine)

    print("CENÁRIO 1: Processamento de Pedido com Sucesso")
    
    customer_vip = Customer(id="CUS_101", name="Carlos Silva", customer_type=CustomerType.VIP)
    items_order_1 = [
        OrderItem(id="ITEM_01", name="Notebook Gamer", unit_price=4000.00, quantity=1, category="Eletrônicos"),
        OrderItem(id="ITEM_02", name="Camiseta Algodão", unit_price=80.00, quantity=2, category="Vestuário")
    ]
    
    order_success = Order(
        id="ORD-2026-001",
        customer=customer_vip,
        items=items_order_1,
        region=Region.SP,
        payment_method=PaymentMethod.PIX
    )

    try:
        receipt_1 = checkout_service.process_order(order_success)
        print_receipt(receipt_1)
    except CheckoutException as e:
        print(f"Erro no checkout: {e}")

    print("\nCENÁRIO 2: Falha por Estoque Insuficiente")

    customer_corp = Customer(id="CUS_202", name="Empresa Tech LLC", customer_type=CustomerType.CORPORATIVO)
    items_order_2 = [
        OrderItem(id="ITEM_03", name="Fone Bluetooth", unit_price=150.00, quantity=5, category="Eletrônicos")
    ]

    order_stock_fail = Order(
        id="ORD-2026-002",
        customer=customer_corp,
        items=items_order_2,
        region=Region.RJ,
        payment_method=PaymentMethod.BOLETO
    )

    try:
        receipt_2 = checkout_service.process_order(order_stock_fail)
        print_receipt(receipt_2)
    except InsufficientStockError as e:
        print(f"Exceção Capturada com Sucesso: {e}")
    except CheckoutException as e:
        print(f"Erro Genérico: {e}")