# Plano de ação — evolução modular scarasoft (Brasil)

> **Status:** proposta para revisão; documentação apenas. Não autoriza implementação, disparos comerciais, publicação ou merge.
> **Origem:** auditoria do código em `templates/electrician` e decisões da conversa de 11/10/2026.
> **Objetivo:** preservar o design premium do template de eletricistas e criar perfis configuráveis para seis segmentos já prospectados em Bauru.

## 1. Diagnóstico do estado atual

### Preservar
- Hero fotográfico de alto impacto: gradiente escuro, tipografia editorial, dois CTAs e boa hierarquia.
- Cartões fotográficos de serviços, layout responsivo, alternância entre seções claras/escuras, espaçamento e componentes compartilhados.
- Navegação, páginas individuais de serviços, galeria, FAQ e CTAs distribuídos pela experiência.
- Base já existente de `enabled_services`, `services.js`, `site.js`, `business.js` e `service-catalog.json`. **Evoluir**, não reconstruir.
- `MobileCallBar.jsx`: já existe barra fixa no mobile; ajustar sua estratégia, não criar outra barra redundante.

### Corrigir / melhorar
1. **Conversão Brasil:** a experiência privilegia telefone e formulário; falta WhatsApp integrado, link `wa.me` corretamente normalizado, mensagem contextual e fallback confiável. No desktop, botão flutuante discreto; no mobile, barra inferior com ação principal e alternativa, evitando duplicação/obstrução.
2. **Hero e conteúdo:** frases genéricas e repetidas (por exemplo, “Converse conosco sobre o serviço elétrico, o prazo desejado e o orçamento para seu imóvel”), pouca diferenciação real, cidade/área pouco evidente. Hero deve responder *o que faz, onde atende, como contratar* em segundos.
3. **Formulário:** `QuoteForm.jsx` exige nome, telefone, email, endereço e mensagem. Reduzir atrito e configurar campos por segmento. Em prévias, **não enviar nada** nem mostrar falsa confirmação; em produção, habilitar apenas com endpoint comprovadamente operacional e regras adequadas de privacidade.
4. **Credibilidade:** `Reviews.jsx` contém convite genérico, não avaliações. `TRUST_STATS` usa palavras (“Cuidado”, “Qualidade”) em vez de evidências. Exibir depoimentos, notas, tempo de atuação, certificações, fotos reais e marcas apenas quando verificadas e autorizadas. Sem fabricação de provas sociais.
5. **Página excessivamente longa:** `HomePage.jsx` intercala Hero, serviços, Features, Reviews, WhyUs, Pillars, Protocol, ProService, Inspiration, TrustSignals, Social, contato. Remover ou tornar opcionais blocos redundantes; comprimento é função da informação útil, não de uma meta fixa.
6. **Acoplamento ao setor elétrico:** há textos, mídias, rotas, opções do formulário, conteúdo, SEO, nomes dinamarqueses e componentes específicos fora do catálogo. Filtrar apenas links não resolve. Um serviço desligado não pode reaparecer em parágrafos, FAQs, imagens, opções, metadados e rotas.
7. **Regionalismos:** remover/normalizar quando aplicável `cvr`, `ean`, `authNumber`, `elektriker`, `Your Company`, `you@example.com`, textos legados e indicadores de “Inspiração” que parecem portfólio sem serem reais. Ajustar DDD/telefone, CEP, cidade/UF, horários e português natural.
8. **SEO local:** títulos/descrições coerentes com serviço e região, canonical/OG corretos, páginas de serviços úteis, marcação `LocalBusiness` apenas com dados reais, sem páginas artificiais por bairro. Verificar renderização/indexabilidade no projeto Vite/React antes de migração tecnológica.
9. **Qualidade mobile:** verificar hierarquia, botões sem sobreposição, preenchimento do formulário, LCP/INP/CLS, imagens, foco por teclado, contraste e movimento reduzido. Animações GSAP/marquee podem continuar apenas se não prejudicarem navegação.
10. **Prévia ≠ produção:** legenda clara para imagens ilustrativas, formulário desativado na prévia, links de contato para dados efetivamente verificados; evitar expor dados falsos como reais.

## 2. Princípios de produto

- **Um motor visual compartilhado; sete perfis** (eletricistas + seis novos), não sete aplicações.
- **Configuração, não edição manual de JSX:** camadas de design/componentes, preset do segmento e dados da empresa.
- **Nenhum fato inventado:** serviços, avaliações, urgência, “24h”, prazos, preços, garantias, autorizações, marcas e imagens de trabalhos.
- **Ausência deve ser tratada como ausência:** esconder módulo ou CTA sem suporte; não inventar texto para preencher o layout.
- **Canal por intenção:** WhatsApp geralmente primário nos serviços locais, telefone pode ser primário para urgência como chaveiros; sempre condicional a contato válido.
- **Portfólio exige origem:** fotografias ilustrativas jamais rotuladas como obras realizadas.
- **Mínima complexidade:** sem CMS, novo backend, agente, CRM, chatbot, migração completa de stack ou módulo animado próprio para cada setor.
- **Qualidade visual original é patrimônio:** manter tipografia, grid, gradientes e identidade premium, mas remover excesso de conteúdo e efeitos sem função.
- **Não extrapolar pesquisas:** preferência por WhatsApp no Brasil justifica prioridade do canal; não afirmar uplift de conversão sem experimento medido.

## 3. Estrutura sugerida para Home

1. Hero: serviço específico + cidade/área + CTA verificável.
2. Prova de confiança curta: apenas evidências verificadas; senão omitir.
3. Principais serviços habilitados.
4. Portfólio/trabalhos reais, quando disponíveis e relevantes; caso contrário conteúdo útil de soluções.
5. Diferenciais/processo: fatos específicos, não adjetivos vazios.
6. FAQ com perguntas concretas por segmento.
7. Contato final: WhatsApp/telefone, cobertura geográfica e endereço apenas quando real.

Variantes: **urgência** (chaveiros, alguns desentupimentos) encurta jornada e antecipa contatos; **projetos sob medida** (serralheria, vidraçaria, toldos) antecipa portfólio; **serviço técnico** (climatização) antecipa categorias e modalidades.

## 4. Plano incremental e responsabilidades

| Etapa | Tarefa | Entrega / aceite |
|---|---|---|
| F0 | Inventário, baseline da main, capturas/testes desktop/mobile, conferir filtros | Evidência e regressão para eletricista; sem mudanças funcionais |
| F1 | Regionalização, WhatsApp, CTAs, formulário, textos e hierarquia | Base pt-BR funcional, sem canais falsos e sem sobreposição |
| F2 | Extração mínima de conteúdo + módulos/serviços configuráveis | Ativar/desativar todos os serviços e seções sem sobras de referência |
| F3a | Perfil completo **serralheria** | Primeiro teste real da arquitetura; gerar caso com poucos serviços |
| F3b | Climatização e chaveiros | Validar conversão técnica versus urgente |
| F3c | Vidraçaria/esquadrias e toldos/coberturas/calhas | Reutilizar galeria/portfólio e configuração de serviços |
| F3d | Dedetização/desentupimento | Validar subperfis independentes e combinados |
| F4 | QA automatizado + captura visual de cada perfil e estados | 7 perfis x cenários completos/mínimos; rotas, conteúdo, canais, mobile |
| F5 | Prévia controlada de prospectos reais já verificados | Um caso por novo segmento, com proveniência; sem comunicação externa automática |

**Não executar tudo em um único PR:** primeiro implementar a base modular + serralheria; PRs posteriores para perfis. As entregas devem ser revisáveis e não bloquear prospecção em paralelo.

### Critérios de aceite
- Build e rotas corretos; sem referências elétricas nos novos segmentos.
- Nenhum serviço desligado aparece em menu, footer, seção, FAQ, formulário, SEO, links ou páginas internas.
- Todos os CTAs são válidos; sem WhatsApp → fallback de telefone/formulário legítimo ou ocultação; sem canais → bloquear publicação.
- Preview não recebe dados e não afirma envio; produção nunca habilita formulário sem backend testado.
- Sem números, certificações, reviews, urgência ou portfólio inventados.
- Responsivo; sem sobreposição; contraste, foco e `prefers-reduced-motion` testados.
- Todos os seis perfis com cenário de poucos serviços, e eletricistas sem regressão.

## 5. Governança

- Regras de `AGENTS.md` permanecem válidas: branch + PR, nunca merge automático/direto na main; autoria de implementação conforme padrão do projeto.
- Esta documentação no PR draft é **somente proposta** e deverá ser revisada pelo proprietário antes da implementação.
- Sem alteração em produção, sem credenciais, sem mensagens a leads.
- Materiais: [arquitetura](./ARQUITETURA-MODULAR.md) e [seis perfis detalhados](./SEGMENTOS.md).
