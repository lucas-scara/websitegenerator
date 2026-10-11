# Coordenação e ledger

A fonte principal do procedimento é [PROSPECCAO.md](../docs/workflows/PROSPECCAO.md). O dashboard apenas registra o lote. O Codex é o coordenador; `tools/control.py` fornece reservas de identidade, ownership e estados persistentes. Use `REVAMP_DB` somente para testes. Não execute `clear-all` no banco real.

`claim` é atômico. Use o worker retornado em `update`. `recover` requer confirmação de que o worker anterior parou; tentativas de contato incertas nunca podem ser repetidas. Histórico de contato permanece no ledger, mas não é parte da meta de prévias. A meta conta `preview_verified:true` com URL HTTPS; `preview-finish` libera o worker após QA e publicação. `batch-status complete` requer meta atingida e nenhum job ativo. Veja comandos, formatos e critérios no procedimento oficial.
