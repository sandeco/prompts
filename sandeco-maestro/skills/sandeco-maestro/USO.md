# Guia de Escrita e Interação (Padrões de Prompt)

Para utilizar esta skill de forma plena, recomenda-se seguir os padrões abaixo:

## Inicialização
- **Comando:** "SandecoMaestro, prepare o esquadrão para [PROJETO]."
- **Exemplo Real:** "SandecoMaestro, prepare o esquadrão integrando [@[c:\python-projects\orquestrador\.agent\skills\youtube-descricoes] @[c:\python-projects\orquestrador\.agent\skills\youtube-tags] @[c:\python-projects\orquestrador\.agent\skills\youtube-titulos] ]."
- **Efeito:** Cria a infraestrutura de pastas e arquivos.

## Gestão de Tarefas
- **Comando:** "SandecoMaestro, delegue ao [PAPEL] a função de [AVROCAL]."
- **Efeito:** Registra no `registro_atividades.json`.

## Aprovação de Planos
- **Fluxo:** "Agente, envie o plano -> SandecoMaestro aprova."
- **Efeito:** Garante o gatekeeping sugerido no manual.

## Mensageria
- **Comando:** "Diga ao [PAPEL] que [MENSAGEM]." ou "Avise a todos que [COMUNICADO]."
- **Efeito:** Usa as pastas de comunicação para persistir os diálogos.

## Verificação de Travas
- **Fluxo:** "Checar travas antes de editar."
- **Efeito:** Evita conflitos em multi-agentes paralelos.
