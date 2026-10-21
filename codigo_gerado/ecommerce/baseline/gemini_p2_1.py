from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class EcommerceError(Exception):
    """Excecao base para erros do sistema de e-commerce."""
    pass


class InsufficientStockError(EcommerceError):
    """Excecao lancada quando um ou mais itens nao possuem estoque suficiente."""
    pass


class InvalidOrderError(EcommerceError):
    """Excecao lancada para dados de entrada invalidos ou nao suportados."""
    pass


@dataclass
class StockItem:
    item_id: str
    name: str
    quantity: int
    unit_price: float
    category: str


@dataclass
class OrderItem:
    item_id: str
    name: str
    unit_price: float
    quantity: int
    category: str


@dataclass
class Order:
    order_id: str
    customer_type: str
    region: str
    payment_method: str
    items: List[OrderItem]


@dataclass
class CheckoutReceipt:
    order_id: str
    status: str
    subtotal: float = 0.0
    handling_fee: float = 0.0
    discounts_applied: float = 0.0
    shipping_fee: float = 0.0
    selected_option: str = ""
    final_total: float = 0.0
    error_message: Optional[str] = None

    def __str__(self) -> str:
        if self.status == "FALHA":
            return (
                f"=== COMPROVANTE DE PEDIDO: {self.order_id} ===\n"
                f"Status: {self.status}\n"
                f"Erro: {self.error_message}\n"
            )
        
        return (
            f"=== COMPROVANTE DE PEDIDO: {self.order_id} ===\n"
            f"Status: {self.status}\n"
            f"Subtotal dos produtos: R$ {self.subtotal:.2f}\n"
            f"Taxas de manuseio: R$ {self.handling_fee:.2f}\n"
            f"Descontos aplicados: R$ {self.discounts_applied:.2f}\n"
            f"Valor do frete: R$ {self.shipping_fee:.2f}\n"
            f"Opção selecionada: {self.selected_option}\n"
            f"TOTAL FINAL: R$ {self.final_total:.2f}\n"
        )


class StockRepository:
    """Simulador de cadastro de estoque em memoria."""

    def __init__(self) -> None:
        self._stock: Dict[str, StockItem] = {}

    def add_item(self, item: StockItem) -> None:
        self._stock[item.item_id] = item

    def get_item(self, item_id: str) -> Optional[StockItem]:
        return self._stock.get(item_id)

    def deduct_stock(self, items: List[OrderItem]) -> None:
        for item in items:
            stock_item = self._stock[item.item_id]
            stock_item.quantity -= item.quantity


class CheckoutService:
    """Servico responsavel pela execucao das regras de negocio e checkout."""

    VALID_CUSTOMER_TYPES = {"COMUM", "VIP", "CORPORATIVO"}
    VALID_REGIONS = {"SP": 15.0, "RJ": 20.0, "OUTROS": 35.0}
    VALID_PAYMENT_METHODS = {"Cartão de Crédito", "PIX", "Boleto"}

    def __init__(self, stock_repo: StockRepository) -> None:
        self.stock_repo = stock_repo

    def process_checkout(self, order: Order) -> CheckoutReceipt:
        try:
            self._validate_order_data(order)
            self._validate_and_check_stock(order.items)

            # Calculo dos valores base
            subtotal = sum(item.unit_price * item.quantity for item in order.items)
            handling_fee = sum(
                10.0 * item.quantity for item in order.items if item.category == "Eletrônicos"
            )
            base_shipping = self.VALID_REGIONS[order.region]

            # Calculo dos descontos validos para Opcao A
            customer_discount = self._calculate_customer_discount(order.customer_type, subtotal)
            subtotal_after_cust_disc = subtotal - customer_discount
            payment_discount = self._calculate_payment_discount(
                order.payment_method, subtotal_after_cust_disc
            )
            total_discounts = customer_discount + payment_discount

            products_net_value = subtotal - total_discounts

            # Avaliacao das opcoes (Regra de Nao-Cumulatividade)
            selected_option, final_shipping, applied_discounts, final_total = (
                self._evaluate_best_option(
                    subtotal=subtotal,
                    handling_fee=handling_fee,
                    total_discounts=total_discounts,
                    products_net_value=products_net_value,
                    base_shipping=base_shipping,
                )
            )

            # Atualizacao do estoque apenas apos validacao e confirmacao de sucesso
            self.stock_repo.deduct_stock(order.items)

            return CheckoutReceipt(
                order_id=order.order_id,
                status="SUCESSO",
                subtotal=subtotal,
                handling_fee=handling_fee,
                discounts_applied=applied_discounts,
                shipping_fee=final_shipping,
                selected_option=selected_option,
                final_total=final_total,
            )

        except EcommerceError as exc:
            return CheckoutReceipt(
                order_id=order.order_id,
                status="FALHA",
                error_message=str(exc),
            )

    def _validate_order_data(self, order: Order) -> None:
        if order.customer_type not in self.VALID_CUSTOMER_TYPES:
            raise InvalidOrderError(f"Tipo de cliente invalido: '{order.customer_type}'.")

        if order.region not in self.VALID_REGIONS:
            raise InvalidOrderError(f"Regiao de entrega nao suportada: '{order.region}'.")

        if order.payment_method not in self.VALID_PAYMENT_METHODS:
            raise InvalidOrderError(f"Forma de pagamento nao suportada: '{order.payment_method}'.")

        if not order.items:
            raise InvalidOrderError("O pedido deve conter pelo menos um item.")

        for item in order.items:
            if item.unit_price <= 0:
                raise InvalidOrderError(
                    f"Preco invalido para o item '{item.name}' (ID: {item.item_id}): R$ {item.unit_price}."
                )
            if item.quantity <= 0:
                raise InvalidOrderError(
                    f"Quantidade invalida para o item '{item.name}' (ID: {item.item_id}): {item.quantity}."
                )

    def _validate_and_check_stock(self, items: List[OrderItem]) -> None:
        unavailable_items = []

        for item in items:
            stock_item = self.stock_repo.get_item(item.item_id)
            if not stock_item:
                unavailable_items.append(
                    f"{item.name} (ID: {item.item_id}) -> Item nao encontrado no estoque"
                )
            elif stock_item.quantity < item.quantity:
                unavailable_items.append(
                    f"{item.name} (ID: {item.item_id}) -> Solicitado: {item.quantity}, Disponivel: {stock_item.quantity}"
                )

        if unavailable_items:
            details = "; ".join(unavailable_items)
            raise InsufficientStockError(f"Estoque insuficiente para os seguintes itens: {details}.")

    def _calculate_customer_discount(self, customer_type: str, subtotal: float) -> float:
        if customer_type == "VIP":
            return subtotal * 0.10
        elif customer_type == "CORPORATIVO" and subtotal > 1000.0:
            return subtotal * 0.15
        return 0.0

    def _calculate_payment_discount(
        self, payment_method: str, subtotal_after_customer_discount: float
    ) -> float:
        if payment_method == "PIX":
            return subtotal_after_customer_discount * 0.05
        return 0.0

    def _evaluate_best_option(
        self,
        subtotal: float,
        handling_fee: float,
        total_discounts: float,
        products_net_value: float,
        base_shipping: float,
    ) -> Tuple[str, float, float, float]:
        """
        Compara as duas alternativas e retorna:
        (Nome da Opcao, Frete Final, Descontos Aplicados, Total Final)
        """
        # Opcao A: Aplicar todos os descontos nos produtos e cobrar o frete integral
        total_a = products_net_value + handling_fee + base_shipping

        # Opcao B: Frete Gratis + Produtos sem desconto (se qualificar com valor > 300)
        qualifies_for_free_shipping = products_net_value > 300.0

        if qualifies_for_free_shipping:
            total_b = subtotal + handling_fee
            
            # Escolhe a opcao que resulta no menor valor pago
            if total_b < total_a:
                return (
                    "Opção B (Frete Grátis - Sem Descontos em Produtos)",
                    0.0,
                    0.0,
                    total_b,
                )

        return (
            "Opção A (Descontos nos Produtos + Frete Integral)",
            base_shipping,
            total_discounts,
            total_a,
        )


# Exemplo Pratico e Testes Executaveis
if __name__ == "__main__":
    # 1. Inicializacao do Estoque
    repo = StockRepository()
    repo.add_item(StockItem("101", "Smartphone Premium", quantity=5, unit_price=1200.0, category="Eletrônicos"))
    repo.add_item(StockItem("102", "Cadeira de Escritório", quantity=10, unit_price=250.0, category="Móveis"))
    repo.add_item(StockItem("103", "Mouse Gamer", quantity=2, unit_price=150.0, category="Eletrônicos"))

    checkout = CheckoutService(repo)

    # Caso 1: Sucesso com escolhas de descontos e selecao automatica da melhor opcao
    print("--- CASO 1: PROCESSAMENTO COM SUCESSO ---")
    pedido_sucesso = Order(
        order_id="PED-001",
        customer_type="VIP",
        region="SP",
        payment_method="PIX",
        items=[
            OrderItem("101", "Smartphone Premium", unit_price=1200.0, quantity=1, category="Eletrônicos"),
            OrderItem("102", "Cadeira de Escritório", unit_price=250.0, quantity=1, category="Móveis"),
        ],
    )
    comprovante_1 = checkout.process_checkout(pedido_sucesso)
    print(comprovante_1)

    # Caso 2: Falha por estoque insuficiente
    print("--- CASO 2: FALHA POR ESTOQUE INSUFICIENTE ---")
    pedido_sem_estoque = Order(
        order_id="PED-002",
        customer_type="COMUM",
        region="RJ",
        payment_method="Boleto",
        items=[
            OrderItem("103", "Mouse Gamer", unit_price=150.0, quantity=5, category="Eletrônicos")
        ],
    )
    comprovante_2 = checkout.process_checkout(pedido_sem_estoque)
    print(comprovante_2)

    # Caso 3: Falha por dados de entrada invalidos (Preco invalido)
    print("--- CASO 3: FALHA POR DADOS INVALIDOS ---")
    pedido_invalido = Order(
        order_id="PED-003",
        customer_type="CORPORATIVO",
        region="OUTROS",
        payment_method="Cartão de Crédito",
        items=[
            OrderItem("102", "Cadeira de Escritório", unit_price=-10.0, quantity=1, category="Móveis")
        ],
    )
    comprovante_3 = checkout.process_checkout(pedido_invalido)
    print(comprovante_3)