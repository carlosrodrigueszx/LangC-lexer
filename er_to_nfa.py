"""
Algoritmo de Thompson: Expressões Regulares → NFA
Universidade Federal do Ceará - Compiladores 2025.1
Linguagem: LangC

Estrutura do NFA:
{
    "states":      conjunto de inteiros representando estados,
    "alphabet":    conjunto de caracteres reconhecidos,
    "transitions": {estado: {char: {conjunto de estados destino}}},
    "epsilon":     {estado: {conjunto de estados destino por ε}},
    "start":       estado inicial (inteiro),
    "accept":      {estado_final: nome_do_token}
}
"""


# ---------------------------------------------------------------------------
# Contador global de estados — garante IDs únicos ao combinar NFAs
# ---------------------------------------------------------------------------

_state_counter = 0


def _new_state():
    """Retorna um novo ID de estado único."""
    global _state_counter
    s = _state_counter
    _state_counter += 1
    return s


def _reset_counter():
    """Reinicia o contador (útil para testes)."""
    global _state_counter
    _state_counter = 0


# ---------------------------------------------------------------------------
# Primitivas de Thompson
# ---------------------------------------------------------------------------

def nfa_symbol(char):
    """
    NFA que reconhece exatamente um caractere.

        (s0) --char--> (s1)

    Retorna um NFA sem token associado ainda.
    """
    s0, s1 = _new_state(), _new_state()
    return {
        "states":      {s0, s1},
        "alphabet":    {char},
        "transitions": {s0: {char: {s1}}},
        "epsilon":     {},
        "start":       s0,
        "accept":      {s1: None},   # token será atribuído depois
    }


def nfa_epsilon():
    """
    NFA que reconhece apenas a string vazia (ε).

        (s0) --ε--> (s1)
    """
    s0, s1 = _new_state(), _new_state()
    return {
        "states":      {s0, s1},
        "alphabet":    set(),
        "transitions": {},
        "epsilon":     {s0: {s1}},
        "start":       s0,
        "accept":      {s1: None},
    }


# ---------------------------------------------------------------------------
# Operações compostas de Thompson
# ---------------------------------------------------------------------------

def nfa_concat(m, n):
    """
    Concatenação: M · N

    Liga cada estado final de M ao estado inicial de N por ε.
    O resultado aceita o que M aceita seguido do que N aceita.

        M_start --> ... --> M_accepts -ε-> N_start --> ... --> N_accepts
    """
    # Copia as transições ε de ambos
    new_epsilon = {**m["epsilon"]}
    for s, targets in n["epsilon"].items():
        new_epsilon[s] = new_epsilon.get(s, set()) | targets

    # Liga os estados finais de M ao início de N por ε
    for accept_state in m["accept"]:
        new_epsilon[accept_state] = (
            new_epsilon.get(accept_state, set()) | {n["start"]}
        )

    # Copia as transições normais de ambos
    new_transitions = {**m["transitions"]}
    for s, chars in n["transitions"].items():
        if s not in new_transitions:
            new_transitions[s] = {}
        for c, targets in chars.items():
            new_transitions[s][c] = (
                new_transitions[s].get(c, set()) | targets
            )

    return {
        "states":      m["states"] | n["states"],
        "alphabet":    m["alphabet"] | n["alphabet"],
        "transitions": new_transitions,
        "epsilon":     new_epsilon,
        "start":       m["start"],
        "accept":      n["accept"],   # apenas os finais de N aceitam
    }


def nfa_union(m, n):
    """
    Alternância: M | N

    Cria um novo estado inicial com ε para M e N,
    e um novo estado final alcançado por ε de ambos.

              ε-> M_start --> ... --> M_accepts -ε
    new_start                                      --> new_accept
              ε-> N_start --> ... --> N_accepts -ε
    """
    new_start  = _new_state()
    new_accept = _new_state()

    new_epsilon = {
        new_start: {m["start"], n["start"]},
        **m["epsilon"],
    }
    for s, targets in n["epsilon"].items():
        new_epsilon[s] = new_epsilon.get(s, set()) | targets

    # Liga antigos estados finais ao novo estado final por ε
    for accept_state in m["accept"]:
        new_epsilon[accept_state] = (
            new_epsilon.get(accept_state, set()) | {new_accept}
        )
    for accept_state in n["accept"]:
        new_epsilon[accept_state] = (
            new_epsilon.get(accept_state, set()) | {new_accept}
        )

    new_transitions = {**m["transitions"]}
    for s, chars in n["transitions"].items():
        if s not in new_transitions:
            new_transitions[s] = {}
        for c, targets in chars.items():
            new_transitions[s][c] = (
                new_transitions[s].get(c, set()) | targets
            )

    return {
        "states":      m["states"] | n["states"] | {new_start, new_accept},
        "alphabet":    m["alphabet"] | n["alphabet"],
        "transitions": new_transitions,
        "epsilon":     new_epsilon,
        "start":       new_start,
        "accept":      {new_accept: None},
    }


def nfa_star(m):
    """
    Kleene star: M*  (zero ou mais repetições de M)

    Cria novo estado inicial e final.
    O novo início vai por ε ao início de M e ao novo final.
    Os finais de M vão por ε ao início de M (repetição) e ao novo final.

        new_start -ε-> M_start --> ... --> M_accepts -ε-> new_accept
            |                                    |
            ε------------------------------------ε (loop)
            ε-> new_accept (aceita string vazia)
    """
    new_start  = _new_state()
    new_accept = _new_state()

    new_epsilon = {
        new_start: {m["start"], new_accept},
        **m["epsilon"],
    }
    for accept_state in m["accept"]:
        new_epsilon[accept_state] = (
            new_epsilon.get(accept_state, set()) | {m["start"], new_accept}
        )

    return {
        "states":      m["states"] | {new_start, new_accept},
        "alphabet":    m["alphabet"],
        "transitions": {**m["transitions"]},
        "epsilon":     new_epsilon,
        "start":       new_start,
        "accept":      {new_accept: None},
    }


def nfa_plus(m):
    """
    M+  (uma ou mais repetições) — equivale a M · M*
    """
    return nfa_concat(m, nfa_star(m))


def nfa_optional(m):
    """
    M?  (zero ou uma ocorrência) — equivale a M | ε
    """
    return nfa_union(m, nfa_epsilon())


# ---------------------------------------------------------------------------
# Funções auxiliares para construir NFAs a partir de strings e classes
# ---------------------------------------------------------------------------

def nfa_string(s):
    """
    Reconhece a string literal s (ex.: 'num', 'show').
    Constrói por concatenação de nfa_symbol para cada caractere.
    """
    if not s:
        return nfa_epsilon()
    result = nfa_symbol(s[0])
    for ch in s[1:]:
        result = nfa_concat(result, nfa_symbol(ch))
    return result


def nfa_char_class(chars):
    """
    Reconhece qualquer caractere do conjunto chars.
    Ex.: nfa_char_class('abc') reconhece a | b | c

    Constrói por alternância sequencial.
    """
    chars = list(chars)
    result = nfa_symbol(chars[0])
    for ch in chars[1:]:
        result = nfa_union(result, nfa_symbol(ch))
    return result


def nfa_range(start_char, end_char):
    """
    Reconhece qualquer caractere no intervalo [start_char, end_char].
    Ex.: nfa_range('a', 'z')
    """
    chars = [chr(c) for c in range(ord(start_char), ord(end_char) + 1)]
    return nfa_char_class(chars)


def nfa_any_except(excluded_chars):
    """
    Reconhece qualquer caractere do alfabeto LangC exceto os em excluded_chars.
    Usado para construir o NFA de strings literais: "[^"]*"
    """
    # Alfabeto completo da LangC (letras, dígitos e símbolos permitidos)
    alphabet = set()
    for c in range(ord('a'), ord('z') + 1):
        alphabet.add(chr(c))
    for c in range(ord('A'), ord('Z') + 1):
        alphabet.add(chr(c))
    for c in range(ord('0'), ord('9') + 1):
        alphabet.add(chr(c))
    alphabet |= set(' \t\n+-*/=>()<;!@#$%&?|_\'"')

    allowed = alphabet - set(excluded_chars)
    return nfa_char_class(sorted(allowed))


# ---------------------------------------------------------------------------
# Construção dos NFAs individuais para cada token da LangC
# ---------------------------------------------------------------------------

def build_token_nfa(token_name, nfa):
    """Associa um nome de token a todos os estados finais do NFA."""
    nfa["accept"] = {s: token_name for s in nfa["accept"]}
    return nfa


def build_all_token_nfas():
    """
    Retorna lista de (token_name, nfa) na ordem de PRIORIDADE.
    Palavras reservadas devem vir ANTES de VAR.
    == deve vir ANTES de =.
    """

    # ------------------------------------------------------------------
    # Letras e dígitos — reutilizados em vários tokens
    # ------------------------------------------------------------------
    lower   = nfa_range('a', 'z')
    upper   = nfa_range('A', 'Z')
    digit   = nfa_range('0', '9')
    letter  = nfa_union(lower, upper)
    alnum   = nfa_union(nfa_union(letter, digit), nfa_symbol('_'))

    # ------------------------------------------------------------------
    # 1. Palavras reservadas (prioridade máxima — vêm antes de VAR)
    # ------------------------------------------------------------------
    kw_num   = build_token_nfa("NUM",   nfa_string("num"))
    kw_text  = build_token_nfa("TEXT",  nfa_string("text"))
    kw_bool  = build_token_nfa("BOOL",  nfa_string("bool"))
    kw_show  = build_token_nfa("SHOW",  nfa_string("show"))
    kw_true  = build_token_nfa("TRUE",  nfa_string("true"))
    kw_false = build_token_nfa("FALSE", nfa_string("false"))

    # ------------------------------------------------------------------
    # 2. Identificadores: [a-zA-Z_][a-zA-Z0-9_]*
    #    (limite de 30 chars é verificado no analisador léxico)
    # ------------------------------------------------------------------
    id_start = nfa_union(letter, nfa_symbol('_'))
    id_rest  = nfa_star(alnum)
    var_nfa  = build_token_nfa("VAR", nfa_concat(id_start, id_rest))

    # ------------------------------------------------------------------
    # 3. Números inteiros: [0-9]+
    # ------------------------------------------------------------------
    integer_nfa = build_token_nfa("INTEGER", nfa_plus(digit))

    # ------------------------------------------------------------------
    # 4. String literal: "[^"]*"
    #    Qualquer sequência de caracteres entre aspas duplas
    # ------------------------------------------------------------------
    quote       = nfa_symbol('"')
    inner_char  = nfa_any_except('"')
    inner_star  = nfa_star(inner_char)
    string_nfa  = build_token_nfa(
        "CONST",
        nfa_concat(quote, nfa_concat(inner_star, quote))
    )

    # ------------------------------------------------------------------
    # 5. Operadores — == ANTES de = (regra do maior casamento)
    # ------------------------------------------------------------------
    eqeq_nfa = build_token_nfa("EQEQ",   nfa_string("=="))
    eq_nfa   = build_token_nfa("EQ",     nfa_symbol('='))
    gt_nfa   = build_token_nfa("GT",     nfa_symbol('>'))
    lt_nfa   = build_token_nfa("LT",     nfa_symbol('<'))
    add_nfa  = build_token_nfa("ADD",    nfa_symbol('+'))
    sub_nfa  = build_token_nfa("SUB",    nfa_symbol('-'))
    mul_nfa  = build_token_nfa("MUL",    nfa_symbol('*'))
    div_nfa  = build_token_nfa("DIV",    nfa_symbol('/'))

    # ------------------------------------------------------------------
    # 6. Pontuação
    # ------------------------------------------------------------------
    lparen_nfa    = build_token_nfa("LPAREN",    nfa_symbol('('))
    rparen_nfa    = build_token_nfa("RPAREN",    nfa_symbol(')'))
    semicolon_nfa = build_token_nfa("SEMICOLON", nfa_symbol(';'))

    # ------------------------------------------------------------------
    # 7. Espaço em branco (será descartado pelo analisador léxico)
    # ------------------------------------------------------------------
    ws_char      = nfa_char_class(' \t\n')
    whitespace_nfa = build_token_nfa("WHITESPACE", nfa_plus(ws_char))

    # ------------------------------------------------------------------
    # Ordem de prioridade (mais prioritário primeiro)
    #
    # ATENÇÃO: INTEGER e CONST devem vir ANTES de VAR.
    # O NFA de VAR usa star(alnum), e alnum inclui dígitos. Isso faz
    # com que dígitos isolados também atinjam o estado final de VAR via
    # epsilon-closure após o move. INTEGER precisa de índice menor para vencer.
    # ------------------------------------------------------------------
    return [
        ("NUM",       kw_num),
        ("TEXT",      kw_text),
        ("BOOL",      kw_bool),
        ("SHOW",      kw_show),
        ("TRUE",      kw_true),
        ("FALSE",     kw_false),
        ("INTEGER",   integer_nfa),
        ("CONST",     string_nfa),
        ("VAR",       var_nfa),
        ("EQEQ",      eqeq_nfa),
        ("EQ",        eq_nfa),
        ("GT",        gt_nfa),
        ("LT",        lt_nfa),
        ("ADD",       add_nfa),
        ("SUB",       sub_nfa),
        ("MUL",       mul_nfa),
        ("DIV",       div_nfa),
        ("LPAREN",    lparen_nfa),
        ("RPAREN",    rparen_nfa),
        ("SEMICOLON", semicolon_nfa),
        ("WHITESPACE",whitespace_nfa),
    ]


# ---------------------------------------------------------------------------
# Combinação de todos os NFAs em um único NFA
# ---------------------------------------------------------------------------

def combine_nfas(token_nfas):
    """
    Cria um NFA combinado com um novo estado inicial que vai por ε
    para o início de cada NFA individual.

                   ε-> NFA_NUM
                   ε-> NFA_TEXT
    new_start -->  ε-> NFA_VAR
                   ε-> ...

    A prioridade é resolvida pela ORDEM da lista: se dois estados finais
    forem atingidos ao mesmo tempo (no DFA), vence o de menor índice na lista.
    Cada estado final carrega o nome do seu token.
    """
    new_start = _new_state()
    combined = {
        "states":      {new_start},
        "alphabet":    set(),
        "transitions": {},
        "epsilon":     {new_start: set()},
        "start":       new_start,
        "accept":      {},
        # Guarda a ordem de prioridade de cada token
        "priority":    {},
    }

    for priority, (token_name, nfa) in enumerate(token_nfas):
        # Liga o novo estado inicial ao início deste NFA por ε
        combined["epsilon"][new_start].add(nfa["start"])

        # Incorpora estados, alfabeto, transições e ε-transições
        combined["states"]   |= nfa["states"]
        combined["alphabet"] |= nfa["alphabet"]

        for s, chars in nfa["transitions"].items():
            if s not in combined["transitions"]:
                combined["transitions"][s] = {}
            for c, targets in chars.items():
                combined["transitions"][s][c] = (
                    combined["transitions"][s].get(c, set()) | targets
                )

        for s, targets in nfa["epsilon"].items():
            combined["epsilon"][s] = (
                combined["epsilon"].get(s, set()) | targets
            )

        # Registra os estados finais e seus tokens
        for accept_state, token in nfa["accept"].items():
            combined["accept"][accept_state] = token
            combined["priority"][accept_state] = priority

    return combined


# ---------------------------------------------------------------------------
# Interface pública principal
# ---------------------------------------------------------------------------

def build_langc_nfa():
    """
    Ponto de entrada principal.
    Retorna o NFA combinado para todos os tokens da LangC.
    """
    _reset_counter()
    token_nfas = build_all_token_nfas()
    return combine_nfas(token_nfas)


# ---------------------------------------------------------------------------
# Utilitários de visualização e depuração
# ---------------------------------------------------------------------------

def print_nfa(nfa, title="NFA"):
    """Imprime o NFA de forma legível para depuração."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"  Estado inicial : {nfa['start']}")
    print(f"  Estados finais : {nfa['accept']}")
    print(f"  Total de estados: {len(nfa['states'])}")
    print(f"  Alfabeto ({len(nfa['alphabet'])} símbolos): "
          f"{sorted(nfa['alphabet'])[:10]}{'...' if len(nfa['alphabet']) > 10 else ''}")

    print(f"\n  Transições normais:")
    for state in sorted(nfa["transitions"]):
        for char, targets in sorted(nfa["transitions"][state].items()):
            print(f"    δ({state}, '{char}') = {sorted(targets)}")

    print(f"\n  Transições ε:")
    for state in sorted(nfa["epsilon"]):
        targets = nfa["epsilon"][state]
        if targets:
            print(f"    ε({state}) = {sorted(targets)}")
    print()


def print_summary(nfa):
    """Imprime apenas um resumo do NFA combinado."""
    print(f"\n{'='*60}")
    print(f"  NFA Combinado - LangC")
    print(f"{'='*60}")
    print(f"  Total de estados : {len(nfa['states'])}")
    print(f"  Estado inicial   : {nfa['start']}")
    print(f"  Estados finais   : {len(nfa['accept'])}")
    print(f"  Alfabeto         : {len(nfa['alphabet'])} símbolos")

    print(f"\n  Tokens reconhecidos (por prioridade):")
    # Agrupa estados finais por token
    token_states = {}
    for state, token in nfa["accept"].items():
        token_states.setdefault(token, []).append(state)

    priority = nfa.get("priority", {})
    seen = set()
    for state in sorted(priority, key=lambda s: priority[s]):
        token = nfa["accept"][state]
        if token not in seen:
            seen.add(token)
            p = priority[state]
            print(f"    [{p:02d}] {token:12s} → estados finais: "
                  f"{sorted(token_states[token])}")
    print()


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def _test_nfa_symbol():
    _reset_counter()
    nfa = nfa_symbol('a')
    assert nfa["start"] == 0
    assert 1 in nfa["accept"]
    assert nfa["transitions"][0]['a'] == {1}
    print("  [OK] nfa_symbol")


def _test_nfa_string():
    _reset_counter()
    nfa = nfa_string("num")
    # Deve ter 6 estados: 3 concatenações × 2 estados cada
    assert len(nfa["states"]) == 6
    print("  [OK] nfa_string('num')")


def _test_nfa_union():
    _reset_counter()
    m = nfa_symbol('a')
    n = nfa_symbol('b')
    u = nfa_union(m, n)
    # Novo start + novo accept = 6 estados no total
    assert len(u["states"]) == 6
    assert len(u["accept"]) == 1
    print("  [OK] nfa_union(a, b)")


def _test_nfa_star():
    _reset_counter()
    m = nfa_symbol('a')
    s = nfa_star(m)
    assert len(s["accept"]) == 1
    print("  [OK] nfa_star(a)")


def _test_nfa_plus():
    _reset_counter()
    m = nfa_range('0', '9')
    p = nfa_plus(m)
    assert len(p["accept"]) == 1
    print("  [OK] nfa_plus([0-9])")


def _test_combined_nfa():
    nfa = build_langc_nfa()
    assert nfa["start"] is not None
    assert len(nfa["accept"]) > 0
    # Verifica que todos os tokens esperados estão presentes
    tokens_presentes = set(nfa["accept"].values())
    tokens_esperados = {
        "NUM", "TEXT", "BOOL", "SHOW", "TRUE", "FALSE",
        "VAR", "INTEGER", "CONST",
        "EQ", "EQEQ", "GT", "LT",
        "ADD", "SUB", "MUL", "DIV",
        "LPAREN", "RPAREN", "SEMICOLON", "WHITESPACE"
    }
    assert tokens_esperados == tokens_presentes, (
        f"Faltando: {tokens_esperados - tokens_presentes}\n"
        f"Extras:   {tokens_presentes - tokens_esperados}"
    )
    print("  [OK] NFA combinado com todos os tokens da LangC")


def run_tests():
    print("\nExecutando testes do Algoritmo de Thompson...")
    _test_nfa_symbol()
    _test_nfa_string()
    _test_nfa_union()
    _test_nfa_star()
    _test_nfa_plus()
    _test_combined_nfa()
    print("\nTodos os testes passaram!\n")


# ---------------------------------------------------------------------------
# Execução direta
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_tests()

    print("Construindo NFA combinado para a LangC...\n")
    nfa = build_langc_nfa()
    print_summary(nfa)

    # Exibe detalhes do NFA de um token específico para demonstração
    _reset_counter()
    token_nfas = build_all_token_nfas()

    print("Detalhes do NFA para o token NUM ('num'):")
    print_nfa(token_nfas[0][1], title="NFA: NUM")

    print("Detalhes do NFA para o token INTEGER ([0-9]+):")
    print_nfa(token_nfas[7][1], title="NFA: INTEGER")
