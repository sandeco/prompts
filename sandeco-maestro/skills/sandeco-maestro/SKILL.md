---
name: sandeco-maestro
description: 'Executa uma lista de skills em sequência ou em paralelo conforme a necessidade informada pelo usuário.'
argument-hint: 'lista de skills separadas por vírgula, ex: help, brainstorming'
---

# Skill: SandecoMaestro (Orquestração Multi-Agente)

Esta habilidade permite ao Antigravity coordenar um esquadrão de agentes inteligentes atuando de forma simultânea no mesmo projeto, reproduzindo a lógica de "Times de Agentes" em ambientes colaborativos.

## Configuração do Ambiente

O esquadrão utiliza uma pasta oculta dentro do diretório desta skill para se comunicar:

- `.agent/skills/sandeco-maestro/.antigravity/equipe/registro_atividades.json` → Registro mestre de atividades, estados e pré-requisitos.
- `.agent/skills/sandeco-maestro/.antigravity/equipe/caixa_entrada/` → Comunicações individuais entre agentes (.msg).
- `.agent/skills/sandeco-maestro/.antigravity/equipe/aviso_geral.msg` → Comunicados globais para todo o esquadrão.
- `.agent/skills/sandeco-maestro/.antigravity/equipe/travas/` → Semáforos para impedir edição simultânea de arquivos.

# IMPORTANTE
1. Nunca crie uma nova pasta `.antigravity` na raiz do projeto.
Utilize a pasta `.antigravity` que fica dentro do diretório desta skill (`.agent/skills/sandeco-maestro/.antigravity/`).
2. Quando começar um novo processo de orquestração sempre limpe 
- registro_atividades.json
- aviso_geral.msg
- travas 
- caixa_entrada

## Papéis do Esquadrão

1. **Condutor (SandecoMaestro)**: O líder do time. Decompõe o problema, distribui responsabilidades e valida planos de ação.
2. **Projetista**: Define a estrutura e padrões arquiteturais antes da codificação.
3. **Executor (Frontend/Backend/BD)**: Realiza atividades técnicas específicas.
4. **Comunicador**: Criação de marca, identidade visual, copywriting e design de páginas.
5. **Explorador**: Busca de informações, documentação e análise de contexto.
6. **Auditor (Advogado do Diabo)**: Procura falhas, bugs e vulnerabilidades de segurança.

## Protocolo de Orquestração Avançada

### 1. Modo de Planejamento (Gatekeeping)

Antes de efetuar alterações relevantes, cada agente deve submeter um **Plano de Ação** à caixa de entrada do SandecoMaestro.

- O agente permanece em modo `SOMENTE_LEITURA` ou `PLANEJAMENTO` até que o SandecoMaestro responda com um comunicado de `APROVADO`.

### 2. Comunicação e Difusão (Broadcast)

- **Comunicação Direta**: Coordenação 1-a-1 entre executores.
- **Comunicado Geral**: SandecoMaestro pode escrever em `aviso_geral.msg` para transmitir novas orientações a todo o esquadrão simultaneamente.

### 3. Sincronização de Atividades e Pré-requisitos

- As atividades em `registro_atividades.json` podem conter uma lista de `pre_requisitos`. Um agente não deve assumir uma atividade se seus pré-requisitos não estiverem com estado `CONCLUIDO`.

## Regras Fundamentais

- NUNCA editar um arquivo se existir um .lock ativo em `.agent/skills/sandeco-maestro/.antigravity/equipe/travas/`.
- Ao finalizar uma atividade, o agente deve liberar suas "travas" e notificar o SandecoMaestro.

---

Siga as instruções em `./workflow.md` e os padrões de prompt em `./USO.md`.
