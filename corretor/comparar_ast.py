# Mede o tamanho da alteração comparando a AST do arquivo do aluno com a do original
# Comentários e docstrings são ignorados. compare() devolve as definições existentes
# modificadas, as definições novas e a ampliação da lista de regras (fora de funções e classes). A soma das três é o número de unidades de edição
import ast
import copy
import difflib
import re
import sys

PADRAO_REGRA = re.compile(r'Desconto|Discount|Rule')


def ler_arvore(caminho):
    with open(caminho, encoding='utf-8', errors='replace') as f:
        arvore = ast.parse(f.read())
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and no.body:
            primeiro = no.body[0]
            if (isinstance(primeiro, ast.Expr)
                    and isinstance(getattr(primeiro, 'value', None), ast.Constant)
                    and isinstance(primeiro.value.value, str)):
                no.body = no.body[1:] or [ast.Pass()]
    return arvore


def unidades(arvore):
    # dumps: cada função, método e classe (sem os métodos) e o seu dump
    # assinaturas: os parâmetros de cada um, para achar mudanças de assinatura
    dumps, assinaturas = {}, {}

    def registrar(nome, func):
        dumps[nome] = ast.dump(func)
        a = func.args
        posicionais = [x.arg for x in a.posonlyargs + a.args]
        n_padrao = len(a.defaults)
        obrigatorios = set(posicionais[:len(posicionais) - n_padrao]) if n_padrao else set(posicionais)
        assinaturas[nome] = {'names': posicionais, 'kwonly': [x.arg for x in a.kwonlyargs],
                             'required': obrigatorios}

    for no in arvore.body:
        if isinstance(no, ast.FunctionDef):
            registrar(no.name, no)
        elif isinstance(no, ast.ClassDef):
            cabeca = copy.copy(no)
            cabeca.body = [m for m in no.body if not isinstance(m, ast.FunctionDef)] or [ast.Pass()]
            dumps[no.name] = ast.dump(cabeca)
            for m in no.body:
                if isinstance(m, ast.FunctionDef):
                    registrar(f'{no.name}.{m.name}', m)
            # Os campos de uma dataclass fazem o papel de assinatura da classe
            campos = [m.target.id for m in no.body
                      if isinstance(m, ast.AnnAssign) and isinstance(m.target, ast.Name)]
            if campos:
                com_padrao = {m.target.id for m in no.body
                              if isinstance(m, ast.AnnAssign) and m.value is not None}
                assinaturas[no.name + '(campos)'] = {'names': campos, 'kwonly': [],
                                                     'required': set(campos) - com_padrao}
    return dumps, assinaturas


def tamanho_da_lista_de_regras(arvore):
    # Maior lista de chamadas a *Desconto*, *Discount* ou *Rule* fora de funções e classes
    maior = 0

    def percorrer(no, dentro):
        nonlocal maior
        for filho in ast.iter_child_nodes(no):
            if (isinstance(filho, ast.List) and filho.elts and not dentro
                    and all(isinstance(e, ast.Call) and isinstance(e.func, ast.Name)
                            and PADRAO_REGRA.search(e.func.id) for e in filho.elts)):
                maior = max(maior, len(filho.elts))
            percorrer(filho, dentro or isinstance(filho, (ast.FunctionDef, ast.ClassDef)))

    percorrer(arvore, False)
    return maior


def linhas_das_definicoes(arvore):
    codigo = '\n'.join(ast.unparse(n) for n in arvore.body
                       if isinstance(n, (ast.FunctionDef, ast.ClassDef)))
    return codigo.splitlines()


def alertas_de_assinatura(orig, aluno):
    # Avisos de assinaturas que podem quebrar chamadas antigas (não entram na nota)
    alertas = []
    for nome, nova in aluno.items():
        if nome not in orig:
            continue
        antiga = orig[nome]
        comuns_nova = [n for n in nova['names'] if n in antiga['names']]
        comuns_antiga = [n for n in antiga['names'] if n in nova['names']]
        if comuns_nova != comuns_antiga or len(comuns_nova) < len(antiga['names']):
            alertas.append(f'{nome}: parâmetros originais reordenados/removidos')
        if nova['kwonly'] and not antiga['kwonly']:
            alertas.append(f'{nome}: parâmetros passaram a ser somente-nomeados')
        for param in (n for n in nova['names'] if n not in antiga['names']):
            if param in nova['required']:
                alertas.append(f'{nome}: novo parâmetro "{param}" sem valor padrão (chamadas antigas quebram)')
    return alertas


def compare(original, aluno):
    # Devolve None se o arquivo do aluno não compila
    try:
        arv_aluno = ler_arvore(aluno)
    except SyntaxError:
        return None
    arv_orig = ler_arvore(original)
    dump_o, assin_o = unidades(arv_orig)
    dump_a, assin_a = unidades(arv_aluno)

    modificadas = [k for k in dump_a if k in dump_o and dump_a[k] != dump_o[k]]
    # Os métodos de uma classe nova não contam à parte, a classe vale uma unidade
    novas = [k for k in dump_a if k not in dump_o
             and not ('.' in k and k.split('.')[0] not in dump_o)]
    ampliou_lista = int(tamanho_da_lista_de_regras(arv_aluno) > tamanho_da_lista_de_regras(arv_orig))

    adicionadas = removidas = 0
    for linha in difflib.ndiff(linhas_das_definicoes(arv_orig), linhas_das_definicoes(arv_aluno)):
        if linha.startswith('+ '):
            adicionadas += 1
        elif linha.startswith('- '):
            removidas += 1

    return {'defs_mod': len(modificadas), 'defs_novas': len(novas), 'registro_lista': ampliou_lista,
            'pontos_edicao': len(modificadas) + len(novas) + ampliou_lista,
            'linhas_add': adicionadas, 'linhas_rem': removidas,
            'defs_mod_lista': ', '.join(modificadas), 'defs_novas_lista': ', '.join(novas),
            'alertas': '; '.join(alertas_de_assinatura(assin_o, assin_a))}


if __name__ == '__main__':
    # Confere os gabaritos: python comparar_ast.py <pasta_originais> <pasta_gabaritos>
    pasta_orig, pasta_gab = sys.argv[1], sys.argv[2]
    for familia in ['chatgpt_p1_1', 'chatgpt_p1_2', 'claude_p1_1', 'claude_p1_2',
                    'gemini_p1_1', 'gemini_p1_2', 'githubcopilot_p1_1', 'githubcopilot_p1_2']:
        r = compare(f'{pasta_orig}/orig_{familia}.py', f'{pasta_gab}/{familia}.py')
        print(f"{familia:20s} mod={r['defs_mod']} novas={r['defs_novas']} reg={r['registro_lista']} "
              f"pontos={r['pontos_edicao']} +{r['linhas_add']}/-{r['linhas_rem']} | "
              f"{r['defs_mod_lista']} | {r['defs_novas_lista']} | {r['alertas']}")
