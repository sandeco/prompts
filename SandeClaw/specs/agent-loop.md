# Spec: Agent Loop (Reasoning Engine)

**Versão:** 1.0
**Status:** Aprovada
**Autor:** SandecoClaw Agent
**Data:** 2026-03-06

---

## 1. Resumo

O **Agent Loop** é a engrenagem central do SandecoClaw. Ele implementa o padrão ReAct (Reasoning and Acting). É o módulo onde uma ação bruta entra, é submetida ao LLM base (Thought), uma ou mais ferramentas são chamadas (Action+Observation), até um veredito de resposta final ser chegado, repetindo em loop limitado de iterações para evitar impasses de contexto infinito.

---

## 2. Contexto e Motivação

**Problema:**
Um LLM standard responde de forma estática do ponto de vista do seu conhecimento congelado. Para que ele vire um Agente, é preciso que ele receba e aja recursivamente no ambiente que está imersivo a ele.

**Evidências:**
Tentar fazer uma "Mega Prompt" para que ele decida e gere arquivo num take só quase sempre gera inferências sujas e falsas promessas de execução (alucinadas). Ele deve executar uma ferramental real via Loop e aguardar o resultado para só então inferir o fecho.

**Por que agora:**
Precisamos desacoplar a parte de grammy/entrada de dados da parte de processamento puramente sistêmico (Tool calls/Registry).

---

## 3. Goals (Objetivos)

- [ ] G-01: Rodar uma iteração abstrata e agnóstica onde um `LLM` possa fornecer ou uma resposta final legível, ou um Tool Call bem estruturado.
- [ ] G-02: Executar automaticamente o call pelo Factory de tools e repassar a observação como se fosse o usuário (`ToolOutput`) no proximo payload pro LLM.
- [ ] G-03: Parar de forma determinística por um hard limit configurável (ex: 5 interações no MAX_ITERATIONS).

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Completude (Success Rate de ReAct loops) | N/A | 95% encerram antes do teto | Em prod |
| Hard limit triggers | Sem limite | Estoura limpo (Throw Error) nas iterações superadas (>MAX) | Imediato |

---

## 4. Non-Goals (Fora do Escopo)

- NG-01: Manter sessões abertas suspensas aguardando input do usuário no MEIO de um loop de Agent Loop ativo.
- NG-02: Executar Tools de forma paralela usando workers (as tool calls serão tratadas resolutivamente em cascata Promise-based Node sequencial no escopo da mesma iteração ReAct).

---

## 5. Usuários e Personas

**Módulo Cliente Primário:** Classes dentro de `TelegramBot` ou `SkillExecutor` que invocam o AgentLoop repassando o array de mensagens antigas e o System Prompt correspondente às ferramentas em registro ativo.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve suportar iterar sobre a classe `BaseTool` herdada para todas as features disponíveis usando o pattern Registry. | Must | Se as Tools não responderam JSON schema, falha ou pede pro LLM de novo. |
| RF-02 | O Agent Loop deve sempre instanciar uma iteração limitadora e parar a execução quando `current > MAX_ITERATIONS` for verificado. | Must | Uma chamada maliciosa não gera billing infinito. |
| RF-03 | A Observação do ambiente gerada por uma base de Tool (`result.output`) deve sempre retornar pro array de mensagens para a próxima dedução (Thought). | Must | LLM não deve se perder; e não pode pre-anunciar execução. |
| RF-04 | O Agent Loop deve registrar logs detalhados de cada etapa (Thought, Action, Observation) no console para monitoramento. | Must | O desenvolvedor deve conseguir acompanhar o raciocínio do agente em tempo real. |

### 6.2 Fluxo Principal (Happy Path)

1. Entrada invoca o método principal: `AgentLoop.run()`.
2. Appends de mensagens recentes do array formatado do banco para compilar com prompts das tools em `SystemPrompt`.
3. LLM infere no array atual e decide a chamada `ToolChoice`.
4. Uma skill retorna um tool call exigendo usar "criar_arquivo".
5. Iterator detecta chamada, Factory instancia e preenche com Args do JSON.
6. A Promise da Tool retorna "Arquivo Foo feito!".
7. Injeta resultado na variável observation array. Retorna ao (3) que gera a final response "Usuário, arquivo Foo foi construído!".

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Max Iterations Reached:**
1. A IA acha que falta informação ou repete tool call incorreto seguidamente.
2. Contagem do loop alcança o `process.env.MAX_ITERATIONS` (5).
3. O Loop injeta break forçado.
4. Output final vira: "Desculpe, desisti ou deu timeout no processamento pois falhei nas chamadas em MAX iteracoes."

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Timeout por interção unitária LLM | < 120s | Pra evitar socket hang do Node |

---

## 8. Design e Interface

**Componentes afetados:** Terminal log-output, Repasse assíncrono pro Output de chat.
Interno apenas.

---

## 9. Modelo de Dados

Não gera tabelas SQL exclusivas, é stateful em RAM contendo arrays literais durante as interações. No fim, a resposta é entregue para salvar via MemoryManager.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| ILlmProvider implementations | Obrigatória | Loop principal é interrompido. |
| ToolRegistry instanciado | Obrigatória | System prompt ficara vazio / não enxerga braços atuadores. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: JSON Malformado de Argumento da IA | O LLM burla a formatação e entrega string malfeita em vez do schema no ToolCall | Catch no loop e gera Observation pro LLM dizendo: "JSON inválido, reenvie a estrutura corrigida por favor." |
| EC-02: Ferramenta retorna Throw (Error hard) | Tentou criar num path que não existe na máquina host do Node (`fs.writeFileSync` failure). | O catch manda: `{"error": "ENOENT path not exists..."}` como string de observação devolta pra IA corrigir caminho. |
| EC-03: Max Iteration Limits | Variável de MAX não foi lida do env (null). | Definir fallback pra 5 explicitamente pra não corromper infra. |

---

## 12. Segurança e Privacidade

- As Tools são injetadas em prompt - nunca expõe secrets nem paths internos completos que dão base para jailbreak explícito sem sanilização (a Tool deve usar regex no parsing dos envios).

---

## 13. Plano de Rollout

- Big Bang via git push na branch core e deploy manual em dev.

---

## 14. Open Questions

N/A
