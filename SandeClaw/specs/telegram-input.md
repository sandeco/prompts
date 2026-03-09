# Spec: Telegram Input Handler

**Versão:** 1.1
**Status:** Em Revisão
**Autor:** SandecoClaw Agent
**Data:** 2026-03-08

---

## 1. Resumo

O módulo Telegram Input recebe eventos brutos advindos das APIs do Telegram via biblioteca grammy (Long Polling), faz a filtragem de segurança por whitelist de ID, converte anexos (documentos PDF e arquivos/mensagens de voz de áudio) em texto viável, e injeta na memória do ciclo de agente para resolução AI.

---

## 2. Contexto e Motivação

**Problema:**
Um LLM nativo e as APIs de LLMs cruas (DeepSeek e Gemini) consomem texto e mídias num array fixo de History. Eles não sabem por ondem vêm, nem descompactam pacotes PDF ou áudios em texto nativamente no formato esperado do chat.
Frequentemente é muito mais prático para o usuário enviar um áudio (Voice Note) no Telegram explicando o que ele deseja, ao invés de digitar textos longos no teclado do celular.

**Evidências:**
Usuários frequentemente alimentam "Agentes" com PDFs via chat para analises (Academic Skills). Além disso, usuários móveis preferem interagir via áudio (Voice) pela comodidade.

**Por que agora:**
A lib Grammy suporta streaming de arquivos anexos por `getFile()`. O Nodejs lida com a ponte em RAM para extração usando o `pdf-parse`, e a integração com um modelo Whisper local permite extrair o texto de qualquer áudio enviado no chat de forma privada e sem custos de API externa.

---

## 3. Goals (Objetivos)

- [ ] G-01: Receber mensagens puras de texto (`message:text`) dos usuários em whitelist e encaminhar de forma crua ao Pipeline AI (`skill -> agent -> output`).
- [ ] G-02: Receber envios de anexo (`message:document`) que sejam do tipo `.pdf` ou `.md`, salvando temporariamente no disco para leitura (via pdf-parse ou leitura de texto puro).
- [ ] G-03: Receber mensagens de voz (`message:voice`) e arquivos de áudio (`message:audio`) de qualquer formato suportado, baixar temporariamente e realizar a transcrição para texto utilizando processamento STT (Speech-to-Text) com Whisper local. O texto transcrito é encaminhado ao Pipeline AI como se fosse texto digitado.
- [ ] G-04: Informar instantaneamente ao usuário "Typing..." ou "Recording voice..." via API Telegram pra que o usuário saiba que a string de download/análise pesada está de fato sob carga de processamento e não engasgou.
- [ ] G-05: Injetar metadados no Agent Loop quando o input do usuário for originado de um áudio (Voice Note), sugerindo ao LLM ou ao Output Handler que responda em voz (TTS via `pt-BR-ThalitaMultilingualNeural`) na saída, a depender das regras globais do bot.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| Arquivo Fantasma Residual TMP | Infinito | 0 bytes deixados (PDF, MD e Audio) | Always |
| Rate de Parseamento Texto | Text Only | 90% PDFs e 100% MDs lidos | MVP |
| Rate de Transcrição STT | 0% | Modelos locais lidando com áudios curtos/médios sem CRASH de RAM | MVP |

---

## 4. Non-Goals (Fora do Escopo)

- NG-01: Mídias Visuais cruas / ImageVision. Este escopo é de Texto, Documentos e Áudios. Não aceitaremos JPGs, PNGs ou OCR de imagens estáticas no Input primário nesta especificação (foco em NLP e processamento textual).
- NG-02: Receber envios via Webhook em Servidor Externo. Rodaremos num loop simples interno Long Polling na máquina local.
- NG-03: Processamento em tempo real do stream de áudio. O sistema precisará que o arquivo inteiro seja baixado para iniciar o Whisper.
- NG-04: Gerar o áudio final (TTS) no próprio Input Handler. O módulo de Input é responsável apenas por **ouvir e sinalizar** que uma resposta em áudio foi solicitada explícita ou implicitamente (se o input for áudio). Quem envia o arquivo `.ogg` falado é o Output Handler, a partir da flag setada por este módulo ou pelo Agent Loop.

---

## 5. Usuários e Personas

**Usuario:** Sandeco interagindo do smartphone para a máquina desktop local através de uma DM do Bot do Telegram, mandando comandos de voz dirigindo o carro pedindo para o agente agir e exigindo receber a resposta de volta em formato de voz (TTS Thalita) para audição rápida sem contato visual no app.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | O sistema deve ouvir eventos `message:text` filtrados. | Must | Bot intercepta Msg ID 123 válida em < 2 segundos e o sistema inicia memory. |
| RF-02 | O sistema deve acionar a extração local quando receber Documentos com mimetype `application/pdf` ou arquivos contendo a extensão `.md`. | Must | O sistema retorna o conteúdo do arquivo transformado em bloco de texto concatenado à Legenda. |
| RF-03 | O sistema deve excluir os documentos baixados da `tmpDir` (`./tmp`) após o parse ou em caso de erro. | Must | Exclusão do rastro na clausula finally da try-catch. Sem memory leaks no FileSystem. |
| RF-04 | O sistema deve ouvir eventos de voz (`message:voice`) e áudio (`message:audio`). | Must | O sistema reconhece anexo de aúdio e o envia para parser do Whisper. |
| RF-05 | O sistema deve usar o Whisper Local para transcrever o áudio baixado para texto. | Must | Áudio convertido para STT. O log do bot mostra "Transcript: xyz" e o sistema envia para o Agent Loop. |
| RF-06 | O sistema deve sinalizar a preferência por áudio (TTS) caso o input seja originário de voz ou o texto possua keyword explícita ("responda em áudio / fale comigo"). | Must | O payload injetado na Memory conterá um marcador booleano `requires_audio_reply: true` e a *voice_id* fixada em `pt-BR-ThalitaMultilingualNeural`. |

### 6.2 Fluxo Principal (Happy Path)

1. Entrada: "Cria um PRD pro meu novo app de finanças e me responde em áudio" enviado por Voice Note no Telegram Client pelo usuário.
2. Bot Grammy valida se user ID = `TELEGRAM_ALLOWED_USER_IDS`.
3. Evento classificado como Voz via `on(["message:voice", "message:audio"])`.
4. Bot Controller atualiza status para o usuário do Telegram: `sendChatAction('record_voice')` ou `typing`.
5. API de stream do TG contata URL temporária interna para baixar chunks raw do áudio (`.ogg`, `.mp3`) no `/tmp/`.
6. Arquivo salvo é encaminhado para o módulo de áudio usando o modelo Whisper local (subprocesso/lib).
7. O sistema devolve o texto transcrito em PT-BR (ou detectado automaticamente pelo Whisper) com uma metatag interna marcando o trigger de TTS de volta, e o sistema exclui o physical temp file na conclusão do hook.
8. Texto transcrito e a Flag `requires_audio_reply` seguem para o Agent Loop injetados pelo sistema, habilitando o Telegram Output a renderizar a engine `edge_tts` no fim da chain.

### 6.3 Fluxos Alternativos

Falhas - ver seção 11.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | Async IO | 100% Non-Blocking | O arquivo baixando nao interrompe msgs concorrentes de texto enviadas. |
| RNF-02 | STT Performance | < 2x a duração | O tempo para Whisper processar STT não deve exceder significativamente a extração local dependendo da GPU ou CPU usada. |

---

## 8. Design e Interface

Pura estrutura Middleware no App Controller sem vizualização fora o Client TG nativo do smartphone do usuário. Apenas haverá feedback de actions como envio de texto simulando se o bot realmente ouviu em paralelo a extração STT.

---

## 9. Modelo de Dados

Não gera tabela SQLite (Input apenas intermedeia).
As mensagens se tornam blocos injetados na Memory SQLite com as quebras. 
A pasta `/tmp/` retém temporariamente `.pdf`, `.md`, `.mp3`, `.ogg`, etc.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| GrammyJS | Obrigatória | Nenhuma intercepção ocorrerá. |
| Pdf-Parse npm | Secundária | Texto cairá no Agent Loop como string vazia de documento ininteligível. |
| Whisper Local CLI/Lib | Secundária | Falha a transcrição e bot responde: "⚠️ Não consegui inicializar o Whisper local agora." |
| Engine Edge-TTS | Secundária | O Input mapeia a Flag de áudio. Se o módulo Output falhar em processar, ocorre Fall-back para texto no final. O impacto primário de identificar a intenção é salvo. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| EC-01: Anexo não é suportado | Usuário envia DOCX, XLS ou JPG. | O sistema responde via Telegram: "⚠️ No momento, só consigo processar texto estruturado (.md), áudio e PDF.", cancela o processamento e aciona a limpeza do TEMP. |
| EC-02: OOM (Out of Memory) no Whisper | Áudio massivo pesa e Whisper crasha o processo no host. | Timeout de 60s e trycatch do Node envelopa falha. O sistema envia e o usuário recebe: "⚠️ Falha ao processar o áudio: arquivo grande demais ou falha no serviço." |
| EC-03: Áudio vazio ou mudo | Arquivo com barulho nulo enviado. | Whisper retorna `""`. O sistema envia a resposta ao usuário: "Áudio vazio captado. Pode reenviar?" e não polui o Agent Loop com string vazia. |
| EC-04: PDF massivo | Upload finalizado e parsing travando estourando local. | Envelopamento de limite de Bytes (ex. 20MB max para text extract). O Catch block captura falha de Memory e o sistema limpa o TEMP no `finally`. O usuário recebe alerta de PDF muito grande. |
| EC-05: Timeout da API do Telegram (Download de Mídia) | A rede falha durante o streaming do arquivo de áudio ou PDF pelo Telegram. | O downloader dá throw de Timeout após 15 segundos sem bytes recebidos. O bot envia mensagem ao usuário: "⚠️ Falha ao baixar arquivo do Telegram. Tente novamente." e a promise falha limpando qualquer resquício de chunk. |
| EC-06: API de LLM Externa indisponível para Agent Loop | STT extrai o texto perfeitamente, a LLM do Core cai em seguida | O STT conclui sua parte transcrevendo e injeta o texto na Memory. A falha da LLM subsequente é tratada pelo Handler Generativo. O input é mantido como texto salvo. |
| EC-07: Solicitação explícita por áudio ambígua | Usuário manda "responda isso sem ser em áudio" | Se não for flag por RegEx ou NLP fino, o sistema pode não setar "requires_audio_reply". Por design atual, ele apenas injeta `true` se a intenção for estritamente confirmada via LLM guardrail e/ou via áudio nativo (Voice Note que assume default = true). |

---

## 12. Segurança e Privacidade

- **Upload e Download Seguro:** Ao não salvar links externos nem exibir uploads localmente de forma compartilhada, asseguramos sandboxing.
- **Transcrições Locais:** A voz trafega end-to-end do telegram ao storage local e é consumida localmente sem ir para OpenAI Whisper cloud endpoints. Total controle de privacidade.

---

## 13. Plano de Rollout

A estrutura do `AudioHandler` acoplada ao Bot Core ficarão em produção local assim que instancializada no App() init() ou acopladas nas rules do `Composer.on("message:voice")`.

---

## 14. Open Questions

- Como acionar o Whisper local a partir do backend Node.js (se SandecoClaw ainda for Node). *Decisão pendente: usar bridge FFI, ou Child Process nativo na máquina.*
- Precisaremos de um `ffmpeg` standalone local para converter aúdio em formato compatível com o whisper ou o próprio whisper local processa os M4A, OPUS/OGG (nativos do Telegram)? *Assume-se que whisper lida com OGG/OPUS baseados em FFMEPG instalado na máquina da Host.*

---

## 15. Relatório de Avaliação Final (SDD)
```text
============================================================
  SPEC QUALITY REPORT
  SCORE TOTAL: 94.0/100  —  ⭐ Excelente — Pronta para implementação

  BREAKDOWN POR DIMENSÃO:
  Completude           100%       30%     30.0/pt
  Testabilidade        100%       25%     25.0/pt
  Clareza               70%       20%     14.0/pt
  Escopo               100%       15%     15.0/pt
  Edge Cases           100%       10%     10.0/pt

  ✅ PONTOS FORTES:
     ✅ Seção 1 (Resumo) presente e preenchida
     ✅ Seção 2 (Contexto) presente e preenchida
     ✅ Seção 3 (Goals) presente e preenchida
     ✅ Seção 4 (Non-Goals) presente e preenchida
     ✅ Seção 5 (Usuários) presente e preenchida
============================================================
```
