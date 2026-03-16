# Passo 1: Preparação e Validação do Esquadrão

## Objetivo

Montar a infraestrutura de comunicação do esquadrão, coletar a lista de skills e validar sua existência.

## Instruções

1. **Montar Infraestrutura do Esquadrão:**
   - Execute o script `scripts/gerenciador_equipe.py` com o comando `iniciar` para criar a estrutura de pastas e arquivos necessários em `.agent/skills/sandeco-maestro/.antigravity/equipe/`.
   - Isso criará automaticamente: `registro_atividades.json`, `caixa_entrada/`, `travas/` e `aviso_geral.msg`.

2. **Coleta de Dados:**
   - Pergunte ao usuário quais skills ele deseja acionar (se não tiverem sido passadas como argumento).
   - Pergunte o modo de execução: `sequencial` ou `paralelo`.

3. **Validação de Skills:**
   - Verifique se cada skill informada existe no diretório `.agent/skills/`.
   - Se alguma skill não for encontrada, notifique o usuário e solicite a correção da lista.

4. **Registro de Atividades:**
   - Para cada skill validada, registre uma atividade no `registro_atividades.json` usando o script `scripts/gerenciador_equipe.py` com o comando `criar_atividade`.
   - Salve a lista validada em `skills_list`.
   - Salve o modo em `modo_execucao`.

5. **Próximo Passo:**
   - Prossiga para `./step-02-execution.md`.
