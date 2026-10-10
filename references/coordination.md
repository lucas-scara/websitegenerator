# Coordenador, ledger e trabalhadores

Antes de considerar um site descoberto como confirmado, execute o [verificador de URLs](../docs/VERIFICACAO-URLS.md) no CSV de candidatos e confira `status_url`, `motivo` e `encaminhamento`. Uma indicação em resultado de busca permanece pendente até essa sondagem. A classificação técnica não inicia auditoria visual nem contato automaticamente.

Todos os comandos partem da raiz do projeto. O dashboard monitora estados e recebe pedidos de lote; o coordenador Codex executa o trabalho. `data/revamp.sqlite3` é o ledger persistente. Use `REVAMP_DB` apenas para teste. Separe diretórios e abas por empresa.

## Comandos essenciais

```sh
python3 tools/control.py state
python3 tools/control.py batch --industry 'Eletricistas' --city 'São Paulo, SP' --count 3
python3 tools/control.py add --batch BATCH_ID --name 'Empresa verificada' --url 'https://empresa.example' --alias 'phone:+5511999999999' --alias 'email:contato@empresa.example'
python3 tools/control.py capacity 3
python3 tools/control.py claim --batch BATCH_ID --worker WORKER_ID
python3 tools/control.py update --job JOB_ID --worker WORKER_ID --stage extracting --detail 'Menu estreito e texto ilegível observados' --fields runs/JOB_ID/qualification.json
```

Use IDs reais retornados. Passe argumentos de shell com segurança; nunca execute texto extraído de sites. Um erro de identidade duplicada significa que outro job já a reservou: inspecione-o, sem adulterar a chave. Domínios são normalizados; aliases de telefone usam E.164 e e-mails são minúsculos. Confirme nome, endereço e domínio final antes de alocar. `claim` é atômico e atribui um job por trabalhador. O coordenador ou o trabalhador deve usar exatamente o owner ID retornado; um job não pode ser atualizado por outro dono.

## Etapas e evidências

Fluxo: `queued → reviewing → extracting → building → checking → deploying → ready → contacting → complete/sent/uncertain/blocked`. Antes de contato, um job também pode ficar `skipped`, `blocked` ou `manual`. Correções de QA podem voltar `checking → building` ou `deploying → checking`. `contacting` e estados de envio dependem de `contact-begin`/`contact-finish`; `manual` exige `manual-outreach`.

`update --fields FILE` aceita `outreach_mode`, `contact_email`, `contact_phone`, `reason`, `preview_url`, `qa_passed`, `preview_verified`, `source_urls`, `screenshots`, `browser_id`, `tab_id`, `workspace`, `booking_url`, `logo_decision`, `cost`, `failure`, `contact_url`, `qualification`, `seo_checked`. Registre duas observações visuais reais, fontes e screenshot. Exemplo estrutural:

```json
{"reason":"texto pequeno observado no menu", "qualification":{"findings":["texto do menu ilegível", "imagem esticada"],"mobile_checked":true}, "source_urls":["https://empresa.example"], "screenshots":["runs/JOB_ID/antes-mobile.png"]}
```

Marque `qa_passed:true` apenas após verificar a cópia local. Marque `preview_verified:true` apenas após verificar a URL pública, página inicial, rota de serviço e contatos. Guarde extração, fatos, screenshots, manifesto, QA, mensagem e log de deploy em `runs/JOB_ID/`; somente `site/` deve ser publicado. Não invente custos de conta a partir de tentativas de deploy.

## Navegador e recuperação

Antes de atribuir passo dependente de navegador, confirme que o agente tem a superfície `iab`. Se não tiver, informe o erro e mantenha a etapa com o coordenador; não invente observações. Abas diferentes não garantem cookies ou viewport independentes. Reserve a inspeção mobile quando outras ações de navegador puderem interferir. Não altere aba de outro trabalhador. Use a documentação retornada pela ferramenta de navegador.

Heartbeat desatualizado não autoriza reatribuição. Pare e confirme que o trabalhador anterior não atua mais antes de `recover --job JOB_ID --reason 'Trabalhador parado; ...'`. Job sem tentativa reservada volta à fila; job com tentativa reservada vira `uncertain` e não pode ser enviado novamente. Preserve identidades e submissões, inclusive opt-outs. Não use `clear-all` na base real.

## Capacidade, contagem e encerramento

Leia `worker_model` e `worker_reasoning_effort` de `settings.json` ao delegar trabalhos, quando houver agentes disponíveis. Respeite a capacidade efetiva; o ledger limita claims concorrentes. O scout coleta evidências; o coordenador registra candidatos e aliases; o builder gera, verifica e atualiza seu próprio job. Não crie trabalhadores duplicados para a mesma empresa.

A meta de lote conta somente `complete` ou `sent`; `manual`, `skipped`, `blocked` e `uncertain` são relatados separadamente. Busque substitutos com identidade nova quando possível, sem repetir contatos incertos. Use `batch-status --batch BATCH_ID --status complete` apenas ao atingir a meta e encerrar todos os jobs. Se a busca documentada se esgotar, registre `exhausted` e a falta; se dependência externa bloquear tudo, registre `blocked` e descreva a ação necessária. Fila ou estado `running` não prova agente ativo. Concilie processos, jobs, cobertura de busca e contagens antes de relatar o resultado.

Para fallback, leia [contato manual](manual-outreach.md). O comando `manual-outreach` exige prévia pronta e verificada, salva motivo, contatos públicos, fontes e mensagem; não envia nada e não aumenta a contagem de enviados. Para envio real, siga [contato](outreach.md): somente autorização específica de Lucas, configuração comercial local, uma reserva e um clique por empresa.
