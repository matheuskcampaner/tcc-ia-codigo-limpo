# Corrige todos os arquivos enviados nas duas partes do experimento
# Uso: python corrigir_turma.py --parte1 pasta/parte1 --parte2 pasta/parte2 --tabela L.pkl --saida results.json
# L.pkl é uma tabela com as colunas cartao, parte e arquivo (a família do kit)
# Os arquivos enviados se chamam p<cartão>_..., por exemplo p10_codigo1.py
import argparse
import glob
import json
import os
import re
import subprocess
import sys

import pandas as pd

CORRETOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corrigir_arquivo.py')


def corrigir(caminho, familia):
    # Cada arquivo roda em um processo separado, para um erro não derrubar os outros
    try:
        proc = subprocess.run([sys.executable, CORRETOR, caminho, familia],
                              capture_output=True, text=True, timeout=40)
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {'load_error': f'harness: {type(e).__name__}: {e}', 'main_error': None,
                'tests': {}, 'prof_name': None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parte1', default='parte1')
    ap.add_argument('--parte2', default='parte2')
    ap.add_argument('--tabela', default='L.pkl')
    ap.add_argument('--saida', default='results.json')
    args = ap.parse_args()

    tabela = pd.read_pickle(args.tabela)
    resultados = {}
    for parte, pasta in ((1, args.parte1), (2, args.parte2)):
        for caminho in sorted(glob.glob(f'{pasta}/*.py')):
            cartao = int(re.search(r'p(\d+)_', caminho).group(1))
            linha = tabela[(tabela.cartao == cartao) & (tabela.parte == parte)]
            familia = linha.arquivo.iloc[0]
            r = corrigir(caminho, familia)
            r['file'] = caminho
            r['fam'] = familia
            resultados[f'{cartao}_{parte}'] = r
            falhas = [k for k, v in r['tests'].items() if not v['ok']]
            print(f"p{cartao:>2} P{parte} {familia:19s} prof={str(r['prof_name']):18s} "
                  f"load={r['load_error']} main={r['main_error']} falhas={falhas}")

    with open(args.saida, 'w') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
