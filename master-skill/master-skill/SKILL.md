---
name: master-skill
description: >
  Orquestrador mestre de frameworks e skills de desenvolvimento com IA.
  ATIVE ESTE SKILL EXCLUSIVAMENTE quando o usuário chamar o comando /master-skill.
  NÃO ative em nenhuma outra situação — este skill responde APENAS ao comando explícito /master-skill.

  Quando ativado, interpreta a instrução fornecida após o comando e executa:
  - Inicialização via `/master-skill init`
  - Instalação de frameworks de IA no projeto atual: BMad Method, Spec-Kit, Antigravity Kit
  - Busca e instalação de skills de uma pasta externa no projeto atual

  Exemplos de ativação (SOMENTE via /master-skill):
  - /master-skill init
  - /master-skill instale o BMad
  - /master-skill instale o Antigravity Kit
  - /master-skill configure o Spec-Kit nesse projeto
  - /master-skill quero a skill de brainstorm
  - /master-skill instale a skill de code-review
  - /master-skill liste as skills disponíveis
---

# Master Skill — Orquestrador de Frameworks e Skills

> **Contexto importante:** Esta skill é instalada **globalmente** na pasta do agente de IA que o usuário configurou.
> Cada agente tem sua própria pasta global de skills:
>
> | Agente | Pasta global |
> |--------|--------------|
> | Antigravity | `C:\Users\<usuario>\.gemini\antigravity\skills\` |
> | Claude Code | `C:\Users\<usuario>\.claude\skills\` |
> | Codex CLI | `C:\Users\<usuario>\.agents\skills\` |
> | Cursor | `C:\Users\<usuario>\.cursor\skills\` |
> | Windsurf | `C:\Users\<usuario>\.windsurf\skills\` |
> | GitHub Copilot | `C:\Users\<usuario>\.github\skills\` |
>
> O arquivo `settings.json` é salvo dentro da pasta desta skill **no agente escolhido durante o `/master-skill init`**.
> Exemplo (Antigravity): `C:\Users\<usuario>\.gemini\antigravity\skills\master-skill\config\settings.json`
> Exemplo (Claude Code): `C:\Users\<usuario>\.claude\skills\master-skill\config\settings.json`

Você foi ativado via `/master-skill`. Antes de qualquer ação, siga o fluxo abaixo.

---

## Passo 0 — Verificar se é o comando `init`

Se a instrução após `/master-skill` for **`init`** (ou variações como "inicializar", "iniciar", "setup inicial", "primeira configuração"), execute o **Fluxo de Inicialização** abaixo.

Para qualquer outra instrução, pule direto para o **Passo 1 — Carregar Configuração**.

---

### Fluxo de Inicialização (`/master-skill init`)

Este comando configura o Master Skill pela primeira vez (ou reconfigura). Ele deve ser executado uma única vez por agente e os dados ficam salvos globalmente.

#### Etapa 1 — Solicitar o agente

Apresente esta mensagem ao usuário:

> 🚀 **Inicialização do Master Skill**
>
> Vamos configurar seu ambiente. Qual agente de IA você está usando?
>
> | # | Agente | Pasta global de skills |
> |---|--------|----------------------|
> | 1 | Antigravity (Gemini) | `C:\Users\<usuario>\.gemini\antigravity\skills\` |
> | 2 | Claude Code | `C:\Users\<usuario>\.claude\skills\` |
> | 3 | Codex CLI | `C:\Users\<usuario>\.agents\skills\` |
> | 4 | Cursor | `C:\Users\<usuario>\.cursor\skills\` |
> | 5 | Windsurf | `C:\Users\<usuario>\.windsurf\skills\` |
> | 6 | GitHub Copilot | `C:\Users\<usuario>\.github\skills\` |
>
> Informe o número ou o nome do agente.

Mapeie a resposta para:

| Agente | Pasta global de skills |
|--------|----------------------|
| Antigravity / Gemini | `C:\Users\<usuario>\.gemini\antigravity\skills\` |
| Claude Code | `C:\Users\<usuario>\.claude\skills\` |
| Codex CLI | `C:\Users\<usuario>\.agents\skills\` |
| Cursor | `C:\Users\<usuario>\.cursor\skills\` |
| Windsurf | `C:\Users\<usuario>\.windsurf\skills\` |
| GitHub Copilot | `C:\Users\<usuario>\.github\skills\` |

#### Etapa 2 — Solicitar a pasta de skills externas

> 📁 **Pasta de Skills Externas**
>
> Informe o caminho completo da pasta onde suas skills customizadas estão armazenadas.
> Exemplo: `F:\SKILLS` ou `C:\Users\sande\MeusProjetos\Skills`

Aguarde a resposta do usuário e:
1. Verifique se a pasta existe no sistema de arquivos
2. Se não existir, informe o erro e peça um novo caminho

#### Etapa 3 — Salvar `settings.json` na pasta global desta skill

O arquivo de configuração é salvo **ao lado deste SKILL.md**, na pasta global da skill do agente informado:

```
C:\Users\<usuario>\.<pasta-do-agente>\skills\master-skill\config\settings.json
```

Exemplos concretos:
- Antigravity → `C:\Users\<usuario>\.gemini\antigravity\skills\master-skill\config\settings.json`
- Claude Code  → `C:\Users\<usuario>\.claude\skills\master-skill\config\settings.json`
- Codex CLI    → `C:\Users\<usuario>\.agents\skills\master-skill\config\settings.json`

Conteúdo do arquivo:

```json
{
  "agent": "<nome-do-agente>",
  "agent_global_skills_folder": "<pasta-global-de-skills-do-agente>",
  "skills_folder": "<caminho-informado-pelo-usuario>"
}
```

```powershell
# Criar a estrutura de pastas se não existir
$configPath = "<pasta-global-do-agente>\master-skill\config"
New-Item -ItemType Directory -Force -Path $configPath

# Salvar o arquivo de configuração
$config = [ordered]@{
  agent = "<nome-do-agente>"
  agent_global_skills_folder = "<pasta-global-de-skills-do-agente>"
  skills_folder = "<caminho-informado-pelo-usuario>"
} | ConvertTo-Json
Set-Content -Path "$configPath\settings.json" -Value $config -Encoding UTF8
```

#### Etapa 4 — Confirmar e concluir

> ✅ **Master Skill inicializado com sucesso!**
>
> - **Agente:** `<nome-do-agente>`
> - **Pasta global da skill:** `<pasta-global-do-agente>\master-skill\`
> - **Pasta de skills externas:** `<caminho-informado>`
> - **Configuração salva em:** `<pasta-global-do-agente>\master-skill\config\settings.json`
>
> Agora você pode usar `/master-skill` normalmente. Exemplo:
> `/master-skill quero a skill de brainstorm`

---

## Passo 1 — Carregar Configuração (para qualquer instrução que não seja `init`)

O `settings.json` fica **na pasta global da skill, dentro do agente que o usuário escolheu no `/master-skill init`**.

O caminho segue sempre o padrão:

```
C:\Users\<usuario>\.<pasta-do-agente>\skills\master-skill\config\settings.json
```

A pasta do agente varia conforme o agente escolhido:

| Agente | Caminho do settings.json |
|--------|--------------------------|
| Antigravity | `C:\Users\<usuario>\.gemini\antigravity\skills\master-skill\config\settings.json` |
| Claude Code | `C:\Users\<usuario>\.claude\skills\master-skill\config\settings.json` |
| Codex CLI | `C:\Users\<usuario>\.agents\skills\master-skill\config\settings.json` |
| Cursor | `C:\Users\<usuario>\.cursor\skills\master-skill\config\settings.json` |
| Windsurf | `C:\Users\<usuario>\.windsurf\skills\master-skill\config\settings.json` |
| GitHub Copilot | `C:\Users\<usuario>\.github\skills\master-skill\config\settings.json` |

Se o `settings.json` ainda não existir em nenhum desses locais, significa que o `/master-skill init` ainda não foi executado.

### Caso A — `settings.json` não existe ou está vazio

Apresente:

> ⚠️ **Configuração não encontrada.**
>
> Execute `/master-skill init` para configurar o ambiente antes de continuar.

Interrompa a execução e aguarde o usuário executar `/master-skill init`.

### Caso B — `settings.json` encontrado

Leia os campos:
- `agent` — nome do agente configurado
- `agent_global_skills_folder` — pasta global de skills do agente
- `skills_folder` — caminho da pasta de skills externas

Use esses valores em todas as operações a seguir.

---

## Passo 2 — Identificar a Intenção

Leia a instrução após `/master-skill` e classifique:

| Categoria | Quando usar | Exemplos |
|-----------|-------------|---------|
| **A — Framework** | Menciona BMad, BMAD, Spec-Kit, SpecKit, Antigravity, antigravity-kit | "instale o BMad", "quero o Spec-Kit", "setup do Antigravity Kit" |
| **B — Skill Externa** | Menciona "skill de X", "quero a skill X", "instale a skill X", "liste skills" | "quero a skill de brainstorm", "instale code-review", "liste as skills" |
| **C — Reconfigurar** | Menciona "mudar pasta", "trocar agente", "reconfigurar", "nova pasta de skills" | "muda a pasta de skills", "reconfigurar", "mudar agente" |

Se a intenção for ambígua, pergunte ao usuário antes de prosseguir.

---

## A — Instalação de Frameworks

Antes de instalar, confirme:
1. Qual é o diretório do projeto atual? (peça ao usuário ou verifique o contexto)
2. O framework solicitado já está instalado? (verifique os arquivos do projeto)

Leia o arquivo de referência correspondente para instruções detalhadas:

- **BMad Method** → `references/bmad.md`
- **Spec-Kit (GitHub)** → `references/speckit.md`
- **Antigravity Kit** → `references/antigravity.md`

Após a leitura, execute a instalação conforme as instruções do arquivo de referência.

---

## B — Skills Externas

Use o valor de `skills_folder` do `settings.json` em todos os comandos abaixo.

### Listar skills disponíveis

```powershell
Get-ChildItem -Path "<skills_folder>" -Filter "SKILL.md" -Recurse | Select-Object FullName
```

Para cada resultado, leia o campo `name` e `description` do frontmatter YAML e apresente ao usuário de forma organizada.

### Buscar uma skill por intenção

1. Execute a busca recursiva acima
2. Para cada candidato relevante, leia o `description` do SKILL.md para confirmar a relevância
3. Se encontrar múltiplas opções, apresente ao usuário e peça para escolher
4. Se não encontrar nenhuma, informe o usuário

### Instalar uma skill no projeto atual

#### Passo 1 — Detectar o agente do projeto

Verifique quais pastas de configuração existem na **raiz do projeto atual**:

| Pasta encontrada | Agente | Destino da skill |
|-----------------|--------|-----------------|
| `.claude/` | Claude Code | `.claude/skills/<skill-nome>/` |
| `.agent/` | Antigravity | `.agent/skills/<skill-nome>/` |
| `.gemini/` | Gemini CLI | `.gemini/skills/<skill-nome>/` |
| `.agents/` | Codex CLI | `.agents/skills/<skill-nome>/` |
| `.cursor/` | Cursor | `.cursor/skills/<skill-nome>/` |
| `.windsurf/` | Windsurf | `.windsurf/skills/<skill-nome>/` |
| `.github/` | GitHub Copilot | `.github/skills/<skill-nome>/` |

Se mais de um agente for detectado, pergunte ao usuário para qual deseja instalar.
Se nenhuma pasta for encontrada, pergunte ao usuário qual agente está usando no projeto.

#### Passo 2 — Copiar a skill preservando subpastas

Calcule o caminho relativo da skill dentro de `skills_folder`:

```
F:\SKILLS\dev\brainstorm\  →  <projeto>\<pasta-agente>\skills\dev\brainstorm\
F:\SKILLS\brainstorm\      →  <projeto>\<pasta-agente>\skills\brainstorm\
```

```powershell
$skillRelPath = "<caminho-relativo-da-skill>"
$destino = "<projeto>\<pasta-agente-do-projeto>\skills\$skillRelPath"
New-Item -ItemType Directory -Force -Path $destino
Copy-Item -Recurse "<skills_folder>\$skillRelPath\*" $destino
```

Após copiar:
- Confirme o sucesso listando a pasta de destino
- Informe ao usuário como chamar a skill recém-instalada

---

## C — Reconfigurar

Quando o usuário quiser mudar a pasta de skills ou o agente:

1. Pergunte o que deseja alterar (pasta de skills, agente, ou ambos)
2. Colete os novos valores
3. Verifique se os caminhos existem
4. Atualize o `settings.json` no mesmo local onde foi encontrado no Passo 1
5. Confirme: _"✅ Configuração atualizada com sucesso."_

---

## Fluxo Completo

```
/master-skill init
       ↓
Solicitar agente → Solicitar pasta de skills externas
       ↓
Salvar settings.json em: <pasta-global-do-agente>/skills/master-skill/config/settings.json
       ↓
Confirmar ✅

/master-skill <instrução>
       ↓
[Passo 1] Ler settings.json ao lado deste SKILL.md (pasta global do agente)
       ↓
  Não encontrado? ──→ Orientar para /master-skill init
       ↓
[Passo 2] Identificar intenção
       ↓
  [A - Framework] ────→ Ler references/<framework>.md → Instalar → Confirmar
  [B - Skill]     ────→ Buscar em skills_folder → Detectar agente do projeto → Copiar → Confirmar
  [C - Reconfig]  ────→ Coletar novos valores → Atualizar settings.json → Confirmar
```

---

## Notas importantes

- **Esta skill é global** — instalada na pasta do agente, não em projetos
- **O `settings.json` fica sempre ao lado deste SKILL.md**, na instalação global do agente
- **Nunca sobrescreva** arquivos ou pastas existentes sem confirmação explícita do usuário
- **Confirme sempre o diretório do projeto** antes de instalar qualquer coisa
- Para frameworks que precisam de `npx`, `uvx` ou `pip`, verifique se a ferramenta está disponível
- Após qualquer instalação bem-sucedida, informe os **próximos passos** ao usuário
