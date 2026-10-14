# Envio comercial por Gmail

O envio usa a mensagem e o canal preparados automaticamente quando a prévia é finalizada com sucesso. O operador revisa o lote no dashboard e uma aprovação explícita dos destinatários selecionados cria a autorização; a mesma ação inicia o despacho sequencial. Nenhum envio ocorre antes dessa aprovação. `gmail-simulate` continua disponível para diagnóstico, mas não é uma etapa obrigatória do primeiro piloto real. Não execute lote real nem envie e-mail durante desenvolvimento ou testes.

## Configuração local

1. Faça backup de `data/revamp.sqlite3` antes de iniciar esta versão; as migrações 4 → 5 → 6 adicionam campos e índices a `commercial_attempts`, preservando `submissions`, jobs e tentativas anteriores.
2. Instale `python3 -m pip install -r requirements-gmail.txt` no ambiente local. `google-auth` valida e renova credenciais OAuth; `google-auth-oauthlib` abre o fluxo OAuth de aplicativo instalado. O HTTP usa o transporte do `google-auth` e o módulo `email` da biblioteca padrão. Não é necessário cliente de descoberta do Google.
3. No Google Cloud, habilite a Gmail API, configure a tela de consentimento OAuth e crie um cliente OAuth do tipo **Desktop app**. Guarde o JSON baixado em `data/gmail-oauth-client.json` e rode `chmod 600 data/gmail-oauth-client.json`. Configure o usuário de teste quando o app estiver em modo de teste. O consentimento pede `gmail.send` para envio, `openid` e `https://www.googleapis.com/auth/userinfo.email` para confirmar a identidade da conta. Nenhum escopo de leitura do Gmail é solicitado.
4. Execute `python3 tools/control.py gmail-auth` localmente, autentique a conta Google aprovada e confirme que `data/gmail-token.json` tem permissão 600. Esse comando **não** autoriza envios. Tokens e segredos ficam apenas em `data/`, ignorado pelo Git.
5. Configure `BR_COMMERCIAL_EMAIL=contato@scarasoft.com.br` no `.env` local, como exigido pelo motor comercial. A assinatura pública é Lucas Scaranello, scarasoft e esse e-mail; nenhum telefone pessoal entra na mensagem. O remetente Gmail é configurado separadamente.

No teste local de autenticação, o escopo abreviado `email` provocou `Scope has changed` em `requests-oauthlib` durante a troca do código OAuth pelo token: o Google devolveu `https://www.googleapis.com/auth/userinfo.email`. O código usa agora essa forma completa em `SCOPES` para que os escopos solicitados e retornados coincidam. O teste de regressão impede a reintrodução de `email` abreviado. Não edite o token ou os segredos para aplicar essa correção; execute o fluxo `gmail-auth` novamente somente se a autenticação local exigir um novo consentimento.

## Remetente e domínio

O remetente aprovado para este fluxo é **`scarasoftbauru@gmail.com`**, autenticado como a própria conta Google no OAuth. O backend exige coincidência exata entre o remetente autorizado, `oauth_email` e o e-mail verificado pelo Google. Não use `contato@scarasoft.com.br` no cabeçalho `From` deste fluxo.

`contato@scarasoft.com.br` continua sendo o endereço comercial divulgado na assinatura e recebe mensagens por encaminhamento do Cloudflare Email Routing. Todos os e-mails iniciais e follow-ups incluem `Reply-To: contato@scarasoft.com.br`, para que as respostas sejam encaminhadas pela rota configurada. Isso não habilita envio a partir dele; `From` e a conta autenticada continuam sendo `scarasoftbauru@gmail.com`. O operador deve acompanhar a caixa de destino do encaminhamento para respostas e pedidos de exclusão.

Se no futuro for aprovado o envio com `From` no domínio `scarasoft.com.br`, confira SPF, DKIM e DMARC e o alinhamento com o provedor de saída. Exemplos: `dig TXT scarasoft.com.br`, `dig TXT _dmarc.scarasoft.com.br` e o seletor DKIM informado pelo provedor (`dig TXT SELECTOR._domainkey.scarasoft.com.br`). Cloudflare Email Routing cobre recebimento, não autentica por si só a saída. Documente a verificação privada em `runs/`.

Consulta DNS pública em 2026-10-12: SPF `v=spf1 include:_spf.mx.cloudflare.net ~all`; DMARC `v=DMARC1; p=reject;`. O seletor DKIM e o provedor de saída do domínio ainda não foram confirmados. Esses registros **não demonstram** que um envio via Gmail com `From: contato@scarasoft.com.br` passaria no alinhamento DMARC. Isso não impede o envio como `scarasoftbauru@gmail.com`, sujeito às verificações da própria conta Google.

Após autenticar a conta Gmail aprovada, crie `data/gmail-sender.json` com permissão 600:

```json
{"oauth_email":"scarasoftbauru@gmail.com","sender":"scarasoftbauru@gmail.com"}
```

`gmail.send` não permite consultar o perfil Gmail. O backend compara a identidade verificada pelo endpoint OAuth UserInfo com o remetente aprovado. Se qualquer etapa faltar, o envio live permanece desabilitado.

## Revisão e aprovação do lote

No dashboard, abra a visão comercial do lote e confira empresa, segmento, oportunidade, URL HTTPS, destinatário, assunto, mensagem, canal, elegibilidade e impedimentos. Selecione os contatos elegíveis desejados; apenas canal `email` pode entrar no despacho Gmail. Formulário elegível mantém prioridade e WhatsApp fica manual. Contatos sem e-mail elegível continuam pendentes, sem roteamento alternativo automático.

Confira a capacidade apresentada antes de aprovar: tentativas anteriores do mesmo lote são acumuladas no limite de contatos, enquanto o limite diário global de 5 considera todos os lotes. A aprovação informa quantos novos envios cabem agora. Ao clicar **Aprovar seleção e iniciar envio**, o backend valida novamente remetente, seleção, elegibilidade e capacidade e grava `data/gmail-authorization.json` com permissão 600, validade de 24 horas, IDs selecionados e resumo dos dados revisados. A autorização não é criada pela conclusão da produção. Se destinatário, canal, conteúdo ou prévia mudar depois da aprovação, os dados não coincidem com a revisão e o envio é bloqueado até nova validação e aprovação.

O botão inicia o despacho sequencial. O backend revalida cada contato imediatamente antes do envio, aplica os limites e registra tentativa e resultado. Uma autorização ativa com contatos pendentes não pode ser substituída por outra aprovação, mesmo após reiniciar o dashboard. Na retomada, contatos com tentativa existente não são reenviados; `attempting` e `uncertain` exigem reconciliação, enquanto contatos aprovados sem tentativa podem seguir sequencialmente. Ao concluir todos os contatos com resultado definido, o backend fecha a autorização. Falha inesperada pausa o despacho, registra a falha operacional e impede retomada automática. Cada mensagem tem um destinatário, corpo UTF-8 e não contém CC, BCC ou anexos. O e-mail inicial tem versão HTML com o texto clicável **Ver a prévia do site** e versão texto simples com a URL explícita como fallback para leitores sem HTML.

`python3 tools/control.py gmail-simulate --job ID` permanece disponível para diagnóstico sem reservar tentativa nem usar Gmail. Não substitui a revisão ou aprovação explícita e não é obrigatório antes do primeiro piloto real.

## Acompanhamento

O dashboard mostra a data do primeiro envio confirmado e os marcos de **dia 4** e **dia 10**. A data é calculada em UTC a partir da tentativa inicial. Não existe agendamento, envio automático nem notificação externa. Quando o dia chega, o operador revisa a mensagem e aciona **Enviar follow-up na mesma conversa**. Como a autorização do despacho inicial é encerrada ao fim do lote, cada follow-up exige autorização local válida novamente pelo mecanismo existente. O backend exige empresa selecionada, limite diário, ausência de resposta/recusa e confirmação da etapa anterior. O máximo de contatos do lote conta empresas no primeiro envio; o limite diário conta todos os envios, inclusive follow-ups.

```sh
python3 tools/control.py gmail-followup --job ID --touch 1  # dia 4
python3 tools/control.py gmail-followup --job ID --touch 2  # dia 10
```

O primeiro envio armazena um `Message-ID` RFC, além de `gmail_message_id` e `gmail_thread_id`. Os follow-ups usam o mesmo assunto, `threadId`, `In-Reply-To` e `References`; se o Gmail confirmar outra conversa, o próximo contato fica bloqueado para revisão manual. Envios anteriores a esta versão sem `Message-ID` RFC não podem ser respondidos automaticamente na mesma conversa com o escopo `gmail.send`; faça o acompanhamento manualmente no Gmail. Resposta, interesse, falta de interesse e opt-out registrados no histórico encerram a sequência. O sistema não lê respostas automaticamente, pois isso exigiria escopo adicional de leitura; registre-as no dashboard.

## Verificação e reconciliação

Consulte `python3 tools/control.py state` e o histórico comercial no dashboard. Cada tentativa Gmail contém destinatário, remetente, assunto, data/hora, resultado, motivo, `gmail_message_id` e `gmail_thread_id` quando retornados. Não compartilhe o snapshot completo fora do ambiente privado, pois ele contém prospectos e mensagens. Erros 401/403/429 rejeitados pelo Gmail ficam `failed_no_send`; confira token, cota e configuração, sem interpretar cota técnica como consentimento comercial. Timeout, conexão perdida, resposta 5xx ou confirmação sem ID ficam `uncertain`; uma interrupção pode deixar `attempting`, igualmente bloqueante. Não há repetição automática.

Após investigar uma tentativa `uncertain` ou `attempting` na conta Gmail, reconcilie somente com evidência explícita:

```sh
python3 tools/control.py gmail-reconcile --attempt ID --status sent --message-id ID_GMAIL --thread-id THREAD_GMAIL --evidence 'Confirmação observada na conta Gmail em data/hora'
python3 tools/control.py gmail-reconcile --attempt ID --status failed_no_send --evidence 'Não envio confirmado por investigação documentada'
```

A reconciliação não dispara e-mail. Mesmo `failed_no_send` permanece no histórico e o motor de preparação segue sua regra de próximo canal. Para opt-out, registre `commercial-record --status opted_out` com evidência. Uma recusa impede novos envios.
