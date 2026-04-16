---
name: sandeco-token-reduce-ollama
description: >
  Comprime tokens de prompts usando reescrita generativa com um modelo Ollama local (default: qwen3:8b)
  para reduzir custo e latencia ao enviar ao Claude. Aceita texto direto, arquivo .txt ou PDF como
  entrada: extrai o PDF para markdown (via pymupdf4llm), salva o .md ao lado do PDF e comprime o
  markdown. Use esta skill sempre que o usuario pedir para comprimir/reduzir/economizar tokens E
  mencionar Ollama, qwen, qwen3, llm local, modelo local, rodar localmente, "sem BERT", ou quiser
  compressao via LLM generativo em vez de classificador. Tambem use quando o usuario quiser
  pre-processar contexto localmente (incluindo PDFs) antes de enviar ao Claude usando Ollama.
  Triggers: "comprimir com ollama", "comprimir localmente", "ollama compress", "qwen3", "qwen",
  "reescrever com ollama", "resumir com llm local", "compressao generativa", "pdf com ollama",
  "ler pdf com ollama", "inicializar token-reduce-ollama", "init token-reduce-ollama".
---

# sandeco-token-reduce-ollama

Comprime texto reescrevendo generativamente com um modelo Ollama local. Diferente do LLMLingua-2
(que classifica token a token com BERT/XLM-RoBERTa), aqui um LLM generativo reescreve o texto de
forma mais concisa preservando o significado.

Default: **qwen3:8b** (5 GB, 40K de contexto, PT-BR forte).

## Diferencas para a skill `sandeco-token-reduce`

| Aspecto              | LLMLingua-2 (BERT)                  | Ollama (LLM generativo)              |
|----------------------|--------------------------------------|---------------------------------------|
| Como funciona        | Classifica/mantem tokens exatos     | Reescreve o texto                    |
| Palavras preservadas | Sim (palavras do original)          | Nao (pode parafrasear)               |
| Fluidez              | Menor (texto cortado)               | Maior (texto natural)                |
| Taxa exata           | Sim (controle fino via rate)        | Aproximada (LLM nem sempre obedece)  |
| Velocidade           | Muito rapida (CPU/GPU)              | Depende do hardware e do modelo      |
| Dependencia          | pip: llmlingua                      | Binario Ollama + pip: ollama         |

## Estrutura

```
sandeco-token-reduce-ollama/
├── SKILL.md          ← este arquivo
├── scripts/
│   ├── setup.py      ← inicializacao (cria .venv, instala libs, puxa modelo Ollama)
│   └── compress.py   ← compressao via Ollama (requer init)
└── .venv/            ← criado pelo setup.py (NAO distribuir)
```

## IMPORTANTE: Pre-requisito Ollama

Esta skill assume que o usuario ja tem o **Ollama instalado** (https://ollama.com/download) e
rodando (`ollama serve`). Esta e a unica instalacao manual exigida — o resto (venv, pacotes
Python, download do modelo) e automatico na primeira chamada.

Se o daemon do Ollama nao estiver ativo no momento da compressao, o `compress.py` aborta com
uma mensagem clara explicando como subir o Ollama.

## Auto-configuracao (self-bootstrap)

A skill se configura sozinha na primeira chamada de compressao. Voce nao precisa rodar
`setup.py` manualmente — basta invocar `compress.py` com o Python do sistema:

```bash
python "<skill-dir>/scripts/compress.py" --text "..." --rate 0.4
```

O que acontece na primeira execucao:
1. `compress.py` detecta que o `.venv` nao existe
2. Roda `setup.py` automaticamente (cria venv, instala pacotes, puxa o modelo)
3. Re-executa a si mesmo com o Python do venv
4. Faz a compressao

Nas chamadas seguintes, o passo 1-3 e pulado (venv ja existe).

### Quando o usuario pedir para "inicializar", "configurar" ou "init" a skill:

Voce pode rodar `setup.py` diretamente com `python "<skill-dir>/scripts/setup.py"` — util se
o aluno quer pre-baixar o modelo antes da primeira compressao (ex: rodando em casa com rede boa
antes de ir para a aula). O setup e idempotente.

## Como comprimir

**Sempre invoque `compress.py` com o Python do sistema** (nao com o do venv). O proprio script
faz o re-exec para o venv quando necessario:

```bash
python "<skill-dir>/scripts/compress.py" [opcoes]
```

Isso simplifica para alunos e compartilhamento: nao precisam saber onde esta o Python do venv.

### So comprimir (texto direto)

```bash
python "<skill-dir>/scripts/compress.py" --text "texto longo aqui" --rate 0.4
```

### Comprimir a partir de arquivo

```bash
python "<skill-dir>/scripts/compress.py" --file caminho/para/arquivo.txt --rate 0.4
```

### Comprimir um PDF (extrai para markdown primeiro)

```bash
python "<skill-dir>/scripts/compress.py" --file documento.pdf --rate 0.4
```

Quando o arquivo termina em `.pdf`, o script:
1. Extrai o PDF para markdown usando `pymupdf4llm` (headers, listas, tabelas, links)
2. Salva o markdown em `documento.md` ao lado do PDF (sempre — e o artefato intermediario)
3. Comprime o markdown com Ollama
4. Retorna as metricas de todas as etapas: paginas, caracteres do markdown, tokens originais, tokens comprimidos, razao

Se voce so quer o markdown sem comprimir muito, use `--rate 0.9`.

### Comprimir e salvar resultado em arquivo

```bash
python "<skill-dir>/scripts/compress.py" --file entrada.txt --rate 0.4 --output comprimido.txt
```

### Comprimir e enviar ao Claude com uma pergunta

```bash
python "<skill-dir>/scripts/compress.py" --file entrada.txt --rate 0.4 --ask "Resuma este texto"
```

### Trocar o modelo Ollama

```bash
python "<skill-dir>/scripts/compress.py" --file entrada.txt --rate 0.4 --ollama-model qwen3:14b
```

### Saida JSON (para consumo programatico)

```bash
python "<skill-dir>/scripts/compress.py" --file entrada.txt --rate 0.4 --json
```

## Parametros do compress.py

| Parametro         | Padrao             | Descricao                                              |
|-------------------|---------------------|--------------------------------------------------------|
| `--text`          | —                   | Texto passado diretamente (mutuamente exclusivo com --file) |
| `--file`          | —                   | Caminho para arquivo de texto                          |
| `--rate`          | `0.4`               | Fracao alvo de tokens (aproximada em compressao generativa) |
| `--output`        | —                   | Salva texto comprimido neste arquivo                   |
| `--json`          | `false`             | Saida em JSON estruturado                              |
| `--ollama-model`  | `qwen3:8b`          | Modelo Ollama a usar                                   |
| `--ollama-host`   | `http://localhost:11434` | URL do daemon Ollama                              |
| `--ask`           | —                   | Pergunta a enviar ao Claude com o contexto comprimido  |
| `--model`         | `claude-sonnet-4-6` | Modelo Claude (so usado com --ask)                     |
| `--max-tokens`    | `4096`              | Max tokens na resposta do Claude                       |

## Guia de taxas de compressao

- `0.5` — Compressao leve, maxima fidelidade
- `0.4` — Equilibrio padrao (recomendado)
- `0.33` — Compressao moderada
- `0.2` — Compressao agressiva (LLM pode nao atingir 20% — dependendo do texto, tende a
  parar em ~30% porque reescrever tao curto vira resumo extremo)

Quando o usuario nao especificar, use `0.4`.

**Importante:** compressao generativa via LLM e APROXIMADA. O modelo tenta atingir a taxa, mas
varia por texto. Sempre mostre a taxa efetiva atingida nas metricas.

## Formato da saida JSON

```json
{
  "compression": {
    "compressed_prompt": "texto comprimido...",
    "origin_tokens": 312,
    "compressed_tokens": 124,
    "ratio": 2.52,
    "saving": 188,
    "rate_requested": 0.4,
    "model": "qwen3:8b"
  },
  "pdf": {
    "source_pdf": "/caminho/para/doc.pdf",
    "pages": 12,
    "markdown_path": "/caminho/para/doc.md",
    "markdown_chars": 24580
  },
  "claude": {
    "answer": "resposta do Claude...",
    "model": "claude-sonnet-4-6",
    "input_tokens": 150,
    "output_tokens": 200
  }
}
```

O campo `pdf` so aparece quando a entrada e um arquivo `.pdf`.
O campo `claude` so aparece quando `--ask` e usado.

## Notas tecnicas

- Modelo default Ollama: `qwen3:8b` (trocavel via `--ollama-model`)
- Contagem de tokens: `tiktoken` com encoding `cl100k_base` (estimativa razoavel para comparacao)
- Qwen3 tem modo "thinking" ativo por padrao — a skill desabilita via `/no_think` no prompt e
  remove blocos `<think>...</think>` residuais na saida
- Temperatura baixa (`0.2`) para saida deterministica
- A variavel `ANTHROPIC_API_KEY` precisa estar definida no ambiente para usar `--ask`

### Pre-processamento automatico

Antes de enviar ao Ollama, o texto passa por:

- `tables_to_keyvalue()` — converte tabelas markdown em pares `chave: valor` (LLMs reescrevem
  tabelas melhor em formato linear; tabelas com `|---|` normalmente sao destruidas)
- `normalize_identifiers()` — remove hifens de IDs (`RF-01` → `RF01`) para o LLM tratar como um
  token unico e nao separar
- `strip_markdown()` — remove decoracao `**bold**`, headers `##`, code fences, checkboxes e
  separadores `---` (o LLM generativo ja produz texto natural, nao precisa desse ruido)

### Instrucoes ao modelo (system prompt)

O system prompt obriga o modelo a:
- Preservar TODAS as negacoes (`não`, `nunca`, `sem`, `nenhum`, `nem`) — trocar uma negacao muda
  o significado
- Preservar TODOS os identificadores, codigos e numeros (`RF-01`, `G05`, `1000ms`, URLs, IDs)
- Preservar termos tecnicos (nomes de bibliotecas, comandos, parametros)
- Nao adicionar informacao que nao estava no original
- Nao adicionar preambulo ("Aqui esta:", "Resumo:", etc.)
- Responder apenas com o texto comprimido

### Quando usar esta skill vs `sandeco-token-reduce`

- **LLMLingua-2 (skill original)**: quando a fidelidade de palavras e critica (auditoria,
  citacao, texto tecnico onde termos exatos importam) ou quando o usuario nao tem GPU
- **Ollama (esta skill)**: quando o usuario quer fluidez melhor, ja tem Ollama rodando, quer
  total privacidade (nada sai da maquina, nem para o HuggingFace), ou quer experimentar com
  modelos diferentes
