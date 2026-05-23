# LangC Lexer 

## Visão Geral

Este projeto implementa o **analisador léxico da linguagem LangC** seguindo o pipeline clássico de compiladores:

```text
Expressões Regulares (ER)
        ↓
Autômato Finito Não Determinístico (NFA)
        ↓
Autômato Finito Determinístico (DFA)
        ↓
Analisador Léxico (Lexer)
```

O objetivo é reconhecer os tokens da linguagem LangC a partir de um código-fonte de entrada e produzir uma sequência de tokens válida.

A implementação será feita em Python.

---

# Objetivos do Trabalho

O analisador léxico deve:

* Definir tokens usando Expressões Regulares
* Construir NFAs usando o algoritmo de Thompson
* Converter NFAs em DFAs usando subset construction
* Implementar o lexer usando o DFA resultante
* Aplicar:

  * regra do maior casamento (maximal munch)
  * prioridade de tokens
* Detectar erros léxicos
* Produzir a saída esperada pelo trabalho

---

# Estrutura do Projeto

```text
langc_lexer/
│
├── README.md
├── main.py
├── tokens.py
├── er_to_nfa.py
├── nfa_to_dfa.py
├── lexer.py
├── automata/
│   ├── nfa.py
│   └── dfa.py
│
├── examples/
│   ├── valid.lang
│   └── invalid.lang
│
└── tokens.txt
```

---

# Etapas do Projeto

# 1. Definir os Tokens

Arquivo: `tokens.py`

Responsável por declarar:

* nome do token
* expressão regular
* prioridade

## Tokens da LangC

| Token      | ER                            |
| ---------- | ----------------------------- |
| NUM        | `num`                         |
| TEXT       | `text`                        |
| BOOL       | `bool`                        |
| SHOW       | `show`                        |
| TRUE       | `true`                        |
| FALSE      | `false`                       |
| VAR        | `[a-zA-Z_][a-zA-Z0-9_]{0,29}` |
| INTEGER    | `[0-9]+`                      |
| CONST      | `"[^"]*"`                     |
| EQEQ       | `==`                          |
| EQ         | `=`                           |
| GT         | `>`                           |
| LT         | `<`                           |
| ADD        | `+`                           |
| SUB        | `-`                           |
| MUL        | `*`                           |
| DIV        | `/`                           |
| LPAREN     | `(`                           |
| RPAREN     | `)`                           |
| SEMICOLON  | `;`                           |
| WHITESPACE | `[ \t\n]+`                    |

## Observações

### Prioridade

Palavras reservadas devem vir antes de `VAR`.

Exemplo:

```python
TOKENS = [
    ("NUM", "num"),
    ("TEXT", "text"),
    ...
    ("VAR", "[a-zA-Z_][a-zA-Z0-9_]{0,29}")
]
```

Assim:

```text
num
```

vira:

```text
NUM
```

e não:

```text
VAR
```

---

### Maior casamento

`==` deve ser reconhecido antes de `=`.

Logo:

```python
("EQEQ", "=="),
("EQ", "=")
```

---

### Identificadores

`VAR` possui limite máximo de 30 caracteres.

Caso ultrapasse:

```text
ERRO LÉXICO
```

---

# 2. Construção do NFA (ER → NFA)

Arquivo: `er_to_nfa.py`

Implementar o algoritmo de Thompson.

## Operações Necessárias

### Símbolo simples

```text
a
```

### Concatenação

```text
ab
```

### União

```text
a|b
```

### Fecho de Kleene

```text
a*
```

### Um ou mais

```text
a+
```

### Classes de caracteres

```text
[a-z]
[0-9]
```

---

## Estrutura sugerida do NFA

```python
nfa = {
    "states": set(),
    "alphabet": set(),
    "transitions": {},
    "epsilon": {},
    "start": 0,
    "accept": {}
}
```

---

## Estratégia

Cada token gera um NFA individual.

Depois todos são unidos:

```text
          ε
START --------> NFA_NUM

          ε
START --------> NFA_VAR

          ε
START --------> NFA_INTEGER
```

---

# 3. Conversão NFA → DFA

Arquivo: `nfa_to_dfa.py`

Implementar:

* epsilon closure
* move
* subset construction

---

## Funções necessárias

### epsilon_closure

```python
epsilon_closure(nfa, states)
```

Retorna todos os estados alcançáveis via ε.

---

### move

```python
move(states, symbol)
```

Retorna os estados alcançáveis consumindo um símbolo.

---

### subset construction

```python
nfa_to_dfa(nfa)
```

Transforma conjuntos de estados NFA em estados DFA.

---

## Estrutura sugerida do DFA

```python
dfa = {
    "states": set(),
    "alphabet": set(),
    "transitions": {},
    "start": 0,
    "accept": {}
}
```

---

# 4. Implementar o Lexer

Arquivo: `lexer.py`

O lexer utiliza o DFA para consumir o código-fonte.

---

## Algoritmo principal

Para cada posição da entrada:

1. começa no estado inicial
2. tenta consumir o máximo possível
3. guarda o último estado final válido
4. produz o token correspondente

---

## Regra do Maior Casamento

Exemplo:

```text
==
```

O lexer:

* lê `=`
* percebe que ainda pode continuar
* lê outro `=`
* produz `EQEQ`

---

## Tratamento de espaços

`WHITESPACE` deve ser reconhecido mas descartado.

---

## Tratamento de erros

Caso nenhum token seja válido:

```text
ERRO LÉXICO
```

Exemplo:

```text
@
```

---

# 5. Arquivo Principal

Arquivo: `main.py`

Responsável por:

* carregar tokens
* gerar NFA
* converter para DFA
* executar lexer
* imprimir saída

---

# Entrada e Saída

## Entrada

Arquivo `.lang`:

```text
num x = 10;
show(x);
```

---

## Saída esperada

```text
NUM
VAR
EQ
INTEGER
SEMICOLON
SHOW
LPAREN
VAR
RPAREN
SEMICOLON
```

---

# tokens.txt

Arquivo exigido pelo trabalho.

Formato:

```text
TOKEN descrição
```

Exemplo:

```text
NUM palavra_reservada_num
TEXT palavra_reservada_text
BOOL palavra_reservada_bool
VAR identificador
INTEGER numero_inteiro
CONST string_literal
EQ atribuicao
EQEQ comparacao_igualdade
```

---

# Casos de Teste

## Caso válido

```text
num idade = 20;
show(idade);
```

---

## Saída

```text
NUM
VAR
EQ
INTEGER
SEMICOLON
SHOW
LPAREN
VAR
RPAREN
SEMICOLON
```

---

## Caso inválido

```text
num @idade = 10;
```

---

## Saída

```text
ERRO LÉXICO
```

---

# Divisão Recomendada da Equipe

## Pessoa 1

* tokens.py
* parser de ER

---

## Pessoa 2

* Thompson (ER → NFA)

---

## Pessoa 3

* subset construction (NFA → DFA)

---

## Pessoa 4

* lexer
* testes
* integração

---

# Melhor Estratégia de Implementação

## Ordem recomendada

### 1. Fazer lexer simplificado primeiro

Mesmo sem NFA/DFA completos.

Objetivo:

* validar tokens
* validar saídas
* testar regras

---

### 2. Implementar Thompson

Garantir que:

* concatenação funciona
* união funciona
* kleene funciona

---

### 3. Implementar subset construction

Testar:

* closures
* transições
* estados finais

---

### 4. Integrar tudo

Fluxo final:

```text
ER → NFA → DFA → TOKENIZAÇÃO
```

---

# Possíveis Dificuldades

## Classes de caracteres

```text
[a-zA-Z]
```

Podem ser expandidas internamente:

```python
{'a', 'b', ..., 'z', 'A', ..., 'Z'}
```

---

## Escape de caracteres

Strings:

```text
"abc"
```

Precisam parar corretamente no próximo `"`.

---

## Estados finais com prioridade

Um estado DFA pode conter vários estados finais do NFA.

Deve vencer:

1. maior casamento
2. token declarado primeiro

---

# Requisitos Teóricos Importantes

O projeto utiliza conceitos clássicos de compiladores:

* Expressões Regulares
* Autômatos Finitos
* Algoritmo de Thompson
* Fecho-ε
* Subset Construction
* DFA
* Reconhecimento léxico

As ERs são adequadas para análise léxica, enquanto gramáticas livres de contexto são usadas posteriormente na análise sintática.

---

# Execução

## Rodar o projeto

```bash
python main.py examples/valid.lang
```

---

# Resultado Esperado

O projeto final deve:

* construir autômatos corretamente
* reconhecer tokens da LangC
* respeitar prioridades
* detectar erros léxicos
* seguir o pipeline formal de compiladores
