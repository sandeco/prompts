"""
compress.py — Script principal da skill sandeco-token-reduce.

Comprime texto com LLMLingua-2 e opcionalmente envia ao Claude.
Auto-detecta GPU.

Requer inicializacao previa com setup.py.

Modos:
    So comprimir:       python compress.py --file texto.txt --rate 0.4
    Comprimir + salvar: python compress.py --file texto.txt --rate 0.4 --output comprimido.txt
    Comprimir + Claude: python compress.py --file texto.txt --rate 0.4 --ask "Resuma este texto"
    Saida JSON:         python compress.py --file texto.txt --rate 0.4 --json
"""

import argparse
import json as json_mod
import re
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).parent.parent
VENV_DIR = SKILL_DIR / ".venv"


# -- Verificacao de ambiente ---------------------------------------------------

def check_environment():
    """Verifica se o venv existe e se estamos rodando dentro dele."""
    venv_python = VENV_DIR / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = VENV_DIR / "bin" / "python"

    if not VENV_DIR.exists() or not venv_python.exists():
        print("ERRO: A skill ainda nao foi inicializada.", file=sys.stderr)
        print(f"Execute primeiro: python \"{SKILL_DIR / 'scripts' / 'setup.py'}\"",
              file=sys.stderr)
        sys.exit(1)

    if sys.prefix == sys.base_prefix:
        print(f"ERRO: Execute este script com o Python do venv:", file=sys.stderr)
        print(f"  \"{venv_python}\" \"{__file__}\" ...", file=sys.stderr)
        sys.exit(1)


# -- Compressor ----------------------------------------------------------------

def detect_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


MODEL_NAME = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
CHUNK_MAX_TOKENS = 400
COMPRESS_KWARGS = dict(
    force_tokens=[
        # Estruturais
        "\n", ".", ",", "?", "!", ":", ";",
        # Negacoes PT
        "não", "sem", "nenhum", "nunca", "nem", "nenhuma",
        # Prioridade / obrigatoriedade
        "Must", "must", "Obrigatória", "obrigatória",
        # Operacionais
        "npm", "run", "dev",
        # Resiliencia / fallback
        "retry", "fallback", "timeout", "WAL", "graciosamente",
        # Metricas
        "baseline", "target", "Baseline", "Target",
        # Delimitadores de codigo inline
        "`",
    ],
    force_reserve_digit=True,
    drop_consecutive=True,
)


def load_compressor():
    from llmlingua import PromptCompressor

    device = detect_device()
    print(f"Carregando LLMLingua-2 (device={device})...", file=sys.stderr)
    return PromptCompressor(
        model_name=MODEL_NAME,
        use_llmlingua2=True,
        device_map=device,
    )


def load_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(MODEL_NAME)


# -- Pre-processamento markdown ------------------------------------------------

def tables_to_keyvalue(text: str) -> str:
    """Converte tabelas markdown para formato key: value que sobrevive a compressao."""
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
    """Gruda prefixos de IDs aos digitos para que force_reserve_digit proteja o conjunto.
    Ex: G-01 -> G01, RF-01 -> RF01, EC-04 -> EC04"""
    return re.sub(r'\b(G|RF|RNF|NG|EC)-(\d+)', r'\1\2', text)


def strip_markdown(text: str) -> str:
    """Remove decoracao markdown mantendo o conteudo textual."""
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)       # separadores
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)                    # **bold** -> texto
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)      # ## headers -> texto
    text = re.sub(r'- \[[ x]\]\s*', '', text)                       # checkboxes
    text = re.sub(r'^```\w*\s*$', '', text, flags=re.MULTILINE)     # code fences (triple)
    text = re.sub(r'\n{3,}', '\n\n', text)                          # colapsar linhas vazias
    return text.strip()


# -- Chunking ------------------------------------------------------------------

def split_into_chunks(text: str, tokenizer, max_tokens: int = CHUNK_MAX_TOKENS) -> list[str]:
    """Divide texto em chunks de ate max_tokens, cortando em limites de linha."""
    lines = text.split('\n')
    chunks = []
    current_lines = []
    current_tokens = 0

    for line in lines:
        line_tokens = len(tokenizer.encode(line, add_special_tokens=False))
        if current_tokens + line_tokens > max_tokens and current_lines:
            chunks.append('\n'.join(current_lines))
            current_lines = []
            current_tokens = 0
        current_lines.append(line)
        current_tokens += line_tokens

    if current_lines:
        chunks.append('\n'.join(current_lines))

    return chunks


# -- Compressao ----------------------------------------------------------------

def compress(text: str, rate: float) -> dict:
    text = tables_to_keyvalue(text)
    text = normalize_identifiers(text)
    text = strip_markdown(text)
    compressor = load_compressor()
    tokenizer = load_tokenizer()

    chunks = split_into_chunks(text, tokenizer)

    if len(chunks) == 1:
        result = compressor.compress_prompt(text, rate=rate, **COMPRESS_KWARGS)
        return {
            "compressed_prompt": result["compressed_prompt"],
            "origin_tokens": result["origin_tokens"],
            "compressed_tokens": result["compressed_tokens"],
            "ratio": round(float(str(result["ratio"]).rstrip("x")), 2),
            "saving": result["origin_tokens"] - result["compressed_tokens"],
            "rate_requested": rate,
        }

    print(f"Texto dividido em {len(chunks)} chunks (max {CHUNK_MAX_TOKENS} tokens cada).",
          file=sys.stderr)

    compressed_parts = []
    total_origin = 0
    total_compressed = 0

    for i, chunk in enumerate(chunks, 1):
        r = compressor.compress_prompt(chunk, rate=rate, **COMPRESS_KWARGS)
        compressed_parts.append(r["compressed_prompt"])
        total_origin += r["origin_tokens"]
        total_compressed += r["compressed_tokens"]
        print(f"  Chunk {i}/{len(chunks)}: {r['origin_tokens']} -> {r['compressed_tokens']} tokens",
              file=sys.stderr)

    ratio = round(total_origin / total_compressed, 2) if total_compressed > 0 else 0.0

    return {
        "compressed_prompt": "\n".join(compressed_parts),
        "origin_tokens": total_origin,
        "compressed_tokens": total_compressed,
        "ratio": ratio,
        "saving": total_origin - total_compressed,
        "rate_requested": rate,
    }


# -- Claude --------------------------------------------------------------------

def ask_claude(compressed_text: str, question: str, model: str, max_tokens: int) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    prompt = f"""Contexto (comprimido via LLMLingua-2 — tokens irrelevantes foram removidos,
mas o significado foi preservado):

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
        description="Comprime tokens com LLMLingua-2 (Microsoft)"
    )
    # Entrada
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Texto a comprimir")
    group.add_argument("--file", help="Caminho para arquivo de texto")

    # Compressao
    p.add_argument("--rate", type=float, default=0.4,
                   help="Fracao de tokens a manter: 0.5=leve, 0.4=padrao, 0.2=agressivo")

    # Saida
    p.add_argument("--output", "-o", help="Salva texto comprimido neste arquivo")
    p.add_argument("--json", action="store_true",
                   help="Saida em JSON (util para integracao programatica)")

    # Claude (opcional)
    p.add_argument("--ask", help="Pergunta a enviar ao Claude com o contexto comprimido")
    p.add_argument("--model", default="claude-sonnet-4-6",
                   help="Modelo Claude (padrao: claude-sonnet-4-6)")
    p.add_argument("--max-tokens", type=int, default=4096,
                   help="Max tokens na resposta do Claude (padrao: 4096)")

    return p.parse_args()


def main():
    check_environment()

    args = parse_args()

    # Carregar texto
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"ERRO: arquivo nao encontrado: {path}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
    else:
        text = args.text

    if not text.strip():
        print("ERRO: texto vazio.", file=sys.stderr)
        sys.exit(1)

    # Comprimir
    result = compress(text, args.rate)

    # Salvar se pedido
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result["compressed_prompt"], encoding="utf-8")
        print(f"Salvo em: {out.resolve()}", file=sys.stderr)

    # Perguntar ao Claude se pedido
    claude_result = None
    if args.ask:
        claude_result = ask_claude(
            result["compressed_prompt"], args.ask, args.model, args.max_tokens
        )

    # Saida
    if args.json:
        output = {
            "compression": result,
        }
        if claude_result:
            output["claude"] = claude_result
        print(json_mod.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\nTokens originais:    {result['origin_tokens']}")
        print(f"Tokens comprimidos:  {result['compressed_tokens']}")
        print(f"Taxa de compressao:  {result['ratio']}x")
        print(f"Tokens economizados: {result['saving']}")

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
