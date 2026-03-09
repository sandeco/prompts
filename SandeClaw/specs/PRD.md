# Spec: PRD — SandecoClaw Core

**Versão:** 1.0
**Status:** Aprovada
**Autor:** SandecoClaw Agent
**Data:** 2026-03-06
**Reviewers:** Sandeco

---

## 1. Resumo

O SandeClaw é um agente pessoal de Inteligência Artificial para operar 100% localmente no desktop do usuário. Ele recebe comandos exclusivamente pelo Telegram, processa-os através de um pipeline que suporta múltiplos LLMs dinamicamente, e tem acesso persistente à memória em SQLite.

---

## 2. Contexto e Motivação

**Problema:**
Agentes hospedados na nuvem e serviços de terceiros requerem expor dados privados ou têm custos recorrentes altos, além da falta de total governança sobre as próprias "skills" customizadas. O usuário não tem controle pleno de instâncias como o OpenClaw sem esbarrar na complexidade da nuvem ou lock-in.

**Evidências:**
Tentativas anteriores baseadas no OpenClaw funcionavam, mas a intenção primária agora é manter uma base minimalista sob controle total do usuário, operando no próprio SO.

**Por que agora:**
A ascensão de LLMs super eficientes (Gemini 1.5/2.0+ e DeepSeek) somada com a facilidade da API do Telegram permitem rodar um agente pessoal sem os atritos operacionais de UI na web.

---

## 3. Goals (Objetivos)

- [ ] G-01: Operar primariamente recebendo e respondendo requisições pelo Telegram via `grammy`.
- [ ] G-02: Intercambiar "cérebros" (LLMs) usando padronização (DeepSeek, Gemini).
- [ ] G-03: Reter contexto por múltiplos turnos com SQLite via repositórios TS.
- [ ] G-04: Respeitar limites rigorosos de autorização via user ID (whitelist).

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Uptime local da API de bot | 0% | 99% após testes | 30 dias |
| Troca dinâmica de Skills via hot-reload | Sem suporte | 1 segundo recarga | 10 dias |

---

## 4. Non-Goals (Fora do Escopo)

- NG-01: Não terá interface Web (React/Vue/HTML). A interface é unicamente o Telegram.
- NG-02: Não suportará múltiplos usuários além da Whitelist estrita. Não é SaaS.
- NG-03: Suporte a bancos de dados robustos como PostgreSQL/Mongo. Foco exclusivo em SQLite local mínimo.

---

## 5. Usuários e Personas

**Usuário primário:** Sandeco (proprietário), acessando via dispositivo móvel ou desktop via cliente Telegram, utilizando IDs em whitelist restrita.

**Jornada atual (sem a feature):**
O usuário tem que gerir manualmente as APIs ou logar em múltiplas abas web (ChatGPT, Gemini) para acionar "skills" em blocos de texto independentes sem integrações de arquivos no próprio SO local.

**Jornada futura (com a feature):**
O usuário envia um chat no Telegram, o SandecoClaw roda local em background num terminal, chama LLMs, lê Skills em pastas locais, aciona ferramentas e responde no mesmo chat de forma orgânica.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve rodar via loop de polling persistente da biblioteca Grammy | Must | O terminal aciona o listener com `npm run dev` e intercepta as mensagens sem fechar. |
| RF-02 | O sistema deve validar todas as mensagens entrantes contra a variável de `TELEGRAM_ALLOWED_USER_IDS` | Must | Um usuário não cadastrado recebe ignore instantâneo; nenhum log sensível é disparado e nenhuma API key é torrada. |
| RF-03 | O sistema deve alternar "LLMs" instanciando fábricas (`ProviderFactory`) | Must | Trocar "gemini" por "deepseek" no config envia prompts diretos ao endpoint alvo corretamente parseado. |

### 6.2 Fluxo Principal (Happy Path)

1. O usuário manda uma string "resuma para mim" no Telegram.
2. O sistema do bot no PC intercepta (via Facade do `AgentController`).
3. O sistema checa se ID pertence à Whitelist (SIM).
4. O sistema joga pro Loop (ReAct / AgentLoop) com Contexto Local salvo do banco SQLite.
5. O LLM selecionado processa, encontra ou não a Tool necessária.
6. A resposta volta via Output Handler no chat Telegram.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Falha de API de LLM:**
1. LLM primário (ex: gemini) sobrecarregado (503).
2. O AgentLoop tenta fallback para outro config ou falha graciosamente enviando aviso pro Telegram em vez de quebrar a Promise da main engine.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Latência de repassagem de Msg | < 1000ms | Não confunde atraso do bot com o da API do provedor LLM. |
| RNF-02 | Persistência Ágil | SQlite Síncrono | `better-sqlite3` escolhido pela performance e simplicidade em single thread Node.js |

---

## 8. Design e Interface

**Componentes afetados:** Terminal log-output, e Chats do aplicativo Telegram do usuário Whitelisted.

**Estados da UI (No Telegram):**
- Estado de processamento: O bot sinaliza ação de digitação contínua via Chat Action do telegram até a requisição real de envio ser efetuada.

---

## 9. Modelo de Dados

**Entidades modificadas/persistidas em `./data/`**

```sql
conversations {
  id: string        // UUID ou Hash único da thread do usuário
  user_id: string   // O originador whitelisted
  provider: string  // ex: 'gemini'
}
messages {
  conversation_id: string 
  role: string      // 'user'|'assistant'|'system'
  content: string   // Raw Payload da conversa
}
```

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| Telegram API | Obrigatória | O agente se tornará inutilizável / Modo sleep no Node. |
| APIs (Gemini/DeepSeek) | Obrigatória | Sem raciocínio lógico. Precisará tentar fallback no `ProviderFactory`. |
| pacote `Grammy` | Obrigatória | Lib node core da arquitetura de polling |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: Injeção por Usuário Falso | Receber requests de bots/crawlers | Cortar no Top-Level Middleware sem chegar ao DB. |
| EC-02: Banco de dados bloqueado | Dois loops simultâneos tentam escrita intensa | Espera via timeout natural do driver WAL (Write Ahead Logic), senão descarta soft e avisa LLM. |
| EC-03: Key Inválida | O arquivo `.env` tá corrompido ou API key descontinuada | Agent tenta inciar, loga Erro fatal de auth no Terminal e notifica no log que o provider `X` falhou. |
| EC-04: Excesso de processamento CPU | Arquivos imensos mandados para summary/pdf local | Trava por threshold e diz "Esse arquivo excede limites locais suportados." |

---

## 12. Segurança e Privacidade

- **Autenticação:** Baseada exclusivamente no Telegram User ID fornecido no array `.env` (`TELEGRAM_ALLOWED_USER_IDS`).
- **Autorização:** Aquele userId = Admin, os demais = rejeitados.

---

## 13. Plano de Rollout

- **Estratégia:** Deploy em máquina local rodando `npm run dev` para a instância primaria.
- **Monitoramento:** Log no Stdout no terminal para acompanhar transições de Agent Loop e falhas nas Requests.

---

## 14. Open Questions



