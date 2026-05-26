"""
Analisador Léxico da LangC — Ponto de Entrada
Universidade Federal do Ceará - Compiladores 2025.1
Prof. Lucas Ismaily

Uso:
    # Lê de um arquivo .langc
    python main.py programa.langc

    # Lê do stdin (útil para testes rápidos no terminal)
    python main.py
    echo "num x = 5 ;" | python main.py

    # Lê de uma string direta (modo --inline)
    python main.py --inline "num x = 5 ;"

Saída:
    Uma linha por linha do programa fonte contendo os tipos dos tokens
    separados por espaço. Em caso de erro léxico, imprime ERRO.

Exemplo:
    Entrada (programa.langc):
        num a = 0 ;
        num b = 5 + a ;
        text c = "teSte" ;

    Saída:
        NUM VAR EQ INTEGER SEMICOLON
        NUM VAR EQ INTEGER ADD VAR SEMICOLON
        TEXT VAR EQ CONST SEMICOLON
"""

import sys
import os
from lexer import tokenizar, formatar_saida


# ---------------------------------------------------------------------------
# Funções de leitura
# ---------------------------------------------------------------------------

def ler_arquivo(caminho):
    """Lê o conteúdo de um arquivo de código-fonte LangC."""
    if not os.path.exists(caminho):
        print(f"ERRO: arquivo '{caminho}' não encontrado.", file=sys.stderr)
        sys.exit(1)

    extensao = os.path.splitext(caminho)[1].lower()
    if extensao not in (".langc", ".lc", ".txt", ""):
        print(
            f"Aviso: extensão '{extensao}' não é a padrão da LangC (.langc).",
            file=sys.stderr
        )

    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def ler_stdin():
    """Lê o código-fonte do stdin (entrada padrão)."""
    print("Aguardando entrada (Ctrl+D para finalizar):", file=sys.stderr)
    return sys.stdin.read()


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    # --inline "código aqui"
    if args and args[0] == "--inline":
        if len(args) < 2:
            print("ERRO: --inline requer uma string de código.", file=sys.stderr)
            sys.exit(1)
        source = args[1]

    # python main.py arquivo.langc
    elif args:
        source = ler_arquivo(args[0])

    # stdin
    else:
        source = ler_stdin()

    # Tokeniza e imprime resultado
    tokens = tokenizar(source)
    print(formatar_saida(tokens))


if __name__ == "__main__":
    main()
