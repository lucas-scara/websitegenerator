# AGENTS.md — Website Generator Brasil

> **Guia operacional do fork `lucas-scara/websitegenerator`.** Leia também [`ROADMAP-MVP-BR-24H.md`](./docs/ROADMAP-MVP-BR-24H.md). Este guia registra as decisões do proprietário e prevalece, no escopo do fork, sobre menções herdadas a Albert no `SKILL.md` e arquivos de referência. **Não interprete este documento como autorização para iniciar uma campanha ou enviar mensagens.**

## Objetivo e escopo fechado

MVP Brasil em **T0 + 24 horas de janela de execução**: descobrir empresas com sites visualmente fracos → verificar informações e formulário original → gerar site a partir de template preparado → hospedar prévia isolada → verificar URL → fazer **um primeiro contato autônomo**, quando houver autorização do lote e formulário elegível; caso contrário, fallback com e-mail/telefone públicos e contato manual. Dashboard e ledger registram o resultado.

**Não reinventar o produto.** Preservar pesquisa, Firecrawl, coordenador/subagentes, SQLite, dashboard, geração rápida e Vercel. Traduzir textos visíveis, template e abordagem para **pt-BR**; manter nomes internos de código e layout. O template disponível hoje é **somente eletricistas**; não usar conteúdo incompatível em outros segmentos. A evolução modular multi-segmento foi **autorizada por Lucas em 11/10/2026** conforme `docs/template-modular/` (PR #7): um único motor visual com perfis por segmento, nunca aplicações independentes, entregue em PRs separados (alicerce brasileiro → serralheria → demais perfis).

## Regras inegociáveis

1. **GitHub:** nunca commitar diretamente na `main`, fazer merge na `main` ou force-push. Trabalhar em branch (sugestão: `feat/br-mvp`), commitar e abrir PR; **merge exclusivo de Lucas**.
2. **Autoria:** e-mail de commit exigido: `lucasscaranello@gmail.com`; nome: `Lucas Scaranello`. Verificar a identidade REAL registrada pelo mecanismo Git. Se a integração não permitir configurar autor/e-mail, parar e comunicar — não presumir autoria.
3. **Identidade:** responsável é Lucas Scaranello; a **assinatura comercial aprovada é `scarasoft — Lucas Scaranello`**. E-mail de contato e telefone/WhatsApp comerciais foram informados por Lucas e ficam na configuração local `.env`, fora do Git. **Não usar** Albert Shiney, `albert@shiney.ai` nem `albertshineys-projects` em novas execuções. Não confundir e-mail de commit com contato comercial.
4. **Sem segredos no Git:** `.env`, tokens, dados reais de prospecção, evidências e histórico ficam locais/privados; repositório pode permanecer público. Não despejar segredos em prompts, logs ou previews.
5. **Envio externo:** instruções herdadas de consentimento de Albert **não valem** para o proprietário do fork. Enquanto o modo Brasil não estiver configurado e o lote não for autorizado explicitamente: **dry-run, sem submit**. Uma autorização deve delimitar segmento/cidade/volume; para lote autorizado, manter envio autônomo de **uma única tentativa por empresa**. Respeitar opt-outs e CAPTCHAs. Resultado incerto **não é retry**; registrar e escalar.
6. **Fallback:** quando não houver formulário apropriado, registrar e-mail/telefone **publicamente divulgados**, URL de origem, motivo e mensagem preparada; nunca marcar como enviada.
7. **Não inventar:** avaliação visual exige evidência observada; não inferir idade por aparência, nem inventar serviços, avaliações, faturamento, preços, disponibilidade, certificações ou resultado de envio.
8. **Sem execução insegura:** não executar `templates/electrician/scripts/prerender.mjs` no MVP; usar o gerador rápido com build preparado. O script legado tem risco de traversal, listener amplo e Chrome `--no-sandbox`.
9. **Sem reset destrutivo:** não usar `clear-all` na base real; preservar ledger, identidades, submissões e opt-outs. Não repetir abordagem por perda de histórico.
10. **MVP estrito:** qualquer mudança precisa (a) viabilizar Brasil, (b) impedir falha relevante, ou (c) provar o fluxo. Fora disso, abrir backlog; sem migração de stack, CRM próprio, backend novo ou redesign. Perfis de segmento seguem a exceção registrada em "Decisões posteriores do proprietário".

## Papéis e entregáveis

- **ChatGPT:** escopo, textos comerciais, revisão de segurança, revisão linguística, gates e análise do PR.
- **Codex:** alterações de arquivos, tradução e configuração, testes, deploy e execução do piloto controlado, PR.
- **Lucas:** decisões comerciais/credenciais, autorização do lote piloto e **merge na `main`**. Assinatura comercial já aprovada: `scarasoft — Lucas Scaranello`.

| Fase | Janela | Saída obrigatória |
|---|---|---|
| F0 | 0–4h | Identidade/configuração seguras, ferramenta preparada, sem envios involuntários |
| F1 | 4–10h | Dashboard, template e mensagens em pt-BR; fluxo original preservado |
| F2 | 10–15h | Prospecção → geração → deploy → contato/fallback funcionando em simulação |
| F3 | 15–20h | Piloto com 3 eletricistas reais de cidade autorizada; evidência por caso |
| F4 | 20–24h | Testes, correções bloqueadoras, PR para revisão, sem merge |

## Fontes de verdade e arquivos importantes

- Roadmap aprovado: `docs/ROADMAP-MVP-BR-24H.md`.
- `SKILL.md` e `skills/local-business-revamp-parallel/SKILL.md`: workflows atuais, **devem ser localizados** antes de campanha.
- `settings.json`: configuração de operação; **contém identidade e escopo herdados**, substituir antes de rodar.
- `references/outreach.md`, `references/manual-outreach.md`, `references/coordination.md`, `references/production.md`: regras e comandos que devem permanecer consistentes com este guia.
- `tools/control.py`: dashboard/SQLite/estados e deduplicação; `tools/quick_site.py`: geração; `tools/site_assets.py`: coleta.
- `templates/electrician/`: motor visual único (não renomear). Cada segmento é um perfil em `templates/electrician/segments/<id>/` (`segment.json`, `service-catalog.json`, `preset.js`, `stock-images.json`); segmentos atuais: `electrician`, `serralheria`, `climatizacao`, `chaveiros` e `vidracaria`. Após editar, executar `prepare --template <id>` para cada perfil, lint/build e validação de páginas.
- `dashboard/`: painel e fila; **enfileirar não inicia trabalhadores**.

## Definição de pronto e reporte

Aceite = evidências de empresas reais prospectadas, duas observações visuais por empresa qualificada, fatos e contatos verificados, site pt-BR gerado, preview público funcional, **um envio real observado no lote autorizado ou fallback registrado**, proteção contra duplicidade, testes relevantes e PR pronto para revisão. Se não houver formulário elegível, **não forçar envio**; demonstrar mecanismo com teste controlado e informar a limitação. Não prometer conversões comerciais em 24h.

Em cada atualização, informar: etapa efetivamente testada, link/evidência quando disponível, bloqueios reais, arquivos alterados e trabalho pendente. Nunca afirmar que agentes continuam operando em background sem mecanismo verificável.

## Decisões posteriores do proprietário

- Cidade-alvo do piloto: **Bauru, São Paulo**. O operador informa a cidade no formulário do lote; ela não é fixa no código.
- Contatos comerciais: configurados no `.env` local, sem versionar os valores. A autorização do lote para envio real ainda é necessária.
- Chave Firecrawl configurada localmente; a consulta de uso autenticou com 1.036 créditos restantes. Nenhuma empresa foi raspada durante essa checagem.
- Lucas autorizou remover o projeto fictício de demonstração da Vercel e operar localmente. A prévia local não fornece URL pública para mensagem comercial; resolver a publicação antes de contato real com link.
- **Template modular (11/10/2026):** Lucas autorizou a evolução modular descrita em `docs/template-modular/`. Primeiro o alicerce brasileiro do template base (WhatsApp, CTAs, formulário, textos, SEO, slugs), depois serralheria e demais perfis, cada etapa em PR próprio.
- **Slugs em português:** rotas públicas dos templates usam slugs em pt-BR (ex.: `/servicos`, `/reparos-eletricos`). Os IDs internos de `segments/<id>/service-catalog.json` permanecem estáveis.
- **WhatsApp presumido:** o telefone público raspado da empresa pode ser tratado como WhatsApp (≈95% dos casos, segundo Lucas). Os CTAs apontam para `wa.me` com esse número normalizado, salvo quando houver número de WhatsApp específico ou indicação explícita de que o número não usa WhatsApp (`whatsapp: false`).
