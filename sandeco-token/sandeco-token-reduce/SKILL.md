---
name: sandeco-token-reduce
description: >
  Comprime tokens de prompts usando LLMLingua-2 da Microsoft para reduzir custo e latencia.
  Use esta skill sempre que o usuario pedir para comprimir um prompt, reduzir tokens, economizar
  tokens, usar LLMLingua, ou quando um texto for longo demais para enviar a um LLM. Tambem use
  quando o usuario quiser pre-processar contexto antes de enviar ao Claude. Triggers: "comprimir",
  "reduzir tokens", "economizar tokens", "LLMLingua", "texto muito longo", "compressao de prompt",
  "token compression", "compress tokens", "inicializar compressao", "init token-reduce".
---

# sandeco-token-reduce

Comprime tokens removendo os menos relevantes de um texto, preservando o significado semantico.
Usa o modelo XLM-RoBERTa da Microsoft (LLMLingua-2) rodando localmente (CPU ou GPU).

## Estrutura

```
sandeco-token-reduce/
├── SKILL.md          ← este arquivo
├── scripts/
│   ├── setup.py      ← inicializacao (cria .venv, instala libs, baixa modelo)
│   └── compress.py   ← compressao de texto (requer init)
└── .venv/            ← criado pelo setup.py (NAO distribuir)
```

## IMPORTANTE: Fluxo de inicializacao

A skill precisa ser inicializada antes do primeiro uso. O `.venv` NAO e distribuido junto
com a skill — cada usuario precisa rodar o init uma vez.

### Antes de qualquer operacao de compressao:

1. Verifique se o `.venv` existe dentro do diretorio desta skill
2. Se NAO existir, informe ao usuario que a skill precisa ser inicializada e execute o setup:

```bash
python "<skill-dir>/scripts/setup.py"
```

O setup faz 4 coisas automaticamente:
- Cria o ambiente virtual `.venv`
- Atualiza o pip
- Instala `llmlingua` e `anthropic`
- Baixa o modelo LLMLingua-2 (~1 GB) do HuggingFace

Avise o usuario que a primeira execucao pode levar alguns minutos por causa do download do modelo.

3. Se o `.venv` JA existir, pule direto para a compressao.

### Quando o usuario pedir para "inicializar", "configurar" ou "init" a skill:

Execute o setup.py diretamente, mesmo que o .venv ja exista (ele e idempotente).

## Como comprimir

Depois de inicializado, use o script `compress.py` com o Python do venv.

O Python do venv esta em:
- Windows: `<skill-dir>/.venv/Scripts/python.exe`
- Unix: `<skill-dir>/.venv/bin/python`

### So comprimir (texto direto)

```bash
"<venv-python>" "<skill-dir>/scripts/compress.py" --text "texto longo aqui" --rate 0.4
```

### Comprimir a partir de arquivo

```bash
"<venv-python>" "<skill-dir>/scripts/compress.py" --file caminho/para/arquivo.txt --rate 0.4
```

### Comprimir e salvar resultado em arquivo

```bash
"<venv-python>" "<skill-dir>/scripts/compress.py" --file entrada.txt --rate 0.4 --output comprimido.txt
```

### Comprimir e enviar ao Claude com uma pergunta

```bash
"<venv-python>" "<skill-dir>/scripts/compress.py" --file entrada.txt --rate 0.4 --ask "Resuma este texto"
```

### Saida JSON (para consumo programatico)

```bash
"<venv-python>" "<skill-dir>/scripts/compress.py" --file entrada.txt --rate 0.4 --json
```

## Parametros do compress.py

| Parametro      | Padrao             | Descricao                                          |
|----------------|---------------------|----------------------------------------------------|
| `--text`       | —                   | Texto passado diretamente (mutuamente exclusivo com --file) |
| `--file`       | —                   | Caminho para arquivo de texto                      |
| `--rate`       | `0.4`               | Fracao de tokens a manter                          |
| `--output`     | —                   | Salva texto comprimido neste arquivo                |
| `--json`       | `false`             | Saida em JSON estruturado                          |
| `--ask`        | —                   | Pergunta a enviar ao Claude com o contexto comprimido |
| `--model`      | `claude-sonnet-4-6` | Modelo Claude (so usado com --ask)                 |
| `--max-tokens` | `4096`              | Max tokens na resposta do Claude                   |

## Guia de taxas de compressao

- `0.5` — Compressao leve, maxima fidelidade
- `0.4` — Equilibrio padrao (recomendado para a maioria dos casos)
- `0.33` — Compressao moderada
- `0.2` — Compressao agressiva para textos muito longos

Quando o usuario nao especificar uma taxa, use `0.4`.

## Formato da saida JSON

Quando `--json` e usado:

```json
{
  "compression": {
    "compressed_prompt": "texto comprimido...",
    "origin_tokens": 312,
    "compressed_tokens": 124,
    "ratio": 2.52,
    "saving": 188,
    "rate_requested": 0.4
  },
  "claude": {
    "answer": "resposta do Claude...",
    "model": "claude-sonnet-4-6",
    "input_tokens": 150,
    "output_tokens": 200
  }
}
```

O campo `claude` so aparece quando `--ask` e usado.

## Notas tecnicas

- Modelo HuggingFace: `microsoft/llmlingua-2-xlm-roberta-large-meetingbank`
- Cache do modelo: `~/.cache/huggingface/` (baixado uma vez pelo setup, reusado sempre)
- `force_tokens` preserva: `\n`, `.`, `,`, `?`, `!`, `:`, negacoes PT (`nao`, `sem`, `nenhum`, `nunca`, `nem`, `nenhuma`)
- `force_reserve_digit=True` protege qualquer token com digitos (IDs como RF-01, valores como 1000ms)
- GPU e detectada automaticamente se `torch` + CUDA estiver disponivel; caso contrario usa CPU
- A variavel `ANTHROPIC_API_KEY` precisa estar definida no ambiente para usar `--ask`

### Pre-processamento automatico

Antes de comprimir, o texto passa por `strip_markdown()` que remove:
- Separadores `---`
- Grid de tabelas `|---|---|`
- Marcadores `**bold**` (mantem texto)
- Prefixos `##` de headers (mantem texto)
- Checkboxes `- [ ]`
- Code fences ` ``` `
- Linhas vazias multiplas (colapsa para uma)

Isso reduz ~6% do texto antes de entrar no modelo, melhorando a qualidade da compressao.

### Chunking automatico

O modelo XLM-RoBERTa tem janela de 512 tokens. Para textos maiores, o script divide automaticamente em chunks de ate 400 tokens (cortando em limites de linha), comprime cada um separadamente e concatena os resultados. Isso elimina o scoring degradado que ocorria em tokens apos a posicao 512.
