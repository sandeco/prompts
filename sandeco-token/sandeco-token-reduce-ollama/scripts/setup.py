"""
setup.py — Inicializacao da skill sandeco-token-reduce-ollama.

Cria o .venv, instala dependencias Python, verifica o daemon do Ollama e puxa o modelo
default qwen3:8b.

Uso:
    python setup.py
"""

import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

SKILL_DIR = Path(__file__).parent.parent
VENV_DIR = SKILL_DIR / ".venv"
PACKAGES = ["ollama", "anthropic", "tiktoken", "pymupdf4llm"]
DEFAULT_MODEL = "qwen3:8b"
OLLAMA_HOST = "http://localhost:11434"


def venv_python():
    """Retorna o caminho do Python dentro do .venv (Windows e Unix)."""
    win = VENV_DIR / "Scripts" / "python.exe"
    unix = VENV_DIR / "bin" / "python"
    return win if win.exists() else unix


def run(cmd, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"\nERRO: comando falhou com codigo {result.returncode}")
        sys.exit(result.returncode)


def check_ollama_running() -> bool:
    """Tenta alcancar o daemon do Ollama."""
    try:
        with urlopen(f"{OLLAMA_HOST}/api/tags", timeout=3) as r:
            return r.status == 200
    except URLError:
        return False
    except Exception:
        return False


def ollama_has_model(model: str) -> bool:
    """Verifica se o modelo ja foi baixado."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return False
        return model in result.stdout
    except Exception:
        return False


def print_done(python, skipped_model=False):
    print("=" * 60)
    print("  Inicializacao concluida!")
    print("=" * 60)
    print(f"\n  Python do venv: {python}")
    if skipped_model:
        print("\n  ATENCAO: o modelo Ollama nao foi baixado porque o daemon nao esta ativo.")
        print(f"  Apos subir o Ollama ('ollama serve'), rode: ollama pull {DEFAULT_MODEL}")
    else:
        print(f"\n  Skill pronta. Modelo default: {DEFAULT_MODEL}")
        print(f"  Peca ao Claude para comprimir um texto!")
    print()


def main():
    print("=" * 60)
    print("  sandeco-token-reduce-ollama — Inicializacao")
    print("=" * 60)
    print(f"\n  Skill dir: {SKILL_DIR}")
    print(f"  Venv dir:  {VENV_DIR}\n")

    # 1. Criar o venv
    if not VENV_DIR.exists():
        print("[1/5] Criando ambiente virtual (.venv)...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
        print("  OK\n")
    else:
        print("[1/5] .venv ja existe, pulando criacao.\n")

    python = venv_python()
    if not python.exists():
        print(f"ERRO: Python do venv nao encontrado em {python}")
        sys.exit(1)

    # 2. Atualizar pip
    print("[2/5] Atualizando pip...")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip", "-q"])
    print("  OK\n")

    # 3. Instalar pacotes Python
    print(f"[3/5] Instalando dependencias: {', '.join(PACKAGES)}")
    run([str(python), "-m", "pip", "install"] + PACKAGES + ["-q"])
    print("  OK\n")

    # 4. Verificar Ollama
    print("[4/5] Verificando daemon do Ollama...")
    if not check_ollama_running():
        print(f"  AVISO: Ollama nao esta acessivel em {OLLAMA_HOST}")
        print("  Instale em https://ollama.com/download e execute 'ollama serve'.")
        print("  (A skill NAO funciona sem o Ollama rodando.)")
        print("  Pulando download do modelo.\n")
        print_done(python, skipped_model=True)
        return
    print("  OK (Ollama ativo)\n")

    # 5. Baixar modelo
    print(f"[5/5] Verificando modelo {DEFAULT_MODEL}...")
    if ollama_has_model(DEFAULT_MODEL):
        print(f"  {DEFAULT_MODEL} ja esta presente.\n")
    else:
        print(f"  Baixando {DEFAULT_MODEL} (~5 GB na primeira vez — pode demorar)...")
        run(["ollama", "pull", DEFAULT_MODEL])
        print("  OK\n")

    print_done(python, skipped_model=False)


if __name__ == "__main__":
    main()
