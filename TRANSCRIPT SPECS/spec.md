Crie uma *skill* capaz de transcrever áudios longos (≥ 1h30) com alta eficiência e robustez.

## Requisitos funcionais
- A *skill* deve receber um arquivo de áudio como entrada.
- Deve processar áudios extensos sem perda de contexto ou falhas por timeout/memória.
- A saída deve ser gerada no formato `.srt` (com timestamps precisos e segmentação adequada).

## Requisitos de processamento
- Implementar processamento em *chunks* (segmentação do áudio) para garantir escalabilidade.
- Garantir sincronização temporal consistente entre os segmentos.
- Otimizar uso de memória e tempo de execução para arquivos longos.

## Motor de transcrição (IA)
- A *skill* deve instalar automaticamente um modelo de transcrição local (ex: Whisper ou equivalente).
- No primeiro uso, deve detectar automaticamente a presença de GPU no ambiente do usuário:
  
  - **Se houver GPU disponível:**
    - Instalar e utilizar `faster-whisper` (otimizado com CUDA).
  
  - **Se NÃO houver GPU:**
    - Instalar e utilizar `whisper` padrão (CPU).

## Requisitos adicionais
- O processo de instalação deve ser automático e transparente para o usuário.
- Deve haver fallback seguro em caso de falha na detecção de GPU.
- A *skill* deve ser resiliente a erros (ex: áudio corrompido, interrupções, etc.).
- Permitir futura extensão para múltiplos idiomas e detecção automática de linguagem.

## Saída esperada
- Arquivo `.srt` estruturado corretamente:
  - Índice sequencial
  - Timestamp inicial e final
  - Texto transcrito correspondente

## IMPORTANTE
A medida que a transcrição for recebida pelo whisper a skill deve ir salvando o arquivo srt incrementalmente.