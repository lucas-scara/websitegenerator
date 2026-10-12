# Benchmark curto de roteamento — 2026-10-12

Caso inteiramente fictício: Empresa Farol em Bauru, nome e telefone na fonte A, telefone na fonte B, nenhuma URL de site verificada, e-mail não pesquisado; prévia contém serviço de telhados sem evidência e formulário ativo. As quatro tarefas representativas foram descoberta, verificação, qualificação A/B/C/D e QA factual. Nenhum dado real, prospecção, contato, deploy ou escrita no SQLite foi usado.

| Execução | Modelo/esforço observados | Subagentes | Tokens entrada/saída | Duração | Critérios de qualidade |
| --- | --- | --- | --- | --- | --- |
| Direta, sem delegação | Coordenador `gpt-5.6-sol`/`medium` | 0 | 19.350 / 363 (6.016 entrada em cache) | 10,2 s | Preservou URL não verificada e reprovou QA; classificou A sem evidência suficiente |
| Configuração de papéis, pedido de quatro delegações | Coordenador `gpt-5.6-sol`/`medium`; modelos dos filhos não auditáveis porque a sessão foi efêmera | 4 solicitados; sem metadados individuais | 140.727 / 911 (119.168 entrada em cache) | 27,0 s | Separou URL/e-mail desconhecidos, propôs B e reprovou QA |
| Smoke persistido, `discovery` pelo nome | Pai `gpt-5.6-sol`/`medium`; filho **`gpt-5.6-sol`/`medium`** | 1 | 60.160 / 143 agregados; filho 19.945 / 73 | 9,5 s | JSON extraído; roteamento de TOML **não aplicado** (`agent_role: null`) |
| Smoke persistido, filho genérico sem parâmetros | Pai `gpt-5.6-sol`/`medium`; filho **`gpt-5.6-sol`/`medium`** | 1 | 60.336 / 122 agregados | 9,1 s | Default Luna/low de `[agents]` **não aplicado** |
| Smoke persistido, spawn explícito | Pai `gpt-5.6-sol`/`medium`; filho **`gpt-5.6-luna`/`low`** | 1 | 54.084 / 111 agregados | 9,8 s | Roteamento efetivo confirmado em `turn_context` do filho |
| Smoke persistido, preferência Luna 6 explícita | Pai `gpt-5.6-sol`/`medium`; filho **`gpt-6-luna`/`low`** | 1 | 60.396 / 151 agregados | 11,1 s | Roteamento efetivo confirmado em `turn_context` do filho |
| Smoke persistido, Sol 6 explícito | Pai **`gpt-6-sol`/`medium`**; filho **`gpt-6-sol`/`medium`** | 1 | 61.587 / 133 agregados | 10,4 s | Roteamento efetivo confirmado em `turn_context` do filho |
| Configuração final do projeto, sem `-m` | Coordenador **`gpt-6-sol`/`medium`** | 0 | 20.376 / 6 | 5,0 s | `turn_context` confirma a precedência do TOML local |

Os tokens são os campos `usage` das sessões CLI, não valores monetários. A entrada agrega cache e overhead de contexto; não é uma medição de custo por modelo. As execuções não são amostras estatísticas, e o segundo caso não confirma modelos individuais. **Não foi demonstrada economia de tokens nem de tempo** para o fluxo delegado; neste caso curto, houve aumento. O teste explícito prova apenas que este CLI aceita escolher Luna/low por subagente. Não extrapole para lotes reais.

Disponibilidade: chamada direta a `gpt-6.1-sol`/`medium` recebeu HTTP 400 (`model is not supported when using Codex with a ChatGPT account`). Chamadas a `gpt-6-luna`/`low` e `gpt-6-sol`/`medium` concluíram, e os smokes persistidos confirmaram os modelos nos filhos, apesar de os IDs não aparecerem em `codex debug models`. Assim, a ausência no catálogo isoladamente não determina indisponibilidade. A política final usa somente modelos GPT-6; os testes com 5.6 são a linha de comparação anterior.

Critérios usados: não afirmar ausência de site sem pesquisa, distinguir e-mail não pesquisado, não aceitar serviço sem evidência, bloquear formulário ativo de prévia e justificar categoria sem score. A primeira classificação A ficou acima do que as evidências fictícias sustentavam; as demais avaliações ficaram mais prudentes, mas não substituem revisão humana nem o procedimento oficial.

Comandos de verificação: `codex --version`; `codex debug models`; `codex exec --strict-config --json --sandbox read-only ...`; leitura restrita dos campos `session_meta.source` e `turn_context.model`/`effort` dos rollouts dos testes. Os cinco TOML passaram por `tomllib` do Python 3.12 e o CLI aceitou a configuração em modo estrito. `python3 -m unittest tests/test_control.py` passou com banco temporário. `codex doctor` carregou a configuração, mas apontou integridade do banco interno de estado do CLI e limitações de conectividade; nenhum arquivo global foi alterado manualmente.
