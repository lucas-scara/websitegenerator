# Contato comercial: simulação por padrão

O fork brasileiro não herda qualquer autorização de envio do autor original. Antes de um contato real, Lucas precisa autorizar um lote específico (segmento, cidade e volume), definir e-mail e telefone comerciais e aprovar a mensagem final. Até lá, prepare o texto e os campos em simulação, sem clicar em Enviar. O dashboard apenas registra e exibe dados; não envia mensagens.

## Mensagem base em pt-BR

Assunto, se necessário: `Prévia de site para [Empresa]`

> Olá! Sou Lucas Scaranello, da scarasoft. Preparei uma prévia de site para [Empresa] com base nas informações públicas do seu negócio.
>
> Você pode avaliá-la aqui: [URL pública verificada]
>
> Se houver interesse em conversar sobre o projeto, responda pelo contato comercial [e-mail comercial] ou [telefone comercial].
>
> scarasoft — Lucas Scaranello

Use apenas nome da empresa, prévia e contatos verificados. Não prometa preço, gratuidade, hospedagem, resultados ou disponibilidade. Não descreva o site atual como antigo, nem simule um pedido de serviço. A assinatura já foi aprovada; o e-mail e telefone comerciais ainda precisam ser definidos pelo responsável.

## Verificação antes da abordagem

Confirme no site original um formulário com campo de mensagem e botão de envio, adequado a uma proposta comercial. Guarde a URL e os campos observados. Links de e-mail/telefone, formulários de newsletter, avaliação de cliente ou solicitação de orçamento de serviço não são elegíveis. Respeite avisos de não solicitação e opt-out. CAPTCHA visível e campos que exigem fatos ou compromissos não verificados levam ao [fallback manual](manual-outreach.md). Não contorne bloqueios nem marque consentimentos opcionais.

Reabra o formulário antes de preencher. Use nome completo Lucas Scaranello e somente e-mail/telefone comerciais configurados localmente. Nunca use o e-mail do commit como substituto automático. Salve a mensagem exata em `runs/JOB_ID/outreach.txt` e confira remetente, URL pública, formulário e prévia antes de qualquer ação de envio.

Para registrar um formulário elegível **sem envio**, use `python3 tools/control.py contact-simulate --job JOB_ID --worker WORKER_ID --message-file runs/JOB_ID/outreach.txt --form-url 'https://empresa.example/contato'`. O job termina como `simulated`, conserva a mensagem e a URL, e não cria reserva em `submissions`. Não clique no botão de envio. Um lote futuro autorizado precisa de um novo job, com identidade/histórico conciliados pelo responsável; não recicle o job simulado automaticamente.

## Autorização técnica e tentativa única

`contact-begin` falha por padrão. Para um lote expressamente autorizado por Lucas, registre localmente `data/outreach-authorization.json` (ignorado pelo Git) com `mode: "live"`, `approved_by: "Lucas Scaranello"`, `batch_id`, `industry`, `city` e `max_contacts` iguais ao escopo aprovado. Configure `BR_COMMERCIAL_EMAIL` e `BR_COMMERCIAL_PHONE` no ambiente local. O comando confere o lote, escopo, limite, assinatura e contatos da mensagem antes de reservar a tentativa. O arquivo técnico não substitui a autorização humana.

```sh
python3 tools/control.py contact-begin --job JOB_ID --worker WORKER_ID --message-file runs/JOB_ID/outreach.txt --form-url 'https://empresa.example/contato'
```

Somente depois de uma reserva válida e da autorização específica, clique em Enviar **uma vez**. Registre exatamente o resultado observado:

```sh
python3 tools/control.py contact-finish --job JOB_ID --worker WORKER_ID --status submitted --evidence 'Clique único; confirmação observada ...'
```

`submitted` indica ação de envio, não entrega confirmada. Se houver dúvida sobre o clique ou resultado, use `uncertain` e nunca tente novamente. Se for certo que nenhum clique ocorreu após a reserva, use `blocked`; a reserva continua registrada. Quando não houver formulário elegível antes da reserva, use `manual-outreach`, sem marcar como enviada. Não troque para e-mail, SMS ou WhatsApp automaticamente.
