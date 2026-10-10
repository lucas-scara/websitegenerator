# Evidências do MVP Brasil

## F0 — configuração e segurança mínima

- Branch `feat/br-mvp` sincronizada com `origin/feat/br-mvp` antes das alterações (`git rev-list --left-right --count`: `0 0`). Nenhum trabalho na `main`.
- Patch do proprietário em `~/Downloads/websitegenerator-br-mvp.patch` já está aplicado no commit `ba0d617`; cópia anexada idêntica. Não foi reaplicado.
- Autoria local verificada por `git var GIT_AUTHOR_IDENT` e `GIT_COMMITTER_IDENT`: Lucas Scaranello `<lucasscaranello@gmail.com>`.
- `settings.json` remove escopo Vercel e contatos do autor original, desliga envio padrão e define assinatura aprovada. Contatos comerciais continuam vazios por falta de configuração aprovada.
- `contact-begin` exige autorização local com lote, segmento, cidade e volume exatos, além de e-mail/telefone comerciais. Sem esse arquivo, nenhuma tentativa é reservada. Uma tentativa continua não repetível.
- Scripts npm que executavam o prerender legado foram removidos. O caminho rápido continua usando `vite build` preparado.
- Testes do ledger passaram, inclusive negação sem autorização e escopo divergente. A suíte completa apontou apenas build preparado desatualizado após mudança no template; recompilar na F1.
- Nenhuma campanha, formulário comercial ou deploy foi executado nesta fase.

## Dependências para fases externas

- Lucas: e-mail e telefone/WhatsApp comerciais; cidade do piloto; autorização nominal/escopo de lote para envio real.
- Integrações: escopo/conta Vercel e chave Firecrawl, configurados localmente, sem versionar segredos.
