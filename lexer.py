"""
Analisador Léxico da LangC
Universidade Federal do Ceará - Compiladores 2025.1

Usa o DFA construído pelo Algoritmo de Subconjuntos (nfa_to_dfa.py)
para tokenizar código-fonte escrito em LangC.

Estratégia: Maior Casamento (Maximal Munch)
-------------------------------------------
O lexer nunca decide qual token reconhecer pelo primeiro estado final
que encontra. Ele CONTINUA avançando enquanto houver transição válida,
guardando o último estado final visto. Só para quando trava — aí
retorna o token do último estado final guardado.

Exemplo com '==':
  Lê '=' → estado final EQ   (guarda: EQ, posição 1)
  Lê '=' → estado final EQEQ (guarda: EQEQ, posição 2)
  Próximo char não tem transição → para
  Retorna EQEQ (o maior casamento), não EQ

Regras de desempate (já resolvidas pelo DFA):
  1. Maior casamento: sempre vence o token mais longo.
  2. Prioridade: para casamentos de mesmo tamanho, vence o token
     de menor índice na lista (palavras reservadas antes de VAR).
"""

import sys
from er_to_nfa import build_langc_nfa, _reset_counter
from nfa_to_dfa import nfa_to_dfa


# ---------------------------------------------------------------------------
# Construção do DFA (feita uma única vez ao importar o módulo)
# ---------------------------------------------------------------------------

def _build_dfa():
    _reset_counter()
    nfa = build_langc_nfa()
    return nfa_to_dfa(nfa)


_DFA = _build_dfa()


# ---------------------------------------------------------------------------
# Estrutura de Token
# ---------------------------------------------------------------------------

class Token:
    """Representa um token reconhecido pelo analisador léxico."""

    def __init__(self, tipo, lexema, linha):
        self.tipo   = tipo    # ex.: "NUM", "VAR", "ADD"
        self.lexema = lexema  # string original no código-fonte
        self.linha  = linha   # número da linha (começa em 1)

    def __repr__(self):
        return f"Token({self.tipo}, {repr(self.lexema)}, linha={self.linha})"


# ---------------------------------------------------------------------------
# Maior Casamento (Maximal Munch)
# ---------------------------------------------------------------------------

def _proximo_token(dfa, source, pos, linha_atual):
    """
    A partir da posição 'pos' no código-fonte, avança pelo DFA
    usando a estratégia do maior casamento.

    Retorna (Token, nova_pos, nova_linha) ou levanta ErroLexico.

    Como funciona passo a passo:
      - state       : estado atual do DFA
      - last_accept : último estado final visitado (None se nenhum)
      - last_pos    : posição no source quando visitamos last_accept
      - last_linha  : linha quando visitamos last_accept

    Quando o DFA trava (sem transição para o próximo char):
      - Se last_accept existe → retorna o token desse ponto
      - Se não existe         → erro léxico
    """
    state       = dfa["start"]
    last_accept = None          # token do último estado final visto
    last_pos    = pos           # posição correspondente
    last_linha  = linha_atual   # linha correspondente

    j           = pos
    linha_j     = linha_atual

    while j < len(source):
        char  = source[j]
        trans = dfa["transitions"].get(state, {})

        if char not in trans:
            break                           # DFA travou

        state  = trans[char]
        j     += 1
        if char == "\n":
            linha_j += 1

        if state in dfa["accept"]:          # novo estado final
            last_accept = dfa["accept"][state]
            last_pos    = j
            last_linha  = linha_j

    # Nenhum estado final foi atingido → erro léxico
    if last_accept is None:
        char_ruim = repr(source[pos]) if pos < len(source) else "EOF"
        raise ErroLexico(
            f"Caractere inválido {char_ruim} na linha {linha_atual}"
        )

    lexema = source[pos:last_pos]
    return Token(last_accept, lexema, linha_atual), last_pos, last_linha


# ---------------------------------------------------------------------------
# Analisador Léxico principal
# ---------------------------------------------------------------------------

class ErroLexico(Exception):
    pass


def tokenizar(source, dfa=None):
    """
    Tokeniza a string 'source' e retorna a lista de Tokens reconhecidos.

    Tokens WHITESPACE são descartados automaticamente.
    Se encontrar um erro léxico, interrompe e retorna None
    (o chamador deve tratar a exceção ErroLexico se preferir).

    Parâmetros:
        source : str  — código-fonte em LangC
        dfa    : dict — DFA a usar (padrão: DFA global da LangC)

    Retorna:
        list[Token] ou None em caso de erro
    """
    if dfa is None:
        dfa = _DFA

    tokens      = []
    pos         = 0
    linha_atual = 1

    while pos < len(source):
        try:
            tok, pos, linha_atual = _proximo_token(dfa, source, pos, linha_atual)
        except ErroLexico as e:
            print(f"ERRO: {e}")
            return None

        # Descarta espaços em branco (não são tokens da linguagem)
        if tok.tipo == "WHITESPACE":
            continue

        # Desambiguação VAR vs INTEGER pelo primeiro caractere do lexema.
        # O NFA de VAR usa star(alnum) que inclui dígitos, causando conflitos.
        # Regras:
        #   - Começa com letra ou _ → VAR
        #   - Começa com dígito, só dígitos → INTEGER
        #   - Começa com dígito, mas tem letras (ex: "1valor") → ERRO léxico
        if tok.tipo in ("VAR", "INTEGER"):
            if tok.lexema[0].isdigit():
                if not tok.lexema.isdigit():
                    print(f"ERRO: token inválido '{tok.lexema}' na linha {tok.linha}")
                    return None
                tok.tipo = "INTEGER"
            else:
                tok.tipo = "VAR"

        # Valida tamanho do identificador (regra da LangC: máx 30 caracteres)
        if tok.tipo == "VAR" and len(tok.lexema) > 30:
            print(f"ERRO: identificador '{tok.lexema}' excede 30 caracteres "
                  f"(linha {tok.linha})")
            return None

        tokens.append(tok)

    return tokens


# ---------------------------------------------------------------------------
# Formatação da saída (formato exigido pelo enunciado)
# ---------------------------------------------------------------------------

def formatar_saida(tokens):
    """
    Formata a lista de tokens no formato exigido pelo enunciado:
    uma linha por linha do fonte, com os tipos dos tokens separados por espaço.

    Exemplo de saída:
        NUM VAR EQ NUM SEMICOLON
        NUM VAR EQ NUM ADD VAR SEMICOLON
        TEXT VAR EQ CONST SEMICOLON
    """
    if tokens is None:
        return "ERRO"

    # Agrupa tokens por linha
    linhas = {}
    for tok in tokens:
        linhas.setdefault(tok.linha, []).append(tok.tipo)

    if not linhas:
        return ""

    resultado = []
    for linha in sorted(linhas):
        resultado.append(" ".join(linhas[linha]))

    return "\n".join(resultado)


# ---------------------------------------------------------------------------
# Interface de linha de comando
# ---------------------------------------------------------------------------

def analisar_arquivo(caminho):
    """Lê um arquivo .langc e imprime os tokens linha a linha."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {caminho}")
        return

    tokens = tokenizar(source)
    print(formatar_saida(tokens))


def analisar_string(source):
    """Tokeniza uma string e imprime os tokens linha a linha."""
    tokens = tokenizar(source)
    print(formatar_saida(tokens))


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def _verificar(descricao, source, esperado):
    """Executa um caso de teste e imprime o resultado."""
    tokens = tokenizar(source)
    saida  = formatar_saida(tokens)
    ok     = saida.strip() == esperado.strip()
    status = "[OK]    " if ok else "[FALHOU]"
    print(f"  {status} {descricao}")
    if not ok:
        print(f"           Entrada  : {repr(source)}")
        print(f"           Esperado : {repr(esperado)}")
        print(f"           Obtido   : {repr(saida)}")
    return ok


def run_tests():
    print("\nExecutando testes do Analisador Léxico...\n")
    total   = 0
    passou  = 0

    casos = [
        # ------------------------------------------------------------------
        # Exemplo do enunciado
        # ------------------------------------------------------------------
        (
            "Exemplo do enunciado (3 linhas)",
            'num a = 0 ;\nnum b = 5 + a ;\ntext c = "teSte" ;',
            "NUM VAR EQ INTEGER SEMICOLON\n"
            "NUM VAR EQ INTEGER ADD VAR SEMICOLON\n"
            "TEXT VAR EQ CONST SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # Declarações simples
        # ------------------------------------------------------------------
        (
            "Declaração num simples",
            "num x = 10 ;",
            "NUM VAR EQ INTEGER SEMICOLON"
        ),
        (
            "Declaração text",
            'text msg = "Ola" ;',
            "TEXT VAR EQ CONST SEMICOLON"
        ),
        (
            "Declaração bool com true",
            "bool b = true ;",
            "BOOL VAR EQ TRUE SEMICOLON"
        ),
        (
            "Declaração bool com false",
            "bool b = false ;",
            "BOOL VAR EQ FALSE SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # Palavras reservadas não viram VAR
        # ------------------------------------------------------------------
        (
            "Prioridade: 'num' é NUM, não VAR",
            "num num = 5 ;",
            "NUM NUM EQ INTEGER SEMICOLON"
        ),
        (
            "Prioridade: 'show' é SHOW, não VAR",
            "show show ;",
            "SHOW SHOW SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # Operadores aritméticos
        # ------------------------------------------------------------------
        (
            "Operadores aritméticos",
            "num r = 2 + 3 * 4 / 1 - 0 ;",
            "NUM VAR EQ INTEGER ADD INTEGER MUL INTEGER DIV INTEGER SUB INTEGER SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # Operadores relacionais e == vs =
        # ------------------------------------------------------------------
        (
            "Maior casamento: == é EQEQ, não dois EQ",
            "show a == b ;",
            "SHOW VAR EQEQ VAR SEMICOLON"
        ),
        (
            "Atribuição com = simples",
            "num a = 5 ;",
            "NUM VAR EQ INTEGER SEMICOLON"
        ),
        (
            "Operadores > e <",
            "show a > b ;",
            "SHOW VAR GT VAR SEMICOLON"
        ),
        (
            "Operador <",
            "show x < 10 ;",
            "SHOW VAR LT INTEGER SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # Parênteses
        # ------------------------------------------------------------------
        (
            "Expressão com parênteses",
            "num r = ( 2 + 3 ) ;",
            "NUM VAR EQ LPAREN INTEGER ADD INTEGER RPAREN SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # String literal com espaço interno
        # ------------------------------------------------------------------
        (
            "String com espaço interno",
            'text s = "oi vc" ;',
            "TEXT VAR EQ CONST SEMICOLON"
        ),
        (
            "String vazia",
            'text s = "" ;',
            "TEXT VAR EQ CONST SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # Identificadores variados
        # ------------------------------------------------------------------
        (
            "Identificador com underscore",
            "num _x = 1 ;",
            "NUM VAR EQ INTEGER SEMICOLON"
        ),
        (
            "Identificador com dígito",
            "num valor1 = 99 ;",
            "NUM VAR EQ INTEGER SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # Programa completo (exemplo da especificação)
        # ------------------------------------------------------------------
        (
            "Programa completo da especificação",
            "show 2 > 2 ;\n"
            "num a = 5 ;\n"
            "num b = 10 ;\n"
            "num soma = a + b ;\n"
            'text mensagem = "Oi!" ;\n'
            "show mensagem ;\n"
            "show a ;\n"
            "show soma ;\n"
            "show a < b ;\n"
            "show a = 5 ;",
            "SHOW INTEGER GT INTEGER SEMICOLON\n"
            "NUM VAR EQ INTEGER SEMICOLON\n"
            "NUM VAR EQ INTEGER SEMICOLON\n"
            "NUM VAR EQ VAR ADD VAR SEMICOLON\n"
            "TEXT VAR EQ CONST SEMICOLON\n"
            "SHOW VAR SEMICOLON\n"
            "SHOW VAR SEMICOLON\n"
            "SHOW VAR SEMICOLON\n"
            "SHOW VAR LT VAR SEMICOLON\n"
            "SHOW VAR EQ INTEGER SEMICOLON"
        ),

        # ------------------------------------------------------------------
        # Erros léxicos
        # ------------------------------------------------------------------
        (
            "Erro léxico: @ inválido",
            "num @x = 1 ;",
            "ERRO"
        ),
        (
            "Erro léxico: # inválido",
            "# comentario",
            "ERRO"
        ),
    ]

    for descricao, source, esperado in casos:
        total  += 1
        passou += _verificar(descricao, source, esperado)

    print(f"\n  Resultado: {passou}/{total} testes passaram\n")
    return passou == total


# ---------------------------------------------------------------------------
# Execução direta
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Se receber argumento, lê do arquivo
    if len(sys.argv) > 1:
        analisar_arquivo(sys.argv[1])
        sys.exit(0)

    # Sem argumento: roda os testes
    sucesso = run_tests()

    if sucesso:
        # Demonstração interativa com o exemplo do enunciado
        print("=" * 60)
        print("  Demonstração — Exemplo do enunciado")
        print("=" * 60)
        exemplo = 'num a = 0 ;\nnum b = 5 + a ;\ntext c = "teSte" ;'
        print("\nEntrada:")
        for linha in exemplo.splitlines():
            print(f"  {linha}")
        print("\nSaída:")
        analisar_string(exemplo)

        # Demonstração com programa completo
        print("\n" + "=" * 60)
        print("  Demonstração — Programa completo")
        print("=" * 60)
        programa = (
            "show 2 > 2 ;\n"
            "num a = 5 ;\n"
            "num b = 10 ;\n"
            "num soma = a + b ;\n"
            'text mensagem = "Oi!" ;\n'
            "show mensagem ;\n"
            "show a ;\n"
            "show soma ;\n"
            "show a < b ;\n"
            "show a = 5 ;"
        )
        print("\nEntrada:")
        for linha in programa.splitlines():
            print(f"  {linha}")
        print("\nSaída:")
        analisar_string(programa)
