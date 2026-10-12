# Coordenação e ledger

A fonte principal do procedimento é [PROSPECCAO.md](../docs/workflows/PROSPECCAO.md). O dashboard apenas registra o lote. O Codex é o coordenador; `tools/control.py` fornece reservas de identidade, ownership e estados persistentes. Use `REVAMP_DB` somente para testes. Não execute `clear-all` no banco real.

`claim` é atômico. Use o worker retornado em `update`. `recover` requer confirmação de que o worker anterior parou; tentativas de contato incertas nunca podem ser repetidas. Histórico de contato permanece no ledger, mas não é parte da meta de prévias. A meta exige URL HTTPS, QA aprovado, deployment no projeto `scarasoft-previas` e `preview_verified:true`; `preview-finish` libera o worker. `batch-status complete` requer meta atingida, nenhum worker ativo e nenhuma prévia em produção, podendo manter candidatos ainda não avaliados. Veja comandos, formatos e critérios no procedimento oficial.

O schema usa `PRAGMA user_version=2`. Uma conexão normal mantém `foreign_keys=ON`. Quando encontra schema antigo, o ledger reconstrói `jobs` numa única transação, verifica integridade e referências antes de confirmar a versão. Testes de migração usam apenas bancos descartáveis ou cópia obtida em modo somente leitura; nunca reinicialize o SQLite real para testar.
