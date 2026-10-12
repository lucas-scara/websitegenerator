---
name: scarasoft-prospeccao
description: Executar lotes de prospecção e prévias comerciais da scarasoft a partir do dashboard.
---

# Workflow scarasoft

Leia [AGENTS.md](AGENTS.md) e [o procedimento oficial](docs/workflows/PROSPECCAO.md). O dashboard enfileira; o Codex consulta `python3 tools/control.py state`, escolhe o lote pendente e coordena descoberta, verificação, qualificação, geração, QA, publicação e atualização do ledger. A meta é o número de prévias públicas verificadas. Contato comercial fica fora desta execução.
