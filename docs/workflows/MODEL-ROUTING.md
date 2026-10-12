# Roteamento de modelos e subagentes — scarasoft

Esta política controla apenas a execução computacional. [PROSPECCAO.md](PROSPECCAO.md) continua sendo a fonte das regras comerciais, do ledger e das transições. O dashboard abre o pedido; o Codex coordena. Nenhum agente inicia contato comercial ou deploy por conta própria.

## Matriz de execução

| Papel | Tarefa | Modelo preferido | Configuração deste ambiente | Esforço |
| --- | --- | --- | --- | --- |
| Coordenador | Ler lote, planejar, decidir delegação, classificar/confirmar decisões, consolidar evidências e transições | `gpt-6-sol` | `gpt-6-sol` no projeto | `medium` |
| `discovery` | Candidatos, fontes públicas, extração inicial e URLs em JSON | `gpt-6-luna` | `gpt-6-luna` | `low` |
| `verification` | Conferir fatos, identidade e contatos públicos; separar confirmado/presumido/desconhecido | `gpt-6-luna` | `gpt-6-luna` | `low` |
| `qualification` | Propor A/B/C/D com justificativa, sem score numérico | `gpt-6-sol` | `gpt-6-sol` | `medium` |
| `quality_review` | Auditoria visual e factual, QA de prévia e inconsistências comerciais | `gpt-6-sol` | `gpt-6-sol` | `medium`; `high` só com motivo registrado |

Os IDs GPT-6 foram validados no coordenador e em subagentes com a conta Codex em 2026-10-12. O catálogo local os omitiu, embora o servidor os tenha aceitado; `gpt-6.1-sol` foi recusado. O `model` do coordenador é definido apenas neste projeto; `~/.codex/config.toml` não é alterado. No CLI 0.155.0 testado, o fluxo genérico de spawn **não aplicou** modelo/esforço dos arquivos de papel nem os defaults de `[agents]`; use os parâmetros explícitos abaixo.

## Quando delegar

O coordenador executa diretamente leitura pontual do ledger, operações simples de arquivo, scripts determinísticos e decisões curtas. Delega apenas tarefas independentes e delimitadas cuja pesquisa ou revisão justifique o contexto extra. Antes de delegar, verifica `state`, identidades, `runs/`, cache e evidências anteriores. Cada pedido ao subagente contém somente objetivo, ID do job/lote, arquivos ou fontes necessários, formato JSON esperado e restrições pertinentes. Não copie todo o histórico do projeto.

Subagentes devolvem JSON curto com fatos, URL, data, incertezas e motivo de escalonamento. Evite relatórios narrativos intermediários. Descoberta e verificação não decidem a categoria final. Qualificação propõe; o coordenador confirma a decisão e registra a transição. QA não repete checagens determinísticas aprovadas.

Ao criar o subagente pelo fluxo genérico disponível neste CLI, passe `fork_turns="none"` e os parâmetros efetivos no spawn: `model="gpt-6-luna", reasoning_effort="low"` para descoberta/verificação; `model="gpt-6-sol", reasoning_effort="medium"` para qualificação/QA. Passe o papel no objetivo/instrução, sem presumir que `task_name="discovery"` selecione o papel TOML. Confira `turn_context.model` e `turn_context.effort` no rollout antes de usar uma nova combinação. O default Luna/low de `[agents]` documenta a intenção para clientes compatíveis, mas não foi aplicado pelo spawn genérico testado.

Conflito factual, identidade ambígua, evidência insuficiente ou falha de qualidade relevante retorna ao coordenador com justificativa registrada. O coordenador escolhe entre nova fonte, revisão humana, `D_pendente` ou bloqueio; não repete a mesma busca indefinidamente. `quality_review` com esforço `high` requer motivo concreto e execução explícita com configuração temporária verificada. Não atribua esforço alto automaticamente.

## Concorrência e ledger

O limite inicial é de três subagentes abertos. Paralelize leitura ou pesquisa de jobs distintos, sem dependências entre si. Um job tem um único owner. Somente o coordenador, ou o worker que ele designar conforme [PROSPECCAO.md](PROSPECCAO.md), executa `claim`, `update`, `recover` e transições no SQLite, respeitando locks e estágio atual. Não há concorrência de escrita no mesmo job. Descartar um subagente não descarta o job.

## Ativação e fallback

1. Abra o repositório como projeto confiável. O Codex só carrega `.codex/config.toml` de projetos confiáveis; aqui ele define Sol/medium para o coordenador.
2. Confira `codex --version` e `codex debug models`; confirme os IDs desejados por uma execução curta, pois o catálogo local pode omitir um modelo aceito pela conta.
3. Inicie nova sessão Codex na raiz do repositório e peça uma tarefa delimitada com os parâmetros explícitos acima. Inspecione o modelo e o esforço nos metadados da sessão antes de afirmar economia.
4. Se Luna estiver indisponível, o coordenador Sol executa a tarefa diretamente e registra o fallback. Se Sol estiver indisponível, suspenda classificação/QA e solicite seleção explícita de outro modelo; não troque silenciosamente para a família 5.6. Atualize os TOML somente após confirmar o novo ID e esforço em execução real.

Precedência documentada: flags/`--config` > configuração do projeto confiável > perfil > configuração do usuário > padrões gerenciados/sistema. Para papéis **quando selecionados como papéis personalizados**, `model` e `model_reasoning_effort` no arquivo prevalecem sobre parâmetros de spawn e defaults de `[agents]`. As declarações `agents.<name>.config_file` apontam para arquivos relativos ao `.codex/config.toml`. Arquivos em `.codex/agents/` também são descobertos como papéis personalizados pela documentação atual, mas o spawn genérico exposto neste CLI registrou `agent_role: null`. Uma sessão já aberta pode precisar ser reiniciada para reler a configuração.

## Compatibilidade e medição

Ambiente auditado: `codex-cli 0.155.0`. O catálogo autenticado listou a família 5.6, mas omitiu `gpt-6-luna` e `gpt-6-sol`, ambos aceitos por esta conta no coordenador e em subagentes com esforço `low`/`medium`. `gpt-6.1-sol` foi recusado. A configuração global selecionava `gpt-6-sol`/`medium`, sem alteração. Teste de sessão mostrou filho genérico herdando Sol/medium apesar dos TOML e defaults; os parâmetros explícitos rotearam Luna/low e Sol/medium. A documentação oficial atual confirma as chaves de `[agents]`, arquivos de papéis e configuração por projeto, sujeita a trust. Ver [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference) e [Config basics](https://learn.chatgpt.com/docs/config-file/config-basic).

O benchmark curto com dados fictícios e limites de medição está em [MODEL-ROUTING-BENCHMARK.md](MODEL-ROUTING-BENCHMARK.md). Não interprete diferença de modelo como economia comprovada sem tokens e duração de execuções comparáveis.
