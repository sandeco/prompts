"""
compress.py — Script principal da skill sandeco-token-reduce-ollama.

Comprime texto reescrevendo generativamente com um modelo Ollama local (default: qwen3:8b)
e opcionalmente envia ao Claude.

SELF-BOOTSTRAP: na primeira execucao detecta que o .venv nao existe, roda o setup.py
automaticamente, e re-executa a si mesmo com o Python do venv. O usuario final nao
precisa rodar setup manualmente — basta chamar este script.

Modos:
    So comprimir:       python compress.py --file texto.txt --rate 0.4
    Comprimir + salvar: python compress.py --file texto.txt --rate 0.4 --output comprimido.txt
    Comprimir + Claude: python compress.py --file texto.txt --rate 0.4 --ask "Resuma este texto"
    Saida JSON:         python compress.py --file texto.txt --rate 0.4 --json
    Trocar modelo:      python compress.py --file texto.txt --rate 0.4 --ollama-model qwen3:14b
"""

import argparse
import json as json_mod
import re
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).parent.parent
VENV_DIR = SKILL_DIR / ".venv"
SETUP_SCRIPT = SKILL_DIR / "scripts" / "setup.py"

DEFAULT_OLLAMA_MODEL = "qwen3:8b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


# -- Self-bootstrap ------------------------------------------------------------

def resolve_venv_python() -> Path:
    """Retorna o caminho esperado do Python do venv (Windows ou Unix)."""
    win = VENV_DIR / "Scripts" / "python.exe"
    if win.exists() or sys.platform == "win32":
        return win
    return VENV_DIR / "bin" / "python"


def ensure_initialized():
    """Configura a skill na primeira execucao e re-executa com o Python do venv.

    Fluxo:
    1. Se o venv nao existe, roda setup.py com o Python atual
    2. Se estamos rodando fora do venv, re-executa com o Python do venv
    3. Caso contrario, segue adiante (estamos dentro do venv)
    """
    venv_python = resolve_venv_python()

    if not VENV_DIR.exists() or not venv_python.exists():
        print("=" * 60, file=sys.stderr)
        print("  Primeira execucao detectada.", file=sys.stderr)
        print("  Configurando a skill automaticamente (so acontece uma vez).", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(file=sys.stderr)

        if not SETUP_SCRIPT.exists():
            print(f"ERRO: setup.py nao encontrado em {SETUP_SCRIPT}", file=sys.stderr)
            sys.exit(1)

        result = subprocess.run([sys.executable, str(SETUP_SCRIPT)])
        if result.returncode != 0:
            print("\nERRO: configuracao inicial falhou.", file=sys.stderr)
            sys.exit(result.returncode)

        venv_python = resolve_venv_python()
        if not venv_python.exists():
            print(f"ERRO: Python do venv nao encontrado apos setup em {venv_python}",
                  file=sys.stderr)
            sys.exit(1)

    # Se nao estamos rodando com o Python do venv, re-executa
    current = Path(sys.executable).resolve()
    target = venv_python.resolve()
    if current != target:
        result = subprocess.run([str(target), str(Path(__file__).resolve())] + sys.argv[1:])
        sys.exit(result.returncode)


# -- Verificacao Ollama --------------------------------------------------------

def ensure_ollama_ready(host: str, model: str):
    """Verifica que o daemon do Ollama esta rodando e o modelo esta presente."""
    from urllib.request import urlopen
    from urllib.error import URLError

    try:
        with urlopen(f"{host}/api/tags", timeout=3) as r:
            data = json_mod.loads(r.read())
    except URLError:
        print(f"ERRO: Ollama nao esta rodando em {host}.", file=sys.stderr)
        print("  Instale em https://ollama.com/download e execute 'ollama serve'.",
              file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERRO ao conectar ao Ollama em {host}: {e}", file=sys.stderr)
        sys.exit(1)

    installed = [m["name"] for m in data.get("models", [])]
    if model in installed or f"{model}:latest" in installed:
        return

    print(f"Modelo '{model}' nao encontrado localmente. Baixando via ollama pull...",
          file=sys.stderr)
    result = subprocess.run(["ollama", "pull", model])
    if result.returncode != 0:
        print(f"ERRO: falha ao baixar o modelo {model}.", file=sys.stderr)
        sys.exit(result.returncode)


# -- Extracao de PDF -----------------------------------------------------------

def extract_pdf_to_markdown(pdf_path: Path) -> tuple[str, Path, int]:
    """Extrai PDF para markdown (via pymupdf4llm), salva arquivo .md irmao.
    Retorna (texto_markdown, path_do_md, num_paginas).
    O .md e sempre salvo ao lado do PDF (doc.pdf -> doc.md)."""
    import pymupdf4llm
    import pymupdf

    with pymupdf.open(str(pdf_path)) as doc:
        n_pages = doc.page_count

    md_text = pymupdf4llm.to_markdown(str(pdf_path), show_progress=False)
    md_path = pdf_path.with_suffix(".md")
    md_path.write_text(md_text, encoding="utf-8")
    return md_text, md_path, n_pages


# -- Pre-processamento ---------------------------------------------------------

def tables_to_keyvalue(text: str) -> str:
    """Converte tabelas markdown em pares 'chave: valor' — LLMs reescrevem isso melhor."""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('|') and '|' in lines[i][1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            if len(table_lines) < 2:
                result.extend(table_lines)
                continue
            headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
            for tl in table_lines[1:]:
                if re.match(r'^\s*\|[-:\s|]+\|\s*$', tl):
                    continue
                values = [v.strip() for v in tl.split('|')[1:-1]]
                for h, v in zip(headers, values):
                    if v:
                        result.append(f"{h}: {v}")
                result.append('')
        else:
            result.append(lines[i])
            i += 1
    return '\n'.join(result)


def normalize_identifiers(text: str) -> str:
    """Remove hifens de IDs para o LLM tratar como token unico.
    Ex: G-01 -> G01, RF-01 -> RF01"""
    return re.sub(r'\b(G|RF|RNF|NG|EC)-(\d+)', r'\1\2', text)


def strip_markdown(text: str) -> str:
    """Remove decoracao markdown — o LLM ja produz texto natural, nao precisa desse ruido."""
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'- \[[ x]\]\s*', '', text)
    text = re.sub(r'^```\w*\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# -- Contagem de tokens --------------------------------------------------------

def count_tokens(text: str) -> int:
    """Usa tiktoken cl100k_base como estimativa consistente para comparacao."""
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


# -- Compressao via Ollama -----------------------------------------------------

COMPRESSION_SYSTEM = """Voce e um compressor de textos. Reescreva o texto do usuario de forma \
mais concisa, mantendo aproximadamente a proporcao solicitada do tamanho original.

REGRAS OBRIGATORIAS:
- Preserve TODAS as negacoes (nao, nunca, sem, nenhum, nem) — trocar uma negacao muda o significado
- Preserve TODOS os identificadores, codigos e numeros (ex: RF01, G05, 1000ms, URLs, IDs, valores)
- Preserve termos tecnicos especificos (nomes de bibliotecas, comandos, parametros, APIs)
- Preserve datas, versoes e unidades
- NAO adicione informacao que nao estava no original
- NAO adicione preambulo ("Aqui esta:", "Texto comprimido:", "Resumo:", etc.)
- NAO use markdown decorativo (negrito, italico, headers) a menos que ja existisse
- Escreva no mesmo idioma do original (se esta em portugues, responda em portugues)

Responda APENAS com o texto comprimido, nada mais."""


def build_user_message(text: str, rate: float) -> str:
    pct = int(round(rate * 100))
    return (
        f"Reescreva o texto abaixo mantendo aproximadamente {pct}% do tamanho original.\n\n"
        f"TEXTO ORIGINAL:\n{text}\n\n"
        f"/no_think"
    )


def strip_thinking_blocks(text: str) -> str:
    """Remove blocos <think>...</think> que alguns modelos (Qwen3) produzem."""
    text = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def compress_ollama(text: str, rate: float, model: str, host: str) -> dict:
    import ollama

    original_text = text
    pre = tables_to_keyvalue(text)
    pre = normalize_identifiers(pre)
    pre = strip_markdown(pre)

    print(f"Enviando ao Ollama ({model} em {host})...", file=sys.stderr)
    client = ollama.Client(host=host)

    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": COMPRESSION_SYSTEM},
            {"role": "user", "content": build_user_message(pre, rate)},
        ],
        options={"temperature": 0.2, "num_ctx": 8192},
    )

    compressed = response["message"]["content"]
    compressed = strip_thinking_blocks(compressed)

    origin_tokens = count_tokens(original_text)
    compressed_tokens = count_tokens(compressed)
    ratio = round(origin_tokens / compressed_tokens, 2) if compressed_tokens > 0 else 0.0

    return {
        "compressed_prompt": compressed,
        "origin_tokens": origin_tokens,
        "compressed_tokens": compressed_tokens,
        "ratio": ratio,
        "saving": origin_tokens - compressed_tokens,
        "rate_requested": rate,
        "model": model,
    }


# -- Claude --------------------------------------------------------------------

def ask_claude(compressed_text: str, question: str, model: str, max_tokens: int) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    prompt = f"""Contexto (comprimido generativamente via Ollama — texto reescrito de forma mais
concisa preservando o significado):

{compressed_text}

Pergunta: {question}"""

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = ""
    for block in response.content:
        if block.type == "text":
            answer += block.text

    return {
        "answer": answer,
        "model": model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


# -- CLI -----------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Comprime tokens via reescrita generativa com Ollama (auto-configura)"
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Texto a comprimir")
    group.add_argument("--file", help="Caminho para arquivo de texto")

    p.add_argument("--rate", type=float, default=0.4,
                   help="Fracao alvo de tokens: 0.5=leve, 0.4=padrao, 0.2=agressivo")

    p.add_argument("--output", "-o", help="Salva texto comprimido neste arquivo")
    p.add_argument("--json", action="store_true",
                   help="Saida em JSON (util para integracao programatica)")

    p.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL,
                   help=f"Modelo Ollama (padrao: {DEFAULT_OLLAMA_MODEL})")
    p.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST,
                   help=f"URL do daemon Ollama (padrao: {DEFAULT_OLLAMA_HOST})")

    p.add_argument("--ask", help="Pergunta a enviar ao Claude com o contexto comprimido")
    p.add_argument("--model", default="claude-sonnet-4-6",
                   help="Modelo Claude (padrao: claude-sonnet-4-6)")
    p.add_argument("--max-tokens", type=int, default=4096,
                   help="Max tokens na resposta do Claude (padrao: 4096)")

    return p.parse_args()


def main():
    # Bootstrap e re-exec ANTES de parse_args — setup.py nao precisa dos args
    ensure_initialized()

    args = parse_args()

    ensure_ollama_ready(args.ollama_host, args.ollama_model)

    pdf_info = None
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"ERRO: arquivo nao encontrado: {path}", file=sys.stderr)
            sys.exit(1)

        if path.suffix.lower() == ".pdf":
            print(f"Extraindo PDF para markdown: {path.name}", file=sys.stderr)
            text, md_path, n_pages = extract_pdf_to_markdown(path)
            pdf_info = {
                "source_pdf": str(path.resolve()),
                "pages": n_pages,
                "markdown_path": str(md_path.resolve()),
                "markdown_chars": len(text),
            }
            print(f"  {n_pages} paginas -> {len(text)} caracteres de markdown",
                  file=sys.stderr)
            print(f"  Markdown salvo em: {md_path.resolve()}", file=sys.stderr)
        else:
            text = path.read_text(encoding="utf-8")
    else:
        text = args.text

    if not text.strip():
        print("ERRO: texto vazio.", file=sys.stderr)
        sys.exit(1)

    result = compress_ollama(text, args.rate, args.ollama_model, args.ollama_host)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result["compressed_prompt"], encoding="utf-8")
        print(f"Salvo em: {out.resolve()}", file=sys.stderr)

    claude_result = None
    if args.ask:
        claude_result = ask_claude(
            result["compressed_prompt"], args.ask, args.model, args.max_tokens
        )

    if args.json:
        output = {"compression": result}
        if pdf_info:
            output["pdf"] = pdf_info
        if claude_result:
            output["claude"] = claude_result
        print(json_mod.dumps(output, ensure_ascii=False, indent=2))
    else:
        if pdf_info:
            print(f"\nPDF:                 {pdf_info['source_pdf']}")
            print(f"Paginas:             {pdf_info['pages']}")
            print(f"Markdown salvo em:   {pdf_info['markdown_path']}")
            print(f"Caracteres markdown: {pdf_info['markdown_chars']}")
        print(f"\nModelo Ollama:       {result['model']}")
        print(f"Tokens originais:    {result['origin_tokens']}")
        print(f"Tokens comprimidos:  {result['compressed_tokens']}")
        print(f"Taxa de compressao:  {result['ratio']}x")
        print(f"Tokens economizados: {result['saving']}")
        print(f"Taxa solicitada:     {result['rate_requested']}")

        if not args.output:
            print(f"\n--- Texto comprimido ---")
            print(result["compressed_prompt"])
            print("------------------------")

        if claude_result:
            print(f"\n--- Resposta do Claude ({args.model}) ---")
            print(claude_result["answer"])
            print(f"\nTokens Claude — input: {claude_result['input_tokens']}, "
                  f"output: {claude_result['output_tokens']}")


if __name__ == "__main__":
    main()
