# Análise estática com o SonarQube

Resultados da análise dos 24 arquivos gerados pelas ferramentas de IA (4 ferramentas, 2 domínios e 3 instruções), como descrito na monografia.

## Configuração

SonarQube Community Build 26.7, com o perfil de qualidade Sonar way e a análise feita pelo pysonar-scanner. O token de acesso foi informado pela variável de ambiente `SONAR_TOKEN` e não faz parte deste repositório.

## Indicadores

- Linhas de código (LOC)
- Complexidade ciclomática
- Complexidade cognitiva
- Problemas de manutenibilidade (code smells)
- Nota de manutenibilidade, de A a E

## Tabela por arquivo

`metricas_por_arquivo.csv` tem uma linha por arquivo, com as colunas `arquivo`, `dominio`, `instrucao`, `ferramenta`, `linhas_de_codigo`, `complexidade_ciclomatica`, `complexidade_cognitiva` e `problemas_de_manutenibilidade`. O nome em `arquivo` é o nome do arquivo em `codigo_gerado/`.

A tabela não tem a nota de manutenibilidade, porque o SonarQube a calcula por conjunto de arquivos e as capturas não a mostram por arquivo de forma identificável. A nota por conjunto é: no cinema, A nos três conjuntos (baseline, Clean Code e controle). No e-commerce, a nota por conjunto não foi registrada; o SonarQube atribuiu nota A em manutenibilidade ao projeto, que reúne os 12 arquivos.

## Capturas de tela

As capturas estão em `capturas/`. A interface do SonarQube está em inglês. Nas imagens, "Lines of Code" é o número de linhas de código, "Cyclomatic Complexity" é a complexidade ciclomática, "Cognitive Complexity" é a complexidade cognitiva e "Issues" são os problemas apontados.

| Arquivo | O que mostra |
|---|---|
| `cinema_01_loc_por_instrucao.png` | Linhas de código do domínio de cinema, por instrução |
| `cinema_02_complexidade_ciclomatica_por_instrucao.png` | Complexidade ciclomática do cinema, por instrução |
| `cinema_03_complexidade_cognitiva_por_instrucao.png` | Complexidade cognitiva do cinema, por instrução |
| `cinema_04_issues_por_instrucao.png` | Problemas apontados no cinema, por instrução |
| `cinema_05_manutenibilidade_resumo.png` | Resumo de manutenibilidade do cinema: problemas, débito técnico e nota |
| `cinema_06_manutenibilidade_nota_por_arquivo.png` | Gráfico de manutenibilidade do cinema, por arquivo (os arquivos sem débito não aparecem) |
| `ecommerce_01_loc_por_instrucao.png` | Linhas de código do domínio de e-commerce, por instrução |
| `ecommerce_02_complexidade_ciclomatica_por_instrucao.png` | Complexidade ciclomática do e-commerce, por instrução |
| `ecommerce_03_complexidade_cognitiva_por_instrucao.png` | Complexidade cognitiva do e-commerce, por instrução |
| `ecommerce_04_visao_geral_issues_bugs_seguranca.png` | Visão geral do e-commerce: problemas de segurança, de confiabilidade e de manutenibilidade |
| `ecommerce_05_issues_por_instrucao.png` | Problemas apontados no e-commerce, por instrução |
| `ecommerce_06_manutenibilidade_resumo.png` | Resumo de manutenibilidade do e-commerce: problemas, débito técnico e nota |
| `ecommerce_07_manutenibilidade_nota_por_arquivo.png` | Gráfico de manutenibilidade do e-commerce, por arquivo (sem rótulos) |
| `ecommerce_08_bugs_por_arquivo_controle.png` | Problemas de confiabilidade (bugs) por arquivo na instrução de controle do e-commerce |
| `ecommerce_09_seguranca_por_arquivo_controle.png` | Problemas de segurança por arquivo na instrução de controle do e-commerce |

As capturas por arquivo (linhas de código, complexidades e problemas de manutenibilidade) não estão aqui porque os mesmos valores estão em `metricas_por_arquivo.csv`.

## Nomes nas capturas

As capturas foram feitas quando o experimento tinha só o domínio de cinema, e os arquivos tinham nomes mais simples. Os nomes atuais são `<ferramenta>_p<domínio>_<condição>.py`.

- No cinema, `chatgpt_prompt1.py`, `chatgpt_prompt2.py` e `chatgpt_prompt3.py` correspondem a `chatgpt_p1_1.py`, `chatgpt_p1_2.py` e `chatgpt_p1_3.py`. O mesmo vale para as outras ferramentas. As pastas `prompts1_baseline`, `prompts2_cleancode` e `prompts3_controle` correspondem a `baseline`, `clean_code` e `controle` em `codigo_gerado/cinema/`.
- No e-commerce, `chatgpt_p2.1.py` equivale a `chatgpt_p2_1.py`, e assim por diante. As pastas `prompt2.1_baseline`, `prompt2.2_cleancode` e `prompt2.3_controle` correspondem a `baseline`, `clean_code` e `controle` em `codigo_gerado/ecommerce/`.

A tabela `metricas_por_arquivo.csv` usa os nomes atuais.
