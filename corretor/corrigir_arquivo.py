# Corrige um arquivo enviado por um aluno: executa o arquivo e aplica os casos de teste
# Uso: python corrigir_arquivo.py arquivo.py familia (exemplo: gemini_p1_2)
# A familia diz qual é a estrutura do código. O resultado sai em JSON, em uma linha
import inspect
import io
import json
import re
import signal
import sys
import types
from contextlib import redirect_stderr, redirect_stdout

LIMITE_SEGUNDOS = 20
VALOR_BASE = 40.0

# Cada aluno deu um nome diferente aos parâmetros (professor, is_teacher...), então o papel do parâmetro é achado por palavra-chave
PAPEIS = [
    ('prof', ('prof', 'teach', 'docent')),
    ('estudante', ('estud', 'student')),
    ('idade', ('idade', 'age')),
    ('dia', ('dia', 'week', 'day')),
    ('base', ('valor', 'base', 'price', 'preco')),
]

DIAS = {'sexta': 'Sexta-feira', 'terca': 'Terça-feira', 'quarta': 'Quarta-feira',
        'quinta': 'Quinta-feira', 'sabado': 'Sábado'}
DIAS_ENUM = {'sexta': 'SEXTA', 'terca': 'TERCA', 'quarta': 'QUARTA',
             'quinta': 'QUINTA', 'sabado': 'SABADO'}

# Casos de teste (id, grupo, idade, estudante, professor, dia, preço esperado)
# O valor base é R$ 40,00
CASOS = [
    ('T7-1', 'antiga', 65, False, False, 'sexta', 20),
    ('T7-2', 'antiga', 20, True, False, 'quarta', 20),
    ('T7-3', 'antiga', 30, False, False, 'terca', 40),
    ('T7-4', 'nova', 30, False, True, 'terca', 20),
    ('T7-5', 'nova', 30, True, True, 'quarta', 20),
    ('X-crianca12', 'antiga_ext', 12, False, False, 'quinta', 20),
    ('X-idade13', 'antiga_ext', 13, False, False, 'quinta', 40),
    ('X-idade59', 'antiga_ext', 59, False, False, 'quinta', 40),
    ('X-idoso60', 'antiga_ext', 60, False, False, 'quinta', 20),
    ('X-estud-sab', 'antiga_ext', 20, True, False, 'sabado', 20),
    ('X-prof-sab', 'nova_ext', 30, False, True, 'sabado', 20),
    ('X-prof-idoso', 'nova_ext', 65, False, True, 'sexta', 20),
]

# Fluxo de emissão do ingresso (só nos baselines que têm emitir_ingresso)
CASOS_EMISSAO = [
    ('I-idoso', 'integracao', 65, False, False, 'sexta', 20),
    ('I-comum', 'integracao', 30, False, False, 'terca', 40),
    ('I-prof', 'integracao', 30, False, True, 'terca', 20),
]
FAMILIAS_COM_EMISSAO = ('chatgpt_p1_1', 'gemini_p1_1', 'githubcopilot_p1_1')


def papel(nome):
    for chave, palavras in PAPEIS:
        if any(p in nome.lower() for p in palavras):
            return chave
    return None


def parametros(func):
    return [p for p in inspect.signature(func).parameters if p != 'self']


def tem_professor(nomes):
    return any(papel(n) == 'prof' for n in nomes)


def argumentos(nomes, valores):
    # Liga cada parâmetro ao valor do seu papel
    return {n: valores[papel(n)] for n in nomes if papel(n) in valores}


def valores_do_caso(caso, nomes, dia, mensagem):
    _, _, idade, estudante, professor, _, _ = caso
    valores = {'base': VALOR_BASE, 'idade': idade, 'estudante': estudante, 'dia': dia}
    if tem_professor(nomes):
        valores['prof'] = professor
    elif professor:
        raise LookupError(mensagem)
    return valores


def carregar(caminho, resultado):
    # Compila e executa o arquivo como programa principal
    with open(caminho, encoding='utf-8', errors='replace') as f:
        fonte = f.read()
    try:
        codigo = compile(fonte, caminho, 'exec')
    except SyntaxError as e:
        resultado['load_error'] = f'SyntaxError: {e.msg} (linha {e.lineno})'
        return None
    modulo = types.ModuleType('__main__')
    modulo.__file__ = caminho
    sys.modules['__main__'] = modulo
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        try:
            exec(codigo, modulo.__dict__)
        except BaseException as e:
            resultado['main_error'] = f'{type(e).__name__}: {e}'
    return modulo.__dict__


# Uma função de cálculo por estrutura de código. Cada uma recebe um caso e devolve o preço

def preco_baseline(ns, caso):
    f = ns['calcular_preco_ingresso']
    nomes = parametros(f)
    v = valores_do_caso(caso, nomes, DIAS[caso[5]], 'funcao sem parametro de professor')
    return float(f(**argumentos(nomes, v)))


def preco_claude_baseline(ns, caso):
    f = ns['vender_ingresso']
    nomes = parametros(f)
    v = valores_do_caso(caso, nomes, DIAS[caso[5]], 'funcao sem parametro de professor')
    return float(f(**argumentos(nomes, v))['preco_final'])


def preco_chatgpt_clean(ns, caso):
    classe = ns['Ingresso']
    campos = list(classe.__dataclass_fields__)
    v = valores_do_caso(caso, campos, DIAS[caso[5]], 'classe de dados sem campo de professor')
    ingresso = classe(**argumentos(campos, v))
    calc = ns.get('calculadora') or ns['CalculadoraPrecoIngresso'](ns['regras'])
    return float(calc.calcular_preco_final(ingresso))


def preco_claude_clean(ns, caso):
    f = ns['calculate_ticket_price']
    nomes = parametros(f)
    v = valores_do_caso(caso, nomes, DIAS[caso[5]], 'fachada sem parametro de professor')
    return float(f(**argumentos(nomes, v)).final_price)


def preco_gemini_clean(ns, caso):
    _, _, idade, estudante, professor, dia, _ = caso
    nomes_cliente = parametros(ns['Cliente'].__init__)
    nomes_sessao = parametros(ns['Sessao'].__init__)
    dados = {'idade': idade, 'estudante': estudante}
    if tem_professor(nomes_cliente):
        dados['prof'] = professor
    elif professor:
        raise LookupError('Cliente sem campo de professor')
    cliente = ns['Cliente'](**argumentos(nomes_cliente, dados))
    dia_enum = getattr(ns['DiaSemana'], DIAS_ENUM[dia])
    sessao = ns['Sessao'](**argumentos(nomes_sessao, {'base': VALOR_BASE, 'dia': dia_enum}))
    calc = ns.get('calculadora')
    if calc is None:
        raise LookupError("variavel 'calculadora' nao foi criada")
    return float(calc.calcular_preco_final(cliente, sessao))


def preco_copilot_clean(ns, caso):
    nomes = parametros(ns['Ticket'].__init__)
    v = valores_do_caso(caso, nomes, DIAS[caso[5]].lower(), 'Ticket sem campo de professor')
    calc = ns.get('calculator')
    if calc is None:
        raise LookupError("variavel 'calculator' nao foi criada")
    return float(calc.calculate_final_price(ns['Ticket'](**argumentos(nomes, v))))


CALCULADORES = {
    'chatgpt_p1_1': preco_baseline, 'gemini_p1_1': preco_baseline,
    'githubcopilot_p1_1': preco_baseline, 'claude_p1_1': preco_claude_baseline,
    'chatgpt_p1_2': preco_chatgpt_clean, 'claude_p1_2': preco_claude_clean,
    'gemini_p1_2': preco_gemini_clean, 'githubcopilot_p1_2': preco_copilot_clean,
}


def registrar(resultado, caso, grupo, funcao):
    try:
        with redirect_stdout(io.StringIO()):
            obtido = funcao()
        resultado['tests'][caso[0]] = {'grupo': grupo, 'esperado': caso[6], 'obtido': obtido,
                                       'ok': abs(obtido - caso[6]) < 0.01}
    except BaseException as e:
        resultado['tests'][caso[0]] = {'grupo': grupo, 'esperado': caso[6], 'obtido': None,
                                       'ok': False, 'erro': f'{type(e).__name__}: {e}'[:120]}


def rodar_casos(ns, familia, resultado):
    calcular = CALCULADORES[familia]
    for caso in CASOS:
        registrar(resultado, caso, caso[1], lambda: calcular(ns, caso))


def emitir(ns, caso):
    # Chama emitir_ingresso e lê o último valor em reais que ele imprime
    f = ns['emitir_ingresso']
    nomes = parametros(f)
    v = valores_do_caso(caso, nomes, DIAS[caso[5]], 'emitir_ingresso sem parametro de professor')
    saida = io.StringIO()
    with redirect_stdout(saida):
        f(**argumentos(nomes, v))
    valores = re.findall(r'R\$\s*([\d]+[.,]\d\d)', saida.getvalue())
    return float(valores[-1].replace(',', '.'))


def rodar_emissao(ns, resultado):
    for caso in CASOS_EMISSAO:
        registrar(resultado, caso, 'integracao', lambda: emitir(ns, caso))


def nome_do_parametro_professor(ns, familia):
    # Só informativo, não entra na nota
    onde = {
        'chatgpt_p1_2': lambda: list(ns['Ingresso'].__dataclass_fields__),
        'gemini_p1_2': lambda: parametros(ns['Cliente'].__init__),
        'githubcopilot_p1_2': lambda: parametros(ns['Ticket'].__init__),
        'claude_p1_2': lambda: parametros(ns['calculate_ticket_price']),
        'claude_p1_1': lambda: parametros(ns['vender_ingresso']),
    }
    try:
        nomes = onde.get(familia, lambda: parametros(ns['calcular_preco_ingresso']))()
        return next((n for n in nomes if papel(n) == 'prof'), None)
    except BaseException:
        return None


def estourou_o_tempo(*_):
    raise TimeoutError('timeout')


def main():
    caminho, familia = sys.argv[1], sys.argv[2]
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, estourou_o_tempo)
        signal.alarm(LIMITE_SEGUNDOS)
    resultado = {'load_error': None, 'main_error': None, 'prof_name': None,
                 'tests': {}, 'notes': []}
    ns = carregar(caminho, resultado)
    if ns is None:
        print(json.dumps(resultado))
        return
    rodar_casos(ns, familia, resultado)
    if familia in FAMILIAS_COM_EMISSAO:
        rodar_emissao(ns, resultado)
    resultado['prof_name'] = nome_do_parametro_professor(ns, familia)
    print(json.dumps(resultado, ensure_ascii=False))


if __name__ == '__main__':
    main()
