# Motor comercial determinístico

Esta fase prepara mensagens e permite registrar resultados observados. O envio de e-mail preparado pelo Gmail é opcional e exige a configuração e a autorização local de [ENVIO-GMAIL.md](ENVIO-GMAIL.md). Não envia formulários nem WhatsApp. O lote de prévias continua concluído pela quantidade de URLs públicas verificadas, independentemente do estado comercial.

## Decisões

- `jobs.stage` continua sendo o fluxo legado de produção. `jobs.contact_status` guarda o estado comercial atual; `jobs.data.commercial_contact` guarda a preparação atual. O novo `commercial_attempts` mantém tentativas e mudanças observadas. `submissions` permanece intacta para o histórico de formulários legados; qualquer registro nela bloqueia uma nova preparação automática.
- Canal em ordem: formulário explicitamente elegível para contato comercial, e-mail público, WhatsApp manual confirmado ou presumido por telefone público, ou nenhum canal. A presunção exige número internacional válido, URL pública de origem e data válida de verificação; `whatsapp: false` e `nao_utiliza` a impedem. Formulários de orçamento, suporte e atendimento não são elegíveis. Falha com evidência de que nada foi enviado (`failed_no_send`) libera apenas o próximo canal. `uncertain` impede nova preparação.
- A cópia vem de `tools/commercial.py` e de campos verificados do ledger. Os e-mails usam os modelos de primeiro site, redesign e site inoperante com link nomeado para a prévia; as mensagens curtas dos outros canais mantêm os exemplos ilustrativos de busca por segmento, sem alegar pesquisa de volume ou ranking. `site_inoperante` requer `verification.technical_failure` com `checked_at` nos últimos 14 dias, `source`, `result` e ao menos duas tentativas; a observação usada na mensagem deve corresponder a `result`.
- Uma mensagem preparada exige prévia HTTPS verificada e `BR_COMMERCIAL_EMAIL` válido no `.env`. A assinatura pública contém Lucas Scaranello, scarasoft e `contato@scarasoft.com.br`, sem telefone pessoal. O dashboard lê somente esse e-mail. Os telefones públicos verificados das empresas continuam disponíveis para roteamento e WhatsApp manual. Abrir `wa.me` nunca registra envio. `prepared` não pode virar `replied` ou `interested` diretamente. Envio manual exige comprovante (URL, arquivo em `runs/` ou ID externo). Contato já realizado fora do dashboard é registrado como `sent_external`, com canal, observação e comprovante; o estado atual vira `sent`. Só então respostas e interesse podem ser registrados. Opt-out bloqueia novo contato.
- A migração SQLite 2 → 3 cria `commercial_attempts` de forma transacional. Não modifica nem elimina `submissions`. A base real deve ser copiada por backup antes da primeira execução de uma nova versão, conforme o procedimento operacional existente.

## Uso local

Abra o dashboard, selecione uma prévia verificada e clique em **Preparar mensagem**. Para site inoperante, informe exatamente o resultado técnico já documentado em `verification.technical_failure.result`. Revise o canal, assunto, texto e destinatário. Copie a mensagem ou abra o link de WhatsApp; nenhuma dessas ações altera o status para enviado. Após observar um envio, use **Registrar resultado**, informe a evidência e o comprovante. Para contato externo já realizado, selecione **Contato externo comprovado** e indique o canal usado. Respostas, interesse, falta de interesse e opt-out também são registros manuais. A seção de produção continua mostrando a prévia publicada depois do contato.

CLI equivalente:

```sh
python3 tools/control.py commercial-prepare --job ID
python3 tools/control.py commercial-prepare --job ID --observation 'HTTP 503 em duas sondagens'
python3 tools/control.py commercial-record --job ID --status sent --evidence 'Confirmação observada no canal em data/hora...' --proof 'id:message-12345678'
python3 tools/control.py commercial-record --job ID --status sent_external --channel email --evidence 'Contato externo realizado e observado' --proof 'runs/ID/comprovante.txt'
python3 tools/control.py commercial-record --job ID --status failed_no_send --evidence 'Falha antes de qualquer envio...'
```

Se o destino não tiver canal adequado, a preparação retorna `no_channel` e indica pesquisar contato público. `commercial-prepare` e `commercial-record` não enviam mensagens externas. O envio Gmail exige comando/ação separado e autorização específica. Os comandos legados de envio de formulário seguem com autorização própria do lote e não são usados por este motor.

Mensagens preparadas antes da remoção do telefone podem continuar no SQLite. O dashboard as marca para revisão e oculta cópia, envio Gmail e abertura direta do WhatsApp; o backend também recusa o envio da assinatura antiga. Para uma mensagem ainda não enviada e sem tentativa pendente, incerta ou opt-out, o dashboard oferece **Regenerar mensagem sem telefone**. A ação revalida prévia, contatos, canal e destinatário, usa o modelo atual e registra os hashes da mensagem antiga e da nova em `events`. Ela também está disponível por `python3 tools/control.py commercial-regenerate --job ID`. Tentativas anteriores e mensagens já enviadas não são alteradas. Se o canal ou destinatário mudou, a ação permanece indisponível e o operador deve revisar o caso; não há substituição automática.
