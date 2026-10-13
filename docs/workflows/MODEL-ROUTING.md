# Roteamento de modelos e subagentes — scarasoft

Esta política controla apenas a execução computacional. [PROSPECCAO.md](PROSPECCAO.md) continua sendo a fonte das regras comerciais, do ledger e das transições. O dashboard abre o pedido; o Codex coordena. Nenhum agente inicia contato comercial ou deploy por conta própria.

## Matriz de execução

| Papel | Tarefa | Modelo preferido | Configuração deste ambiente | Esforço |
| --- | --- | --- | --- | --- |
| Coordenador | Ler lote, planejar, decidir delegação, classificar/confirmar decisões, consolidar evidências e transições | `gpt-6-sol` | `gpt-6-sol` no projeto | `medium` |
| `discovery` | Candidatos, fontes públicas, extração inicial e URLs em JSON | `gpt-6-luna` | `gpt-6-luna` | `low` |
| `verification` | Conferir fatos, identidade e contatos públicos; separar confirmado/presumido/desconhecido | `gpt-6-luna` | `gpt-6-luna` | `low` |
| `qualification` | Análise comercial estruturada; propor A/B/C/D com justificativa, sem score numérico | `gpt-6-luna` | `gpt-6-luna` | `medium` |
| `quality_review` | Auditoria visual/editorial complexa e QA de prévia | `gpt-6-sol` | `gpt-6-sol` | `medium`; `high` só como exceção justificada |

Os IDs GPT-6 foram validados no coordenador e em subagentes com a conta Codex em 2026-10-12. O catálogo local os omitiu, embora o servidor os tenha aceitado; `gpt-6.1-sol` foi recusado. O `model` do coordenador é definido apenas neste projeto; `~/.codex/config.toml` não é alterado. No CLI 0.155.0 testado, o fluxo genérico de spawn **não aplicou** modelo/esforço dos arquivos de papel nem os defaults de `[agents]`; use os parâmetros explícitos abaixo.

## Quando delegar

O coordenador executa diretamente leitura pontual do ledger, operações simples de arquivo, scripts determinísticos e decisões curtas. Delega apenas tarefas independentes e delimitadas cuja pesquisa ou revisão justifique o contexto extra. Antes de delegar, verifica `state`, identidades, `runs/`, cache e evidências anteriores. Cada pedido ao subagente contém somente objetivo, ID do job/lote, arquivos ou fontes necessários, formato JSON esperado e restrições pertinentes. Não copie todo o histórico do projeto.

Subagentes devolvem JSON curto com fatos, URL, data, incertezas e motivo de escalonamento. Evite relatórios narrativos intermediários. Descoberta e verificação não decidem a categoria final. Qualificação propõe; o coordenador confirma a decisão e registra a transição. QA não repete checagens determinísticas aprovadas.

Para tarefas locais, delimitadas e somente de leitura, prefira `python3 tools/agent_exec.py ROLE --prompt-file CAMINHO_PRIVADO --job JOB_ID --worker WORKER_ID`. O executor usa o papel TOML e invoca `codex exec` com modelo (`-m`) e esforço (`-c`) explícitos; depois identifica o rollout e verifica `turn_context`. Falha fechado se o modelo/esforço observado divergir. O arquivo de prompt deve ficar em área privada, fora do Git, e conter apenas o contexto necessário. O resultado inclui thread, modelo, esforço e usage apenas quando a sessão o fornecer; com job e worker, registra os metadados verificados na etapa ativa. Não estima tokens nem custo. Não execute tarefas reais com este helper em testes.

Para spawn interativo genérico, passe `fork_turns="none"` e os parâmetros efetivos: `model="gpt-6-luna", reasoning_effort="low"` para descoberta/verificação; `model="gpt-6-luna", reasoning_effort="medium"` para qualificação; `model="gpt-6-sol", reasoning_effort="medium"` para revisão visual/editorial complexa. Passe o papel no objetivo/instrução, sem presumir que `task_name="discovery"` selecione o papel TOML. Confira `turn_context.model` e `turn_context.effort` no rollout. Sol/high exige exceção concreta, motivo registrado e conferência de metadados. As definições TOML são defaults para clientes compatíveis, não garantia de roteamento em spawn genérico.

Conflito factual, identidade ambígua, evidência insuficiente ou falha de qualidade relevante retorna ao coordenador com justificativa registrada. O coordenador escolhe entre nova fonte, revisão humana, `D_pendente` ou bloqueio; não repete a mesma busca indefinidamente. `quality_review` com esforço `high` requer motivo concreto e execução explícita com configuração temporária verificada. Não atribua esforço alto automaticamente.

## Concorrência e ledger

As dimensões de concorrência são independentes: até quatro empresas por lote (configuração `max_concurrent_businesses`); subagentes até o limite global configurado pelo Codex; e operações externas sujeitas aos limites próprios de cada serviço. O projeto não fixa `max_concurrent_threads_per_session`, para não substituir o teto global do operador. `scouting.max_concurrent_business_scrapes` limita scraping externo a dois; `deployment.max_concurrent_deployments` limita deploy a um por vez. Se paralelismo de empresas ou o suporte do backend não estiver disponível, use execução sequencial. Paralelize apenas empresas independentes e respeite dependências dentro de cada empresa. Um job tem um único owner. Somente o coordenador, ou o worker que ele designar conforme [PROSPECCAO.md](PROSPECCAO.md), executa `claim`, `update`, `recover` e transições no SQLite, respeitando locks e estágio atual. Não há concorrência de escrita no mesmo job. Descartar um subagente não descarta o job.

`settings.json:requested_workers` está presente no arquivo, mas não tem consumidor no código atual (busca `rg` no repositório). Seu valor 5 é mantido por compatibilidade; não o interprete como quantidade de empresas ou subagentes. `max_concurrent_businesses`, scraping externo e deploy são controles distintos.

## Ativação e fallback

1. Abra o repositório como projeto confiável. O Codex só carrega `.codex/config.toml` de projetos confiáveis; aqui ele define Sol/medium para o coordenador e Luna/low como padrão de subagente. O teto de subagentes permanece sob controle da configuração global Codex.
2. Confira `codex --version` e `codex debug models`; confirme os IDs desejados por uma execução curta, pois o catálogo local pode omitir um modelo aceito pela conta.
3. Inicie nova sessão Codex na raiz do repositório e peça uma tarefa delimitada com os parâmetros explícitos acima. Inspecione o modelo e o esforço nos metadados da sessão antes de afirmar que o roteamento foi aplicado.
4. Se Luna estiver indisponível, o coordenador Sol executa a tarefa diretamente e registra o fallback. Se Sol estiver indisponível, suspenda classificação/QA e solicite seleção explícita de outro modelo; não troque silenciosamente para a família 5.6. Atualize os TOML somente após confirmar o novo ID e esforço em execução real.

Precedência documentada: flags/`--config` > configuração do projeto confiável > perfil > configuração do usuário > padrões gerenciados/sistema. Para papéis **quando selecionados como papéis personalizados**, `model` e `model_reasoning_effort` no arquivo prevalecem sobre parâmetros de spawn e defaults de `[agents]`. As declarações `agents.<name>.config_file` apontam para arquivos relativos ao `.codex/config.toml`. Arquivos em `.codex/agents/` também são descobertos como papéis personalizados pela documentação atual, mas o spawn genérico exposto neste CLI registrou `agent_role: null`. Uma sessão já aberta pode precisar ser reiniciada para reler a configuração.

## Compatibilidade e medição

Ambiente auditado: `codex-cli 0.155.0`. O catálogo autenticado listou a família 5.6, mas omitiu `gpt-6-luna` e `gpt-6-sol`, ambos aceitos por esta conta no coordenador e em subagentes com esforço `low`/`medium`. `gpt-6.1-sol` foi recusado. A configuração global selecionava `gpt-6-sol`/`medium`, sem alteração. Teste de sessão mostrou filho genérico herdando Sol/medium apesar dos TOML e defaults; parâmetros explícitos rotearam Luna/low e Sol/medium. A configuração de papéis foi ajustada para Luna/medium em qualificação. `settings.json` ainda contém `worker_model`/`worker_reasoning_effort` como compatibilidade, agora Luna/low; esses campos não têm consumidor identificado no código atual. Referências antigas a GPT-5.6 Terra foram removidas desta configuração. Não há dependência de Ultra: modelo, esforço e quantidade de subagentes são controles separados. A documentação oficial confirma as chaves de `[agents]`, arquivos de papéis e configuração por projeto, sujeita a trust. Ver [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference) e [Config basics](https://learn.chatgpt.com/docs/config-file/config-basic).

O benchmark curto com dados fictícios e limites de medição está em [MODEL-ROUTING-BENCHMARK.md](MODEL-ROUTING-BENCHMARK.md). Não interprete diferença de modelo como economia comprovada sem tokens e duração de execuções comparáveis.
