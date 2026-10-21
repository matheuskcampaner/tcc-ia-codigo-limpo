# Junta os resultados da correção em uma tabela, com a nota de cada arquivo e o tamanho da alteração
# Uso: python consolidar_tabela.py --resultados results.json --tabela L.pkl --originais pasta/arquivos_originais --saida G.pkl
# Nota: 2 se todos os casos passam e o exemplo do arquivo executa sem erro
#       1 se a regra do professor existe, mas algum caso falha ou o arquivo não executa em algum fluxo
#       0 se o arquivo não carrega ou não tem parâmetro para o professor
import argparse
import json

import pandas as pd

from comparar_ast import compare

# Arquivo que não carrega: todos os casos contam como falhos (5 do T7, 8 da regra antiga e 4 da regra nova)
FALHAS_NAO_CARREGA = {'t7': 5, 'regressao': 8, 'regra_nova': 4, 'integracao': 0}


def contar_falhas(testes, nao_carrega):
    if nao_carrega:
        return FALHAS_NAO_CARREGA

    def falhou(casos):
        return sum(not c['ok'] for c in casos)

    def grupos(*nomes):
        return [c for c in testes.values() if c['grupo'] in nomes]

    t7 = [testes[i] for i in ('T7-1', 'T7-2', 'T7-3', 'T7-4', 'T7-5') if i in testes]
    emissao_antiga = [testes[i] for i in ('I-idoso', 'I-comum') if i in testes]
    return {'t7': falhou(t7),
            'regressao': falhou(grupos('antiga', 'antiga_ext')) + falhou(emissao_antiga),
            'regra_nova': falhou(grupos('nova', 'nova_ext')),
            'integracao': falhou(grupos('integracao'))}


def montar_linha(chave, r, pasta_originais):
    cartao, parte = map(int, chave.split('_'))
    familia, testes, nao_carrega = r['fam'], r['tests'], r['load_error']
    medidas = compare(f'{pasta_originais}/orig_{familia}.py', r['file']) or {}
    falhas = contar_falhas(testes, nao_carrega)
    total_falhas = sum(not c['ok'] for c in testes.values())

    if nao_carrega or r['prof_name'] is None:
        nota, nota_t7 = 0, 0
    else:
        nota_t7 = 2 if falhas['t7'] == 0 else 1
        nota = 2 if (total_falhas == 0 and not r['main_error']) else 1

    if nao_carrega:
        reprovados = 'arquivo não executa'
    else:
        reprovados = ', '.join(k for k, v in testes.items() if not v['ok'])
    return dict(cartao=cartao, parte=parte, arquivo=familia, load_error=nao_carrega,
                main_error=r['main_error'], prof_param=r['prof_name'],
                correcao=nota, correcao_core_T7=nota_t7, casos_T7_falhos=falhas['t7'],
                erros_regressao=falhas['regressao'], falhas_regra_nova=falhas['regra_nova'],
                falhas_integracao=falhas['integracao'], testes_falhos=reprovados, **medidas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resultados', default='results.json')
    ap.add_argument('--tabela', default='L.pkl')
    ap.add_argument('--originais', default='arquivos_originais')
    ap.add_argument('--saida', default='G.pkl')
    args = ap.parse_args()

    with open(args.resultados) as f:
        resultados = json.load(f)
    tabela = pd.read_pickle(args.tabela)

    linhas = [montar_linha(k, r, args.originais) for k, r in resultados.items()]
    G = (pd.DataFrame(linhas)
         .merge(tabela[['cartao', 'parte', 'condicao', 'ia', 'paas', 'conf']], on=['cartao', 'parte'])
         .sort_values(['cartao', 'parte']))
    G.to_pickle(args.saida)

    pd.set_option('display.width', 250)
    pd.set_option('display.max_columns', 30)
    colunas = ['cartao', 'parte', 'arquivo', 'correcao', 'correcao_core_T7', 'erros_regressao',
               'falhas_regra_nova', 'falhas_integracao', 'defs_mod', 'defs_novas', 'registro_lista',
               'pontos_edicao', 'linhas_add', 'linhas_rem', 'paas', 'conf']
    print(G[colunas].to_string(index=False))
    print()
    print(G[G.alertas.fillna('') != ''][['cartao', 'parte', 'alertas']].to_string(index=False, max_colwidth=200))
    print()
    print(G[G.correcao < 2][['cartao', 'parte', 'arquivo', 'load_error', 'main_error',
                             'testes_falhos', 'paas', 'conf']].to_string(index=False, max_colwidth=120))


if __name__ == '__main__':
    main()
