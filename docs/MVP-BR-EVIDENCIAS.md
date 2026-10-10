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

## F2 — simulação e Vercel (resultado observado)

- `contact-simulate` registra mensagem e URL do formulário em `data.contact_simulation`, conclui o job como `simulated` e não grava em `submissions`. Teste cobre ausência de autorização, escopo divergente, simulação sem reserva, retomada somente com autorização específica e tentativa única subsequente.
- O fluxo de geração e navegação da prévia foi testado localmente com dados fictícios; o formulário demonstrativo não enviou mensagem. Triagem real via Firecrawl não foi executada porque a chave não está configurada.
- Projeto Vercel isolado `revamp-br-mvp-demo-20261010` criado com dados fictícios. O comando `vercel deploy --yes` **sem `--prod`** retornou `target: production` por ser o primeiro deploy do projeto, com URL `https://revamp-br-mvp-demo-20261010-idpmutjhx.vercel.app` e alias `https://revamp-br-mvp-demo-20261010.vercel.app`. Isso foi inesperado diante da restrição de não mudar produção; nenhum outro deploy foi feito.
- Visitante sem sessão foi redirecionado ao login Vercel, logo a URL **não é pública para prospecção**. Uma leitura autenticada pelo `vercel curl` retornou HTTP 200 e `X-Robots-Tag: noindex, nofollow`; o comando gerou um token de bypass de proteção no escopo do projeto, sem imprimi-lo. A rota de serviço e formulário foram verificados apenas na cópia local.
- Não foi enviada mensagem comercial. Não foi alterada a proteção da Vercel. A decisão de manter ou remover o projeto de demonstração está pendente do responsável.

## F3 — piloto externo

**Pendente, sem campanha executada.** Ainda faltam cidade autorizada, chave Firecrawl, contatos comerciais e autorização nominal/escopo do lote de 3 eletricistas. Nenhuma empresa real foi qualificada ou contatada. A URL Vercel de demonstração permanece protegida por login e não atende ao gate de prévia pública. Não há evidência de 3 casos reais nem envio real; estes itens do roadmap seguem abertos.

## F4 — regressão e PR

- `python3 -m unittest discover -s tests -q`: 41 testes passaram, incluindo travas de autorização, simulação, deduplicação, fallback manual, reserva única e bloqueio de `clear-all` no ledger durável.
- `python3 tools/quick_site.py prepare --template electrician`: lint e build passaram. Warnings não bloqueadores de React/legado e tamanho de bundle permanecem; não foram expandidos para evitar reforma fora do MVP.
- `node --check dashboard/app.js` e `git diff --check`: passaram.
- Revisão de exposição: nenhuma chave Firecrawl, e-mail comercial real, telefone comercial real ou dados de prospecção foram versionados. O projeto Vercel demonstra apenas identidade fictícia e imagens ilustrativas. O build está com `noindex` e a conta protege a URL.
- Backlog pós-MVP: corrigir prerender legado antes de reativar; tratar warnings de lint/bundle; novos templates somente após piloto validado.

### Reprodução local

```sh
python3 tools/quick_site.py prepare --template electrician
python3 -m unittest discover -s tests -q
./website --template electrician --name 'Elétrica Exemplo' --phone '+55 11 99999-9999' --city 'São Paulo' --zip '01000-000' --theme-color '#2563eb'
python3 tools/control.py serve --port 4310
```

Abra `http://127.0.0.1:4310/` e a URL `/preview/ID/` retornada pelo gerador. O formulário da prévia é demonstrativo. Para contato real, siga `references/outreach.md` após autorização específica, prévia **pública** verificada e contatos comerciais definidos. Não reutilize a URL protegida de demonstração na mensagem.
