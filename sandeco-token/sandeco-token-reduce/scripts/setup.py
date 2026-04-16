"""
setup.py — Inicializacao da skill sandeco-token-reduce.

Cria o .venv, instala dependencias e baixa o modelo LLMLingua-2.
Deve ser executado uma unica vez antes de usar a skill.

Uso:
    python setup.py
"""

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
VENV_DIR = SKILL_DIR / ".venv"
PACKAGES = ["llmlingua", "anthropic"]


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


def main():
    print("=" * 60)
    print("  sandeco-token-reduce — Inicializacao")
    print("=" * 60)
    print(f"\n  Skill dir: {SKILL_DIR}")
    print(f"  Venv dir:  {VENV_DIR}\n")

    # 1. Criar o venv
    if not VENV_DIR.exists():
        print("[1/4] Criando ambiente virtual (.venv)...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
        print("  OK\n")
    else:
        print("[1/4] .venv ja existe, pulando criacao.\n")

    python = venv_python()
    if not python.exists():
        print(f"ERRO: Python do venv nao encontrado em {python}")
        sys.exit(1)

    # 2. Atualizar pip
    print("[2/4] Atualizando pip...")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip", "-q"])
    print("  OK\n")

    # 3. Instalar pacotes
    print(f"[3/4] Instalando dependencias: {', '.join(PACKAGES)}")
    print("  (isso pode levar alguns minutos na primeira vez)")
    run([str(python), "-m", "pip", "install"] + PACKAGES + ["-q"])
    print("  OK\n")

    # 4. Baixar o modelo LLMLingua-2 (faz uma compressao minima para forcar o download)
    print("[4/4] Baixando modelo LLMLingua-2 (~1 GB na primeira vez)...")
    print("  (o modelo fica em cache em ~/.cache/huggingface/)")
    download_script = (
        "from llmlingua import PromptCompressor; "
        "c = PromptCompressor("
        "model_name='microsoft/llmlingua-2-xlm-roberta-large-meetingbank', "
        "use_llmlingua2=True, device_map='cpu'); "
        "r = c.compress_prompt('Hello world test.', rate=0.5); "
        "print('  Modelo carregado com sucesso!')"
    )
    run([str(python), "-c", download_script])
    print()

    # Resumo
    print("=" * 60)
    print("  Inicializacao concluida!")
    print("=" * 60)
    print(f"\n  Python do venv: {python}")
    print(f"\n  A skill esta pronta para uso.")
    print(f"  Peca ao Claude para comprimir um texto!")
    print()


if __name__ == "__main__":
    main()
