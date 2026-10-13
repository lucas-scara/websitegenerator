# Envio comercial por Gmail

O envio usa a mensagem e o canal preparados em `commercial-prepare`. O estado de produção do site não muda. O padrão é `dry_run`: sem autorização privada explícita, `gmail-send` falha antes de reservar tentativa. `gmail-simulate` apenas valida e mostra o plano; nunca chama Gmail.

## Configuração local

1. Faça backup de `data/revamp.sqlite3` antes de iniciar esta versão; a migração 4 → 5 adiciona campos e um índice a `commercial_attempts`, preservando `submissions`, jobs e tentativas anteriores.
2. Instale `python3 -m pip install -r requirements-gmail.txt` no ambiente local. `google-auth` valida e renova credenciais OAuth; `google-auth-oauthlib` abre o fluxo OAuth de aplicativo instalado. O HTTP usa o transporte do `google-auth` e o módulo `email` da biblioteca padrão. Não é necessário cliente de descoberta do Google.
3. No Google Cloud, habilite a Gmail API, configure a tela de consentimento OAuth e crie um cliente OAuth do tipo **Desktop app**. Guarde o JSON baixado em `data/gmail-oauth-client.json` e rode `chmod 600 data/gmail-oauth-client.json`. Configure o usuário de teste quando o app estiver em modo de teste. O consentimento pede `gmail.send` para envio e `openid email` para confirmar a identidade da conta. Nenhum escopo de leitura do Gmail é solicitado.
4. Execute `python3 tools/control.py gmail-auth` localmente, autentique a conta Google aprovada e confirme que `data/gmail-token.json` tem permissão 600. Esse comando **não** autoriza envios. Tokens e segredos ficam apenas em `data/`, ignorado pelo Git.
5. Configure `BR_COMMERCIAL_EMAIL` e `BR_COMMERCIAL_PHONE` no `.env` local, como já exigido pelo motor comercial. Eles identificam a scarasoft na mensagem; o remetente Gmail é configurado separadamente.

## Remetente e domínio

`contato@scarasoft.com.br` recebe pelo Cloudflare Email Routing, mas isso não habilita o envio no Gmail. Antes de autorizar live, configure-o na conta Google em **Configurações → Contas e importação → Enviar e-mail como**, conclua a verificação enviada ao endereço encaminhado e confirme o método de saída/SMTP oferecido pela conta. Faça um teste manual de envio e inspecione o cabeçalho `From` efetivo e a entrega. Não use outro remetente sem aprovação explícita.

Confira os registros SPF, DKIM e DMARC publicados para `scarasoft.com.br` e se o provedor de saída efetivamente usado está autorizado e assina o domínio. Exemplos: `dig TXT scarasoft.com.br`, `dig TXT _dmarc.scarasoft.com.br` e o seletor DKIM informado pelo provedor (`dig TXT SELECTOR._domainkey.scarasoft.com.br`). Cloudflare Email Routing cobre recebimento, não autentica por si só a saída. Documente a verificação privada em `runs/`.

Consulta DNS pública em 2026-10-12: SPF `v=spf1 include:_spf.mx.cloudflare.net ~all`; DMARC `v=DMARC1; p=reject;`. O seletor DKIM e o provedor de saída ainda não foram confirmados. Esses registros **não demonstram** que um envio via Gmail com `From: contato@scarasoft.com.br` passará no alinhamento DMARC. Mantenha `domain_dns_checked` falso/ausente até validar SPF ou DKIM alinhado com o serviço efetivamente usado e inspecionar um envio manual de teste.

Após confirmar conta, alias e DNS, crie `data/gmail-sender.json` com permissão 600:

```json
{"oauth_email":"CONTA_GOOGLE_AUTENTICADA","sender":"contato@scarasoft.com.br","alias_verified":true,"domain_dns_checked":true}
```

`gmail.send` não permite consultar a lista de aliases nem o perfil Gmail. O backend compara a identidade verificada pelo endpoint OAuth UserInfo com `oauth_email` e exige essa confirmação local do alias. Se qualquer etapa faltar, o envio live permanece desabilitado.

## Autorização de um lote

Prepare e revise as mensagens. Formulários comerciais elegíveis continuam tendo prioridade sobre e-mail. Crie `data/gmail-authorization.json` somente depois da aprovação expressa do operador, com permissão 600:

```json
{
  "mode": "live",
  "approved_by": "Lucas Scaranello",
  "approved_at": "2026-10-12T12:00:00Z",
  "batch_id": "batch-ID_REAL",
  "job_ids": ["job-ID_APROVADO"],
  "sender": "contato@scarasoft.com.br",
  "max_contacts": 1,
  "daily_limit": 5
}
```

`job_ids` é a seleção explícita de empresas. `max_contacts` limita tentativas do lote, incluindo falhas anteriores; `daily_limit` limita tentativas em UTC em todos os lotes e vale 5 se omitido. Para simular ou desabilitar, altere `mode` para `dry_run` ou remova o arquivo. O dashboard e a prospecção não criam nem alteram essa autorização. Editar um arquivo local protegido é a aprovação operacional; não há botão no dashboard para aprovar lote.

Execute `python3 tools/control.py gmail-simulate --job ID` para validar sem reservar tentativa. Depois de confirmar os campos no dashboard, use **Enviar via Gmail** ou `python3 tools/control.py gmail-send --job ID`. Ambos aplicam as mesmas verificações no backend. Cada mensagem tem um destinatário, corpo UTF-8 e não contém CC, BCC ou anexos. A mensagem preparada inclui a identidade comercial e instrução de opt-out.

## Verificação e reconciliação

Consulte `python3 tools/control.py state` e o histórico comercial no dashboard. Cada tentativa Gmail contém destinatário, remetente, assunto, data/hora, resultado, motivo, `gmail_message_id` e `gmail_thread_id` quando retornados. Não compartilhe o snapshot completo fora do ambiente privado, pois ele contém prospectos e mensagens. Erros 401/403/429 rejeitados pelo Gmail ficam `failed_no_send`; confira token, cota e configuração, sem interpretar cota técnica como consentimento comercial. Timeout, conexão perdida, resposta 5xx ou confirmação sem ID ficam `uncertain`; uma interrupção pode deixar `attempting`, igualmente bloqueante. Não há repetição automática.

Após investigar uma tentativa `uncertain` ou `attempting` na conta Gmail, reconcilie somente com evidência explícita:

```sh
python3 tools/control.py gmail-reconcile --attempt ID --status sent --message-id ID_GMAIL --evidence 'Confirmação observada na conta Gmail em data/hora'
python3 tools/control.py gmail-reconcile --attempt ID --status failed_no_send --evidence 'Não envio confirmado por investigação documentada'
```

A reconciliação não dispara e-mail. Mesmo `failed_no_send` permanece no histórico e o motor de preparação segue sua regra de próximo canal. Para opt-out, registre `commercial-record --status opted_out` com evidência. Uma recusa impede novos envios.
