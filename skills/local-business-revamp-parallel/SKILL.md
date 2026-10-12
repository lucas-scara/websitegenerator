---
name: local-business-revamp-parallel
description: Distribuir trabalho entre agentes quando um lote de prévias da scarasoft precisar de execução paralela.
---

# Coordenação paralela

Leia [AGENTS.md](../../AGENTS.md) e [o procedimento oficial](../../docs/workflows/PROSPECCAO.md). O Codex continua coordenador. Distribua empresas distintas a agentes disponíveis, com worker IDs distintos no ledger. `claim` evita processamento simultâneo da mesma empresa. Cada agente registra fontes, datas e evidências privadas no seu `runs/JOB_ID/`, atualiza somente o job que possui e devolve URL pública verificada ou pendência objetiva. O coordenador reconcilia meta, histórico e workers antes de concluir o lote. Não realize contato comercial.
