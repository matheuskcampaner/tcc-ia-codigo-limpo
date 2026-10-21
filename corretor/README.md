# Corretor automático do experimento (domínio de cinema)

Scripts usados para corrigir as alterações feitas pelos participantes e medir o tamanho de cada alteração, como descrito na Seção 3.5.7 da monografia.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `corrigir_arquivo.py` | Executa um arquivo e aplica os 12 casos de regra e o fluxo de emissão do ingresso. Os casos de teste estão na lista `CASOS`, e o valor base é R$ 40,00. |
| `corrigir_turma.py` | Corrige todos os arquivos das pastas `parte1` e `parte2`, chamando `corrigir_arquivo.py` para cada um, e grava `results.json`. |
| `comparar_ast.py` | Compara a AST do arquivo do participante com a do original e conta as definições modificadas, as definições novas, a ampliação da lista de regras e os alertas de assinatura. |
| `consolidar_tabela.py` | Junta `results.json` em uma tabela, com a nota de correção e as medidas do tamanho da alteração. |

## Requisitos

Python 3.9 ou superior (por causa de `ast.unparse`) e pandas, usado apenas por `corrigir_turma.py` e `consolidar_tabela.py`. Os scripts foram verificados em Linux com Python 3.13.

O limite de tempo de `corrigir_arquivo.py` usa `signal.SIGALRM`, que só existe em Linux e macOS. No Windows, use o WSL.

`corrigir_arquivo.py` executa o código dos arquivos recebidos. Rode apenas arquivos de confiança, de preferência em um ambiente isolado.

## Nota de correção

- 2: todos os casos passam e o arquivo executa sem erro.
- 1: a regra do professor existe, mas algum caso falha ou o arquivo não executa em algum fluxo.
- 0: o arquivo não carrega ou não tem parâmetro para o professor.

## Conferência com os códigos de referência

Os códigos de referência estão em `corretor/referencias/`. Os originais se chamam `orig_<familia>.py` e os gabaritos se chamam `<familia>.py`. O nome da família tem a forma `<ferramenta>_p<domínio>_<condição>`. O primeiro número identifica o domínio (1 é o cinema, como em `gemini_p1_2`, e o e-commerce usa 2, como em `chatgpt_p2_1.py` em `codigo_gerado/ecommerce/`). O segundo número é a condição: `1` é o baseline e `2` é o Clean Code. Cada família é também o nome do arquivo gerado. Por exemplo, `gemini_p1_2` é o arquivo `gemini_p1_2.py` em `codigo_gerado/cinema/clean_code/`. Os originais são cópias dos arquivos de `baseline` e `clean_code` em `codigo_gerado/cinema/`, com o prefixo `orig_`.

Para corrigir um arquivo de referência:

    python corretor/corrigir_arquivo.py corretor/referencias/originais/orig_gemini_p1_2.py gemini_p1_2

Para medir os gabaritos contra os originais:

    python corretor/comparar_ast.py corretor/referencias/originais corretor/referencias/gabaritos

Resultado esperado: nos 8 originais falham só os casos do professor, e nos 8 gabaritos nenhum caso falha.

## Uso completo

Os arquivos dos participantes e a tabela `L.pkl` não são públicos, porque o termo de consentimento prevê identificação apenas pelo número do participante. Sem esses dados, `corrigir_turma.py` e `consolidar_tabela.py` não rodam. Quem tiver dados no mesmo formato pode executar:

    python corretor/corrigir_turma.py --parte1 pasta/parte1 --parte2 pasta/parte2 --tabela L.pkl --saida results.json
    python corretor/consolidar_tabela.py --resultados results.json --tabela L.pkl --originais pasta/arquivos_originais --saida G.pkl

Os arquivos enviados se chamam `p<cartão>_...py`, em que `cartão` é o número do participante (por exemplo, `p10_codigo1.py`). Os originais se chamam `orig_<familia>.py`. A tabela `L.pkl` tem as colunas `cartao`, `parte`, `condicao`, `ia`, `arquivo`, `paas` e `conf`.

## Observações

Para um arquivo que não carrega, `consolidar_tabela.py` fixa `erros_regressao` em 8, e os casos de emissão do ingresso não entram nessa contagem.
