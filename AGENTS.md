# scarasoft — instruções do repositório

Leia [o procedimento oficial](docs/workflows/PROSPECCAO.md) antes de executar um lote. O dashboard registra cidade, segmento e meta de prévias verificadas no SQLite; o Codex coordena a execução quando o operador pedir. O dashboard não inicia agentes. A conclusão automática do lote não inclui contato comercial.

Trabalhe em branch, nunca commite na `main`, faça merge ou force-push. Autor dos commits: `Lucas Scaranello <lucasscaranello@gmail.com>`; verifique com `git var GIT_AUTHOR_IDENT`. Abra PR para revisão humana. Preserve `data/`, `runs/`, identidades, lotes, contatos, submissões e opt-outs. Não publique prospectos reais nem segredos no Git. Não use `clear-all` no banco durável.

Use o motor multissegmento em `templates/electrician/segments/`, `tools/quick_site.py` e o projeto Vercel existente `scarasoft-previas`. Não crie backend, CRM, fila externa, projeto Vercel por empresa ou novo orquestrador. Não altere templates visuais sem necessidade comprovada. A fonte de verdade para verificação de URLs é [VERIFICACAO-URLS](docs/VERIFICACAO-URLS.md); para captura Firecrawl, [firecrawl-scouting](references/firecrawl-scouting.md); para geração e publicação, [PILOTO-PREVIAS](docs/PILOTO-PREVIAS.md). Documentos de pilotos anteriores são histórico, não instruções atuais.

Nenhum contato comercial faz parte desta fase. Preserve ferramentas e histórico de contato existentes, mas não execute `contact-begin`, `contact-finish`, `contact-simulate` ou `manual-outreach` ao cumprir um lote de prévias. Fatos, avaliações visuais e serviços devem ter evidências reais. Não infira idade do site pela aparência. Telefone público pode ser WhatsApp presumido, salvo evidência contrária; distinga de WhatsApp confirmado.
