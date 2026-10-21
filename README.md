# tcc-ia-codigo-limpo

Material de apoio da monografia "Avaliação do Uso de Inteligência Artificial Generativa no Apoio à Produção de Código Limpo", trabalho de conclusão do curso de Ciência da Computação da Universidade Estadual de Maringá (UEM), 2026.

Autor: Matheus Kochepki Campaner. Orientador: Prof. Dr. Renato Balancieri.

O trabalho avalia se instruções de Clean Code e SOLID na geração de código por inteligência artificial tornam o código mais fácil de compreender e de modificar do que o código gerado apenas com requisitos funcionais. Quatro ferramentas (ChatGPT, Claude, Gemini e GitHub Copilot) geraram código em Python para dois domínios, cinema e e-commerce, sob três instruções (baseline, Clean Code e controle). Os 24 arquivos foram analisados com o SonarQube, e oito deles, do domínio de cinema, foram lidos e alterados por estudantes em um experimento cruzado.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `instrucoes/` | As seis instruções de geração, uma por domínio e instrução, e, em `instrucoes_participantes/`, as instruções entregues aos participantes nas duas partes do experimento |
| `codigo_gerado/` | Os 24 arquivos gerados pelas ferramentas, em `cinema/` e `ecommerce/`, separados em `baseline/`, `clean_code/` e `controle/`. O arquivo `CHECKSUMS.txt` traz o código SHA-256 de cada arquivo |
| `sonarqube/` | Tabela com as métricas de cada arquivo e capturas de tela da análise. Ver o `README.md` da pasta |
| `corretor/` | Scripts que corrigem as alterações dos participantes e medem o tamanho de cada alteração, com os códigos de referência em `referencias/`. Ver o `README.md` da pasta |
| `desenho_experimento/` | Tabela com o código que cada cartão recebeu em cada parte do experimento |

## Como conferir os arquivos gerados

Os arquivos de `codigo_gerado/` estão como foram gerados, sem alterações. Para conferir, execute dentro de `codigo_gerado/`, em Linux ou macOS, `sha256sum -c CHECKSUMS.txt` (no macOS, `shasum -a 256 -c CHECKSUMS.txt`). No Windows, o PowerShell calcula o mesmo código de cada arquivo com `Get-FileHash`.

## Como repetir a análise

A análise estática usou o SonarQube Community Build 26.7, com o perfil de qualidade Sonar way e o pysonar-scanner. Para repetir, crie um projeto no SonarQube e execute o scanner sobre `codigo_gerado/`, informando o token pela variável de ambiente `SONAR_TOKEN`. Nenhum token faz parte deste repositório.

## Como usar o corretor

Os comandos, os requisitos e a conferência com os códigos de referência estão no `README.md` de `corretor/`.

## O que não está neste repositório

Os dados dos participantes, isto é, as respostas dos formulários e os arquivos enviados por eles, não estão aqui. O termo de consentimento previu o uso acadêmico dos dados e a identificação apenas pelo número do participante. Esses dados estão disponíveis mediante solicitação ao autor, pelo e-mail ra126609@uem.br.

## Licença

Este repositório usa a licença MIT. Ver o arquivo `LICENSE`.
