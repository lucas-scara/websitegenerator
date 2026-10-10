# Evidências do MVP Brasil

## F0 — configuração e segurança mínima

- Branch `feat/br-mvp` sincronizada com `origin/feat/br-mvp` antes das alterações (`git rev-list --left-right --count`: `0 0`). Nenhum trabalho na `main`.
- Patch do proprietário em `~/Downloads/websitegenerator-br-mvp.patch` já está aplicado no commit `ba0d617`; cópia anexada idêntica. Não foi reaplicado.
- Autoria local verificada por `git var GIT_AUTHOR_IDENT` e `GIT_COMMITTER_IDENT`: Lucas Scaranello `<lucasscaranello@gmail.com>`.
- `settings.json` removeu o escopo Vercel e os contatos do autor original na F0, desligou o envio padrão e definiu a assinatura aprovada. O escopo de Lucas foi identificado e configurado na F2; os contatos comerciais continuam vazios.
- `contact-begin` exige autorização local com lote, segmento, cidade e volume exatos, além de e-mail/telefone comerciais. Sem esse arquivo, nenhuma tentativa é reservada. Uma tentativa continua não repetível.
- Scripts npm que executavam o prerender legado foram removidos. O caminho rápido continua usando `vite build` preparado.
- Testes do ledger passaram, inclusive negação sem autorização e escopo divergente. A suíte completa apontou apenas build preparado desatualizado após mudança no template; recompilar na F1.
- Nenhuma campanha, formulário comercial ou deploy foi executado nesta fase.

## Dependências para fases externas

- Lucas: e-mail e telefone/WhatsApp comerciais; cidade do piloto; autorização nominal/escopo de lote para envio real.
- Integrações: escopo/conta Vercel e chave Firecrawl, configurados localmente, sem versionar segredos.

## F1 — localização e prévia local

- Dashboard aberto em `http://127.0.0.1:4310/` no navegador local: formulário e estados em pt-BR, fila visível, sem execução automática.
- Template `electrician` traduzido em páginas, navegação, formulário demonstrativo, textos de serviços e metadados (`lang=pt-BR`, `og:locale=pt_BR`); rotas técnicas existentes preservadas.
- `python3 tools/quick_site.py prepare --template electrician`: lint e build passaram. Avisos do linter são não bloqueadores; o bundle principal segue acima de 500 kB, como no desenho existente.
- `./website` gerou cópia fictícia “Elétrica Exemplo Brasil” com telefone +55, CEP e cidade São Paulo em aproximadamente 0,12 s. A prévia local abriu em tela estreita, com contatos e rota `/electrical-installation` corretos.
- Teste local do formulário demonstrativo com dados fictícios exibiu “Nenhuma mensagem foi enviada”. Não houve requisição comercial externa.
- Suíte Python: 40 testes passaram após preparar o template. `node --check dashboard/app.js` e `git diff --check` passaram.

## F2 — pré-condições de integração

- Vercel CLI 59.16.0: `whoami` retornou `lucasscaranello-3315`; `teams ls` listou `lucasscaranello-3315s-projects`. O escopo foi configurado em `settings.json`, sem criar projeto nem realizar deploy.
- Firecrawl: nenhuma chave em `.env` ou no processo; prospecção via Firecrawl ainda não foi executada.
- Contatos comerciais e autorização do lote: ausentes. `contact-begin` permanece bloqueado. A simulação local do ledger é coberta por teste, sem registro em `submissions`.
