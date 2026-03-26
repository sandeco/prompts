# Spec-Kit (GitHub) — Guia de Instalação

**O que é**: Toolkit open source da GitHub para Spec-Driven Development. Fornece uma estrutura onde specs são contratos executáveis que guiam IA na geração, testes e validação de código.

**Repositório oficial**: https://github.com/github/spec-kit

---

## Pré-requisitos

- Python 3.11+
- Git
- `uv` package manager

Para instalar `uv` caso não tenha:
```bash
pip install uv
# ou no Windows via PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Instalação

Substitua `vX.Y.Z` pela versão mais recente disponível em https://github.com/github/spec-kit/releases

```bash
# Inicializar em uma nova pasta
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <NOME_DO_PROJETO>

# Inicializar na pasta atual do projeto
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init .
```

### Para Google Antigravity (Gemini)

```bash
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init . --ai gemini
```

### Opções disponíveis

| Flag | Descrição |
|------|-----------|
| `--ai gemini` | Configura para Google Antigravity / Gemini CLI |
| `--ai claude` | Configura para Claude Code |
| `--ai copilot` | Configura para GitHub Copilot |
| `--script ps` | Scripts em PowerShell (padrão no Windows) |
| `--script sh` | Scripts em Bash/Shell |
| `--ignore-agent-tools` | Pula verificação de ferramentas |

---

## O que é criado

```
.agents/          → Configurações de agentes de IA e comandos slash
docs/             → Artefatos de especificação (constitution, specs, plans, tasks)
features/         → Documentação específica de features
.github/workflows → Automação CI/CD (opcional)
```

---

## Comandos principais após instalação

| Comando | O que faz |
|---------|-----------|
| `/speckit.constitution` | Define os princípios e diretrizes do projeto |
| `/speckit.specify` | Cria especificações de requisitos |
| `/speckit.plan` | Gera plano técnico de implementação |
| `/speckit.tasks` | Gera lista de tarefas a partir do plano |
| `/speckit.implement` | Executa a implementação das tarefas |
