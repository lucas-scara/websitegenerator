# Fallback de contato manual

Se a empresa qualificada não tiver formulário comercial adequado, houver CAPTCHA ou o formulário exigir compromisso não autorizado, conclua a prévia e sua verificação pública. Registre o motivo, os contatos divulgados publicamente, suas URLs de origem e a mensagem preparada. Respeite opt-outs: uma recusa expressa não vira fallback. Não invente contatos e não tente outro canal automaticamente.

Após o estado `ready`, salve a mensagem com a URL da prévia em `runs/JOB_ID/outreach.txt` e registre:

```sh
python3 tools/control.py manual-outreach --job JOB_ID --worker WORKER_ID --reason 'Sem formulário comercial adequado' --message-file runs/JOB_ID/outreach.txt --email 'contato@empresa.example' --phone '+5511999999999'
```

Omita `--email` ou `--phone` se não houver valor público verificado. `source_urls` deve conter as fontes. O comando exige prévia verificada, QA, qualificação visual e mensagem preparada; salva `data.manual_outreach`, marca `manual_required` e libera o trabalhador. Ele **não envia** mensagem. Não use `update --stage manual` nem reclassifique uma tentativa já reservada ou resultado incerto. O trabalho manual fica separado das contagens de envio.
