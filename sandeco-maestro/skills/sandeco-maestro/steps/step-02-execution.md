# Passo 2: Acionamento das Skills

## Objetivo

Disparar as skills conforme o modo selecionado, respeitando pré-requisitos, travas e protocolos de comunicação do esquadrão.

## Instruções

1. **Verificação de Pré-requisitos:**
   - Antes de acionar qualquer skill, consulte o `registro_atividades.json` para confirmar que todos os `pre_requisitos` da atividade estejam com estado `CONCLUIDO`.
   - Skills com pré-requisitos pendentes devem aguardar na fila.

2. **Verificação de Travas:**
   - Antes de qualquer edição de arquivo, verifique se existe um `.lock` ativo em `.agent/skills/sandeco-maestro/.antigravity/equipe/travas/`.
   - Se houver trava ativa, aguarde a liberação antes de prosseguir.

3. **Modo Sequencial:**
   - Se `modo_execucao` for `sequencial`:
     - Para cada skill em `skills_list`:
       - Instrua o agente a carregar e executar a skill correspondente.
       - Aguarde a conclusão antes de iniciar a próxima.
       - Atualize o estado da atividade para `CONCLUIDO` no registro.
       - Informe o status de cada execução ao SandecoMaestro.

4. **Modo Paralelo:**
   - Se `modo_execucao` for `paralelo`:
     - Para cada skill em `skills_list`:
       - Dispare um **subagente** dedicado para executar a skill.
       - Não aguarde a conclusão para disparar as demais.
       - Cada subagente deve atualizar seu estado no registro ao finalizar.
       - Informe ao usuário que as skills estão sendo processadas simultaneamente.

5. **Notificação e Encerramento:**
   - Ao concluir cada atividade, libere todas as travas associadas.
   - Envie um comunicado geral (broadcast) informando a conclusão via `scripts/gerenciador_equipe.py` com o comando `comunicado_geral`.
   - Apresente um resumo completo da operação ao usuário.
   - Finalize o workflow.
