# Spec: Memory Module (SQLite Persistence)

**Versão:** 1.0
**Status:** Aprovada
**Autor:** SandecoClaw Agent
**Data:** 2026-03-06

---

## 1. Resumo

O módulo de persistência de estado do SandecoClaw gerencia tanto as conversas de longo prazo em banco de dados SQLite (`better-sqlite3`) quanto atua como manager da janela de contexto para impedir que o limite maximo do envelope de tokens da IA (Context Window) estoure.

---

## 2. Contexto e Motivação

**Problema:**
LLMs são stateless - eles esquecem tudo que foi dito na interação anterior de uma API REST call.
Sem armazenamento persistente, o robô perde a utilidade primária de um "Agente Pessoal".

**Evidências:**
Tentativas de armazenar arrays in-memory no Node.js funcionam apenas até o app ser encerrado/reiniciado (hot-reload da infra ou npm dev reload). O histórico vaporizava.

**Por que agora:**
A adoção do SQLite é veloz, serverless (um arquivo físico único), suporta chamadas síncronas rápidas (bloqueios impercetiveis para volumes unicos de acesso Telegram) e não consome infra adicional. 

---

## 3. Goals (Objetivos)

- [ ] G-01: Prover Storage fixo e rápido de mensagens do Telegram para recriar as conversas ativas.
- [ ] G-02: Possuir um `MemoryManager` central (Facade) que decide automaticamente quando as mensagens velhas deverão ser ignoradas (Truncamento nativo) sem apagar sua versão persistente histórica.
- [ ] G-03: Ranquear requisições de SQLite usando Repository Pattern, desacoplando SQL views puro do Agent Loop principal.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Tempo de Write Sync | N/A | < 10ms | Constante |
| Limite de Arquivo DB | 0.0 MB | Manter sob 500 MB (Vacuum ocasional) | 1 Ano |

---

## 4. Non-Goals (Fora do Escopo)

- NG-01: Não criará banco distribuído de Grafos ou Chroma Vector Database. A intenção é ter memória conversacional direta, sem Sematic Search Complexo inicialmente.
- NG-02: ORMs como Prisma, TypeORM etc. Usaremos SQL nativo `better-sqlite3` por leveza e clareza. 

---

## 5. Usuários e Personas

**Módulos primários:** 
- O arquivo `DocumentHandler` (grava input principal).
- A Classe `TelegramBot` via `AgentLoop` (lê e grava answers).
- A Ferramenta Genérica de Sistema (apenas lê seu próprio histórico pra sumarização futura).

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O Singleton de DB deve criar a tabela de histórico (`conversations` e `messages`) sozinho no startup se não existirem. | Must | Excluir db antigo; reiniciar app; arquivo data/ db.sqlite reaparece limpo. |
| RF-02 | O Storage deve usar WAL (Write-Ahead Logging) ativo pra manter leitura sem block | Must | Múltiplas msgs via Telegram não congelam o bot por locks do sqlite3 nativo. |
| RF-03 | A classe abstrata repassará ao Agent Loop somente o número `MEMORY_WINDOW_SIZE` de mensagens recentes. | Must | Uma chamada REST pro Gemini não falhará por estouro de token via histórico inchado (1M text words). |

### 6.2 Fluxo Principal (Happy Path)

1. Usuário envia "Oi agente".
2. `ConversationRepository` localiza UUID conversacional ativo do User_ID.
3. `MessageRepository` persiste a nova mensagem `role="user"` com texto associado ao ID.
4. `MemoryManager` extrai da DB as últimas "N" conversas usando LIMIT.
5. Devolve array `[]` filtrado para AgentLoop atuar.
6. A resposta do bot com `role="assistant"` ou `role="tool"` é persistida analogamente pelas mesmas classes.

### 6.3 Fluxos Alternativos

Falhas de Banco - Vide [11. Edge Cases e Tratamento de Erros](#11-edge-cases-e-tratamento-de-erros)

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Transações Seguras | Auto-commit nativo | WAL ativo resolve concorrencia Single thread node. |

---

## 8. Design e Interface

Pura estrutura sem interface visual (ver `sqlite-viewer` VSCode extensão para debbug interno).

---

## 9. Modelo de Dados

`conversations`
`messages`

Sem foreign keys restritas ativadas com pragma foreign_keys=ON pra priorizar inserts mais leves sem checks, apenas referências programáticas via Node.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| `better-sqlite3` | Obrigatória | O agente vai quebrar a Main.ts na instancialização. |
| Filesystem (`fs`) | Obrigatório | DB path tem que ser gerido e gravado via Node FS Perms. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: Arquivo Lock file corrupto | Desligamento forçado de energia no Write SQLite local. | SQLite reabre do journaling automático e read de forma íntegra sem interrupções maiores. |
| EC-02: Null Bytes na Mensagem do Usuário | Receber bytes invisíveis no TG causando Erro de syntax DB. | Stripping na entrada `content.replace(/\u0000/g, '')`. O DB não engole a query suja. |
| EC-03: Memória Enorme de Resposta de LLM | O modelo decide cuspir 16k tokens em Output. | Limite o SQLite max text de String e truncate se estourar Max Byte (fallback). |

---

## 12. Segurança e Privacidade

- **Arquivos DB Sensíveis:** O `sandecoclaw.db` jamais pode ir pro Git (Adicionar no `.gitignore` /data).
- **Sem senhas cruas no prompt:** O DB grava as msgs do usuário. Não logaremos APIs ali como System Prompts secretos pra evitar persistencia indevida.

---

## 13. Plano de Rollout

Rollout instantâneo para DB Version 1. Scripts de Migration explícitos não são escopo inicial, pra reset bastando apagar e reinjetar no DB_PATH local de DEV.

---

## 14. Open Questions

N/A
