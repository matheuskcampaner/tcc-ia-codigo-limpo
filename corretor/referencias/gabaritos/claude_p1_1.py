"""
Sistema de Venda de Ingressos de Cinema
========================================
Calcula o preço final do ingresso com base em:
- Valor base do ingresso
- Idade do cliente
- Dia da semana
- Se o cliente é estudante

Regras de desconto (não cumulativas — máximo de 50%):
  - Quarta-feira: 50% para todos os clientes
  - Demais dias:
      • Estudantes        → 50%
      • Crianças (≤ 12)   → 50%
      • Idosos (≥ 60)     → 50%
"""

import uuid
from datetime import datetime


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

DESCONTO_MEIA_ENTRADA = 0.50        # 50 %
DIA_DESCONTO_GERAL    = "quarta-feira"


# ---------------------------------------------------------------------------
# Lógica de negócio
# ---------------------------------------------------------------------------

def calcular_desconto(idade: int, dia_semana: str, estudante: bool, professor: bool = False) -> float:
    """
    Retorna a fração de desconto aplicável (0.0 ou 0.50).

    Parâmetros
    ----------
    idade      : Idade do cliente em anos completos.
    dia_semana : Dia da semana por extenso (ex.: 'Quarta-feira').
    estudante  : True se o cliente apresentou carteirinha de estudante.

    Retorno
    -------
    0.50 quando houver direito a desconto, 0.0 caso contrário.
    """
    if dia_semana.strip().lower() == DIA_DESCONTO_GERAL:
        return DESCONTO_MEIA_ENTRADA

    if estudante or idade <= 12 or idade >= 60 or professor:
        return DESCONTO_MEIA_ENTRADA

    return 0.0


def calcular_preco_final(valor_base: float, desconto: float) -> float:
    """Aplica o desconto ao valor base e retorna o preço final."""
    return round(valor_base * (1.0 - desconto), 2)


def gerar_id_bilhete() -> str:
    """Gera um ID único para o bilhete."""
    return str(uuid.uuid4()).upper()


# ---------------------------------------------------------------------------
# Interface principal
# ---------------------------------------------------------------------------

def vender_ingresso(
    valor_base: float,
    idade: int,
    dia_semana: str,
    estudante: bool,
    professor: bool = False,
) -> dict:
    """
    Processa a venda de um ingresso e retorna as informações do bilhete.

    Parâmetros
    ----------
    valor_base : Preço cheio do ingresso (R$).
    idade      : Idade do cliente.
    dia_semana : Dia da semana (ex.: 'Sexta-feira').
    estudante  : True se o cliente for estudante.

    Retorno
    -------
    Dicionário com os dados do bilhete emitido.
    """
    # Validações básicas
    if valor_base <= 0:
        raise ValueError("O valor base do ingresso deve ser positivo.")
    if idade < 0 or idade > 120:
        raise ValueError(f"Idade inválida: {idade}.")

    desconto       = calcular_desconto(idade, dia_semana, estudante, professor)
    preco_final    = calcular_preco_final(valor_base, desconto)
    id_bilhete     = gerar_id_bilhete()
    emitido_em     = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    bilhete = {
        "id"           : id_bilhete,
        "emitido_em"   : emitido_em,
        "valor_base"   : valor_base,
        "desconto_pct" : int(desconto * 100),
        "preco_final"  : preco_final,
        "idade"        : idade,
        "dia_semana"   : dia_semana,
        "estudante"    : estudante,
    }

    _exibir_bilhete(bilhete)
    return bilhete


# ---------------------------------------------------------------------------
# Exibição no console
# ---------------------------------------------------------------------------

def _exibir_bilhete(bilhete: dict) -> None:
    """Imprime o resumo do bilhete e a mensagem de sucesso."""
    linha = "=" * 52
    print(f"\n{linha}")
    print("          🎬  CINEMA ESTRELA  🎬")
    print(linha)
    print(f"  ID do Bilhete : {bilhete['id']}")
    print(f"  Emitido em    : {bilhete['emitido_em']}")
    print(linha)
    print(f"  Dia da semana : {bilhete['dia_semana']}")
    print(f"  Idade         : {bilhete['idade']} anos")
    print(f"  Estudante     : {'Sim' if bilhete['estudante'] else 'Não'}")
    print(linha)
    print(f"  Valor base    : R$ {bilhete['valor_base']:.2f}")

    if bilhete["desconto_pct"] > 0:
        print(f"  Desconto      : {bilhete['desconto_pct']}% (meia-entrada)")
    else:
        print("  Desconto      : Nenhum (ingresso inteiro)")

    print(f"  VALOR FINAL   : R$ {bilhete['preco_final']:.2f}")
    print(linha)
    print("  ✅  Ingresso emitido com sucesso!")
    print(f"{linha}\n")


# ---------------------------------------------------------------------------
# Exemplos de uso
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("\n>>> EXEMPLO 1 — Quarta-feira (desconto geral)")
    vender_ingresso(
        valor_base=30.00,
        idade=35,
        dia_semana="Quarta-feira",
        estudante=False,
    )

    print(">>> EXEMPLO 2 — Estudante em dia comum")
    vender_ingresso(
        valor_base=30.00,
        idade=22,
        dia_semana="Sexta-feira",
        estudante=True,
    )

    print(">>> EXEMPLO 3 — Criança em dia comum")
    vender_ingresso(
        valor_base=30.00,
        idade=10,
        dia_semana="Sábado",
        estudante=False,
    )

    print(">>> EXEMPLO 4 — Idoso em dia comum")
    vender_ingresso(
        valor_base=30.00,
        idade=65,
        dia_semana="Domingo",
        estudante=False,
    )

    print(">>> EXEMPLO 5 — Adulto sem desconto")
    vender_ingresso(
        valor_base=30.00,
        idade=40,
        dia_semana="Quinta-feira",
        estudante=False,
    )