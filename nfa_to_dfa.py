"""
Algoritmo de Subconjuntos (Subset Construction): NFA → DFA
Universidade Federal do Ceará - Compiladores 2025.1
Linguagem: LangC

Como funciona (resumo):
  No NFA, ao consumir um caractere, o autômato pode estar em VÁRIOS
  estados ao mesmo tempo. A ideia do algoritmo é transformar cada
  conjunto de estados do NFA em UM único estado do DFA.

  Passos:
    1. Calcula o ε-closure do estado inicial do NFA → estado inicial do DFA.
    2. Para cada estado do DFA (conjunto de estados NFA) e cada símbolo
       do alfabeto, calcula para onde o conjunto vai (move + ε-closure).
    3. Cada conjunto que ainda não virou estado do DFA vira um novo estado.
    4. Repete até não restar conjuntos novos.
    5. Um estado do DFA é final se QUALQUER estado NFA do conjunto for final.
       Em caso de conflito (dois estados finais diferentes no mesmo conjunto),
       usa a REGRA DE PRIORIDADE: vence o token de menor índice na lista.

Estrutura do DFA produzido:
{
    "states":      conjunto de inteiros (IDs dos estados DFA),
    "alphabet":    conjunto de caracteres,
    "transitions": {estado_dfa: {char: estado_dfa_destino}},
    "start":       estado inicial (inteiro),
    "accept":      {estado_dfa: nome_do_token},
    "dead":        ID do estado morto (rejeita tudo) — pode ser None
}
"""

from er_to_nfa import build_langc_nfa


# ---------------------------------------------------------------------------
# Passo 1 — ε-closure
# ---------------------------------------------------------------------------

def epsilon_closure(nfa, states):
    """
    Retorna todos os estados NFA alcançáveis a partir de 'states'
    seguindo APENAS transições ε (sem consumir caractere).

    Usa busca em largura (BFS) iterativa para evitar recursão profunda.

    Exemplo:
        Se  ε(0) = {1},  ε(1) = {2, 3},  ε(3) = {4}
        epsilon_closure(nfa, {0}) = {0, 1, 2, 3, 4}
    """
    closure = set(states)          # começa com os próprios estados
    queue   = list(states)         # fila de estados a expandir

    while queue:
        s = queue.pop()
        for t in nfa["epsilon"].get(s, set()):
            if t not in closure:
                closure.add(t)
                queue.append(t)

    return frozenset(closure)      # frozenset → pode ser chave de dicionário


# ---------------------------------------------------------------------------
# Passo 2 — move (transições normais)
# ---------------------------------------------------------------------------

def move(nfa, states, char):
    """
    Retorna todos os estados NFA alcançáveis a partir de 'states'
    consumindo exatamente o caractere 'char' (sem ε).

    Equivale a:  ∪ { δ(s, char) | s ∈ states }
    """
    result = set()
    for s in states:
        result |= nfa["transitions"].get(s, {}).get(char, set())
    return result


# ---------------------------------------------------------------------------
# Passo 3 — DFA edge (move + ε-closure combinados)
# ---------------------------------------------------------------------------

def dfa_edge(nfa, dfa_state_set, char):
    """
    Dado um estado do DFA (representado como frozenset de estados NFA)
    e um caractere, retorna o próximo estado do DFA (também frozenset).

        DFAedge(d, c) = ε-closure( move(d, c) )

    Retorna frozenset vazio se não há transição válida.
    """
    moved = move(nfa, dfa_state_set, char)
    if not moved:
        return frozenset()         # estado morto
    return epsilon_closure(nfa, moved)


# ---------------------------------------------------------------------------
# Passo 4 — Determinar token de um estado final do DFA
# ---------------------------------------------------------------------------

def resolve_token(nfa, dfa_state_set):
    """
    Verifica se algum estado NFA em dfa_state_set é estado final.
    Se mais de um for final, aplica a REGRA DE PRIORIDADE:
    vence o token com menor índice na lista original de tokens
    (definida em er_to_nfa.py e armazenada em nfa["priority"]).

    Retorna o nome do token ou None se não for estado final.
    """
    best_token    = None
    best_priority = float("inf")

    for s in dfa_state_set:
        if s in nfa["accept"]:
            p = nfa["priority"].get(s, float("inf"))
            if p < best_priority:
                best_priority = p
                best_token    = nfa["accept"][s]

    return best_token


# ---------------------------------------------------------------------------
# Algoritmo principal — Subset Construction
# ---------------------------------------------------------------------------

def nfa_to_dfa(nfa):
    """
    Converte o NFA recebido em um DFA equivalente usando o
    Algoritmo de Subconjuntos (Subset Construction).

    Retorna um dicionário representando o DFA.
    """
    alphabet = nfa["alphabet"]

    # ------------------------------------------------------------------
    # Estado inicial do DFA = ε-closure do estado inicial do NFA
    # ------------------------------------------------------------------
    start_set = epsilon_closure(nfa, {nfa["start"]})

    # Mapeamento: frozenset de estados NFA → ID inteiro do estado DFA
    set_to_id = {start_set: 0}
    # Mapeamento inverso (para depuração): ID → frozenset
    id_to_set = {0: start_set}

    # Fila de conjuntos ainda não processados
    queue = [start_set]

    # Estruturas do DFA
    dfa_transitions = {}    # {id_dfa: {char: id_dfa_destino}}
    dfa_accept      = {}    # {id_dfa: nome_do_token}
    dead_state      = None  # ID do estado morto (se necessário)

    next_id = 1             # próximo ID disponível para estado DFA

    # ------------------------------------------------------------------
    # BFS: processa cada conjunto de estados NFA
    # ------------------------------------------------------------------
    while queue:
        current_set = queue.pop(0)
        current_id  = set_to_id[current_set]

        dfa_transitions[current_id] = {}

        # Verifica se este estado DFA é final
        token = resolve_token(nfa, current_set)
        if token is not None:
            dfa_accept[current_id] = token

        # Calcula transições para cada símbolo do alfabeto
        for char in alphabet:
            next_set = dfa_edge(nfa, current_set, char)

            if not next_set:
                # Transição leva ao estado morto (sem saída)
                continue

            # Se o conjunto ainda não tem ID, cria um novo estado DFA
            if next_set not in set_to_id:
                set_to_id[next_set] = next_id
                id_to_set[next_id]  = next_set
                next_id            += 1
                queue.append(next_set)

            dfa_transitions[current_id][char] = set_to_id[next_set]

    # ------------------------------------------------------------------
    # Estado morto: usado quando não há transição para um caractere.
    # Criado explicitamente para o analisador léxico poder detectar
    # quando nenhum token é reconhecível.
    # ------------------------------------------------------------------
    # (não adicionamos estado morto explícito — o analisador léxico
    #  trata ausência de transição como rejeição, o que é equivalente)

    return {
        "states":      set(range(next_id)),
        "alphabet":    alphabet,
        "transitions": dfa_transitions,
        "start":       0,
        "accept":      dfa_accept,
        "dead":        dead_state,
        # Mapeamento auxiliar para depuração
        "_id_to_nfa_set": id_to_set,
    }


# ---------------------------------------------------------------------------
# Utilitários de visualização
# ---------------------------------------------------------------------------

def print_dfa(dfa, title="DFA", max_rows=40):
    """Imprime o DFA de forma legível."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"  Estado inicial : {dfa['start']}")
    print(f"  Total de estados: {len(dfa['states'])}")
    print(f"  Estados finais  : {len(dfa['accept'])}")
    print(f"  Alfabeto        : {len(dfa['alphabet'])} símbolos")

    print(f"\n  Estados finais (token reconhecido):")
    for state, token in sorted(dfa["accept"].items()):
        print(f"    Estado {state:3d} → {token}")

    print(f"\n  Tabela de transições (primeiras {max_rows} linhas):")
    count = 0
    for state in sorted(dfa["transitions"]):
        for char, dest in sorted(dfa["transitions"][state].items()):
            if count >= max_rows:
                remaining = sum(
                    len(v) for v in dfa["transitions"].values()
                ) - max_rows
                print(f"    ... ({remaining} transições omitidas)")
                return
            marker = " ← FINAL" if state in dfa["accept"] else ""
            print(f"    δ({state:3d}, {repr(char):5s}) = {dest:3d}{marker}")
            count += 1
    print()


def print_dfa_summary(dfa):
    """Imprime apenas o resumo do DFA."""
    print(f"\n{'='*60}")
    print(f"  DFA - LangC")
    print(f"{'='*60}")
    print(f"  Estados totais  : {len(dfa['states'])}")
    print(f"  Estado inicial  : {dfa['start']}")
    print(f"  Estados finais  : {len(dfa['accept'])}")
    print(f"  Alfabeto        : {len(dfa['alphabet'])} símbolos")
    print(f"  Transições      : "
          f"{sum(len(v) for v in dfa['transitions'].values())}")

    print(f"\n  Tokens e seus estados no DFA:")
    # Agrupa por token
    token_map = {}
    for state, token in dfa["accept"].items():
        token_map.setdefault(token, []).append(state)
    for token, states in sorted(token_map.items()):
        print(f"    {token:12s} → estado(s) DFA: {sorted(states)}")
    print()


def print_dfa_table(dfa, chars=None):
    """
    Imprime a tabela de transições no formato tradicional de livro didático.
    Se 'chars' for None, usa um subconjunto representativo do alfabeto.
    """
    if chars is None:
        # Mostra apenas os chars mais relevantes para a LangC
        chars = sorted([
            'a', 'b', 'z', '0', '9',
            '=', '+', '-', '*', '/',
            '>', '<', '(', ')', ';',
            ' ', '"', '_',
        ])
        # Filtra apenas os que existem no alfabeto do DFA
        chars = [c for c in chars if c in dfa["alphabet"]]

    header = f"{'Estado':>8} |" + "".join(f" {repr(c):>6}" for c in chars) + " | Token"
    print(f"\n  Tabela de transições (colunas representativas):")
    print(f"  {header}")
    print(f"  {'-'*len(header)}")

    for state in sorted(dfa["states"])[:30]:  # primeiros 30 estados
        row = f"  {'→'+str(state) if state == dfa['start'] else str(state):>8} |"
        for c in chars:
            dest = dfa["transitions"].get(state, {}).get(c, "-")
            row += f" {str(dest):>6}"
        token = dfa["accept"].get(state, "")
        marker = " *" if token else ""
        row += f" | {token}{marker}"
        print(row)

    if len(dfa["states"]) > 30:
        print(f"  ... ({len(dfa['states']) - 30} estados omitidos)")
    print()


# ---------------------------------------------------------------------------
# Verificações de corretude
# ---------------------------------------------------------------------------

def verify_dfa(dfa):
    """
    Verifica propriedades básicas que todo DFA deve ter:
      1. Estado inicial existe.
      2. Toda transição aponta para estado válido.
      3. Cada estado tem no máximo 1 destino por símbolo (determinismo).
      4. Estados finais têm tokens válidos (strings não vazias).
    """
    errors = []

    if dfa["start"] not in dfa["states"]:
        errors.append("Estado inicial não está no conjunto de estados.")

    valid_tokens = {
        "NUM", "TEXT", "BOOL", "SHOW", "TRUE", "FALSE",
        "VAR", "INTEGER", "CONST",
        "EQ", "EQEQ", "GT", "LT",
        "ADD", "SUB", "MUL", "DIV",
        "LPAREN", "RPAREN", "SEMICOLON", "WHITESPACE"
    }

    for state, transitions in dfa["transitions"].items():
        if state not in dfa["states"]:
            errors.append(f"Estado {state} nas transições não existe.")
        for char, dest in transitions.items():
            if dest not in dfa["states"]:
                errors.append(
                    f"Transição δ({state}, {repr(char)}) = {dest}: "
                    f"destino não existe."
                )
            if not isinstance(dest, int):
                errors.append(
                    f"Transição δ({state}, {repr(char)}): "
                    f"destino deve ser inteiro (DFA), não conjunto."
                )

    for state, token in dfa["accept"].items():
        if state not in dfa["states"]:
            errors.append(f"Estado final {state} não existe.")
        if token not in valid_tokens:
            errors.append(
                f"Estado {state} tem token inválido: '{token}'."
            )

    return errors


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def _test_epsilon_closure():
    """Testa o ε-closure com um NFA simples."""
    nfa_mock = {
        "epsilon": {
            0: {1, 2},
            1: {3},
            3: {4},
        }
    }
    result = epsilon_closure(nfa_mock, {0})
    assert result == frozenset({0, 1, 2, 3, 4}), f"Esperado {{0,1,2,3,4}}, obtido {result}"
    print("  [OK] epsilon_closure: alcança todos os estados por ε")


def _test_move():
    """Testa o move com transições simples."""
    nfa_mock = {
        "transitions": {
            0: {"a": {1, 2}},
            1: {"a": {3}},
            2: {"b": {4}},
        }
    }
    result = move(nfa_mock, {0, 1}, "a")
    assert result == {1, 2, 3}, f"Esperado {{1,2,3}}, obtido {result}"
    print("  [OK] move: une os destinos de todos os estados do conjunto")


def _test_determinism():
    """Verifica que o DFA gerado é de fato determinístico."""
    from er_to_nfa import build_langc_nfa
    nfa = build_langc_nfa()
    dfa = nfa_to_dfa(nfa)

    for state, transitions in dfa["transitions"].items():
        for char, dest in transitions.items():
            assert isinstance(dest, int), (
                f"δ({state}, {repr(char)}) = {dest} não é inteiro — NFA, não DFA!"
            )
    print("  [OK] Determinismo: todas as transições apontam para um único estado")


def _test_all_tokens_present():
    """Verifica que todos os tokens da LangC aparecem no DFA."""
    from er_to_nfa import build_langc_nfa
    nfa = build_langc_nfa()
    dfa = nfa_to_dfa(nfa)

    esperados = {
        "NUM", "TEXT", "BOOL", "SHOW", "TRUE", "FALSE",
        "VAR", "INTEGER", "CONST",
        "EQ", "EQEQ", "GT", "LT",
        "ADD", "SUB", "MUL", "DIV",
        "LPAREN", "RPAREN", "SEMICOLON", "WHITESPACE"
    }
    presentes = set(dfa["accept"].values())
    faltando  = esperados - presentes
    assert not faltando, f"Tokens ausentes no DFA: {faltando}"
    print(f"  [OK] Todos os {len(esperados)} tokens estão presentes no DFA")


def _test_priority_eqeq_over_eq():
    """
    Verifica que '==' é reconhecido como EQEQ e não como dois EQ.
    O estado alcançado após ler '==' deve ser EQEQ.
    """
    from er_to_nfa import build_langc_nfa
    nfa = build_langc_nfa()
    dfa = nfa_to_dfa(nfa)

    # Simula leitura de '=' seguido de '='
    state = dfa["start"]
    for char in "==":
        state = dfa["transitions"].get(state, {}).get(char)
        assert state is not None, f"Sem transição para '{char}' no estado {state}"

    token = dfa["accept"].get(state)
    assert token == "EQEQ", (
        f"Após '==', esperado EQEQ, obtido '{token}'"
    )
    print("  [OK] Prioridade: '==' reconhecido como EQEQ (não como dois EQ)")


def _test_keyword_over_var():
    """
    Verifica que 'num', 'text', 'show', 'true', 'false', 'bool'
    são reconhecidos como palavras reservadas, não como VAR.
    """
    from er_to_nfa import build_langc_nfa
    nfa = build_langc_nfa()
    dfa = nfa_to_dfa(nfa)

    keywords = {
        "num": "NUM", "text": "TEXT", "bool": "BOOL",
        "show": "SHOW", "true": "TRUE", "false": "FALSE",
    }

    for word, expected_token in keywords.items():
        state = dfa["start"]
        for char in word:
            state = dfa["transitions"].get(state, {}).get(char)
            assert state is not None, (
                f"Sem transição para '{char}' lendo '{word}'"
            )
        token = dfa["accept"].get(state)
        assert token == expected_token, (
            f"'{word}': esperado {expected_token}, obtido '{token}'"
        )
    print("  [OK] Palavras reservadas reconhecidas corretamente (não como VAR)")


def _test_verify_dfa_no_errors():
    """Roda verify_dfa e garante que não há erros estruturais."""
    from er_to_nfa import build_langc_nfa
    nfa = build_langc_nfa()
    dfa = nfa_to_dfa(nfa)

    errors = verify_dfa(dfa)
    assert not errors, f"Erros estruturais no DFA:\n" + "\n".join(errors)
    print("  [OK] verify_dfa: sem erros estruturais")


def run_tests():
    print("\nExecutando testes do Algoritmo de Subconjuntos (NFA → DFA)...")
    _test_epsilon_closure()
    _test_move()
    _test_determinism()
    _test_all_tokens_present()
    _test_priority_eqeq_over_eq()
    _test_keyword_over_var()
    _test_verify_dfa_no_errors()
    print("\nTodos os testes passaram!\n")


# ---------------------------------------------------------------------------
# Execução direta
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_tests()

    print("Construindo DFA para a LangC...\n")
    nfa = build_langc_nfa()
    dfa = nfa_to_dfa(nfa)

    print_dfa_summary(dfa)
    print_dfa_table(dfa)
    print_dfa(dfa, title="DFA - LangC (primeiras transições)", max_rows=30)
