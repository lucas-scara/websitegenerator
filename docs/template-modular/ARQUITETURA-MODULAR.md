# Arquitetura modular — especificação para implementação

> Proposta de contrato; adaptar aos mecanismos existentes após inventário. Não implementar nesta PR documental.

## Princípio

**Design scarasoft compartilhado** → **preset do segmento** → **dados/evidências da empresa** → **site gerado**. Reutilizar React/Vite, roteamento, gerador rápido e catálogo existentes. Não construir seis forks nem um CMS.

## Inventário inicial confirmado em main (11/10/2026)

- `templates/electrician/src/App.jsx`: rotas; `CONTENT_PAGES` carregadas por `import.meta.glob` e filtradas por `isServiceEnabled`; barra fixa mobile.
- `src/services.js`: `enabled_services` vindo de `BUSINESS`, mapeamento por URL de `service-catalog.json`; **`isServiceEnabled` retorna true para rotas desconhecidas**. Refletir sobre validação explícita de ids em perfis novos.
- `src/site.js`: `ALL_NAV`, `ALL_HOME_SERVICES`, `ALL_GALLERY`, `TRUST_STATS`, `AREAS.elektriker`; bastantes textos hard-coded.
- `src/business.js`: configuração `window.WEBSITE_BUSINESS`, defaults elétricos, `copy` substituindo placeholders; `phoneHref` e `emailHref`. Não há `whatsappHref`.
- `src/components/MobileCallBar.jsx`: CTA ligar e ir para formulário, fixo em telas abaixo de lg.
- `src/components/QuoteForm.jsx`: obrigatórios nome/telefone/e-mail/endereço/mensagem, temas elétricos, `endpoint = ''`, preview sem envio.
- `src/components/Reviews.jsx`: texto genérico sem reviews.
- `src/pages/HomePage.jsx`: muitas seções e citações elétricas, além de efeitos GSAP e galeria ilustrativa.
- `src/pages/PricesPage.jsx`, `ContactPage.jsx`, `Footer.jsx`, `ContactSection.jsx`: textos e campos em grande parte elétricos, heranças EU.
- `src/lib/useSEO.js`: atualiza metatags client-side. Validar resultados do site gerado e de indexação antes de propor SSR.

## Contrato de configuração ilustrativo

```json
{
  "segment": "serralheria",
  "business": {
    "name": "Empresa Exemplo",
    "city": "Bauru",
    "state": "SP",
    "phone": null,
    "whatsapp": null,
    "address": null,
    "service_areas": []
  },
  "enabled_services": ["metal_gates", "metal_railings"],
  "sections": {
    "portfolio": true,
    "reviews": false,
    "faq": true,
    "process": true,
    "brands": false
  },
  "conversion": {"primary": "whatsapp", "fallback": "phone"},
  "preview": true
}
```

Não tomar nomes de chaves como contrato já implementado. **Fonte da verdade:** catálogo de serviços por segmento + dados confirmados + validação de schema. `null` significa informação não disponível; não inventar preenchimento. Preferir adaptar `enabled_services` atual a construir uma segunda lógica concorrente.

## Modelo mínimo recomendado

**Preset de segmento**
- `id`, rótulo, tipo de intenção (técnico, urgência, portfólio, misto).
- Catálogo `service_id` estável → título, resumo, slug, mídia ilustrativa válida, perguntas, disponibilidade; o segmento define possíveis serviços, não serviços confirmados.
- Ordem de seções e campos do formulário; variantes hero curto/visual/urgência.
- Política de CTAs (ordem padrão, não promessa de disponibilidade).
- Orientações de texto e fatos proibidos.
- Lista de FAQ ligada a cada serviço quando aplicável.

**Perfil da empresa**
- Identidade, cidade/UF, telefone/WhatsApp, horários, localização/área atendida, redes reais.
- Serviços **comprovados**, incluindo status de verificação/proveniência quando disponível.
- Diferenciais, preços, marcas, documentos e garantias **somente** com fontes.
- Mídias com origem, permissão, legenda e `kind` (`real_work`, `illustrative`, `brand`).
- Depoimentos com fonte, permissão e data de verificação quando aplicável.

**Renderização**
- Resolve preset + empresa → modelo final validado; componentes só recebem dados filtrados.
- Ocultar blocos vazios; não preencher com slogans artificiais.
- Gerar menu, rotas, cards, FAQs, CTAs, footer e SEO da **mesma lista de serviços resolvidos**. Evitar múltiplos arrays hard-coded inconsistentes.
- Nunca renderizar páginas acessíveis para serviços desligados, inclusive URL direta; evitar links órfãos e redirects inconsistentes.
- Falha de validação (ex.: sem canal de contato para produção, id desconhecido, dados conflitantes) deve bloquear geração/publicação conforme gravidade, com log.
- QA automático deve rastrear termos de outros setores e dados de demonstração.

## WhatsApp e contato

- Somente se número confirmado; E.164/BR normalizado: `https://wa.me/55DDDNUMERO?text=...` (sem sinais, com codificação adequada e cuidado para não duplicar DDI).
- Mensagem inicial curta e contextual, por exemplo “Olá! Encontrei vocês pelo site e gostaria de solicitar orçamento para [serviço].” Não adicionar dados pessoais ou rastreamento invisível na mensagem.
- Desktop: botão flutuante no canto inferior direito, evitando widgets sobrepostos. Mobile: **uma** barra persistente com WhatsApp + ligar; para chaveiros, pode ser ligar + WhatsApp. Usar safe-area; não cobrir formulário, cookies ou navegação.
- Fallback quando indisponível: ligação, formulário **funcional em produção** ou email, conforme dados válidos. Nunca renderizar link vazio, e nunca fingir formulário operacional.
- Métricas futuras: cliques `whatsapp_click`, `phone_click`, `form_submit_success` apenas quando real; não confundir evento de clique com lead fechado.

## Política de preview

- Preview deve avisar que é demonstrativo, quando dados/imagens forem ilustrativos.
- `QuoteForm` na main já usa `endpoint = ''`, impedindo envio e mostrando estado preview. Preservar esse bloqueio até um fluxo de produção autorizado e testado.
- Imagens de referência/editoriais não são obras da empresa; nunca chamar galeria de “Projetos realizados” sem mídias reais autorizadas.
- Nenhuma avaliação/review, selo, métrica, preço, SLA ou “24h” fabricados.
- Informações de contato exibidas devem ser comprovadas; considerar desabilitar CTAs em demos fictícias.

## Regionalização Brasil

- Campos próprios de cidade/UF, CEP, endereço completo quando há loja física; empresas de atendimento externo podem exibir apenas região.
- `cvr` (Dinamarca), `ean`, `authNumber` não devem vazar em página brasileira; eventual CNPJ é opcional e validado.
- Área atendida: cidade, município/regiões reais; não gerar landing page por bairro sem conteúdo único útil.
- Linguagem brasileira natural, evitando “Inspiração” como nome de portfólio real e “Converse sobre seu projeto” em todo bloco.
- Provas legais/regulatórias: licenças sanitárias, certificação profissional, autorização de marcas etc. exibidas somente quando verificadas.
- Dados estruturados de `LocalBusiness` e SEO por rota coerentes com o que o usuário vê; atenção a prévias não indexáveis.

## Variantes por intenção

| Intenção | Segmentos típicos | Hero / prioridades |
|---|---|---|
| Urgência | Chaveiros; algumas desentupidoras | CTA telefone, horários verificados, área atendida, poucos blocos |
| Técnico | Climatização; dedetização | Tipo de serviço, problemas resolvidos, procedimentos, marcas/licenças comprovadas |
| Portfólio | Serralheria; vidraçaria; toldos | Imagens **reais** primeiro, tipos de projeto, processo, WhatsApp |
| Misto | Portões automáticos; calhas; manutenção | Seleção por serviços e prioridade adaptável |

## Testes mínimos automatizados + visuais

1. Sete perfis geram build e páginas principais; `eletricista` serve como regressão.
2. Para cada perfil, caso **muitos serviços** e caso **um/dois serviços**; checar menu, URLs, páginas, FAQ, footer, cards, formulário e SEO sem sobras.
3. Desligar EV charging no eletricista e procurar todas as menções/links/fotos; usar isso como teste de implementação modular.
4. WhatsApp válido, inválido/ausente, telefone presente/ausente, ambos ausentes; validar destino e política de publicação.
5. Formulário preview jamais faz POST nem exibe sucesso; eventual modo produção só relata sucesso após resposta real.
6. Mobile 320px/375px/768px e desktop; sem overflow, sem CTA cobrindo inputs, contato acessível.
7. Performance (LCP/CLS/INP), foco teclado, contraste, texto alternativo e movimento reduzido.
8. SEO: title/description/OG/canonical, dados estruturados coerentes, sem dados fictícios indexáveis.
9. Falta de portfólio: não renderizar seção “Obras realizadas” usando stock.
10. Conteúdo: varrer rastros de eletricistas, dinamarquês, placeholders `Your Company`, email `you@example.com`.

## Caminho de implementação

Começar pela menor mudança que permita **serralheria + eletricista** funcionar usando os mesmos componentes, com testes. Só então reutilizar os presets para os demais setores. Criar PRs separados, não mergear main automaticamente.

**Complementos:** [plano](./PLANO-DE-ACAO.md), [especificações de segmentos](./SEGMENTOS.md).
