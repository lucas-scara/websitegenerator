# Catálogo de seis perfis — briefings completos para Codex

> **Decisões de produto, não alegações sobre empresas específicas.** Todos os exemplos usam Bauru apenas como cidade demonstrativa; geração deve usar local real. Não tratar foto ilustrativa como obra da empresa, nem serviço possível como serviço confirmado.
>
> Referências: [plano de ação](./PLANO-DE-ACAO.md) · [arquitetura](./ARQUITETURA-MODULAR.md).
>
> Os seis grupos são: climatização; dedetizadoras/desentupidoras; serralherias/portões; chaveiros; vidraçarias/esquadrias; toldos/coberturas/calhas. **Eletricistas permanece como sétimo preset e controle de regressão.**

## Regras visuais transversais

Preservar hero fotográfico com gradiente e tipografia editorial, cartões de serviço, identidade premium e alternância de fundos do template atual. Mudar hierarquia dos módulos por intenção, não criar seis designs sem parentesco. No desktop, CTA WhatsApp flutuante se confirmado; mobile barra persistente única, adaptativa, sem sobreposições. Destaque localização e modalidade real de atendimento. Galeria de obras só com evidência real/autorizada; caso contrário, fotos ilustrativas devidamente rotuladas e com títulos adequados. Sem depoimentos falsos, marcas/selos sem fonte, preços/garantias/urgência inventados. FAQ deve responder perguntas específicas, nunca gerar repetição genérica.

---

## 1. Climatização (`climatizacao`)

### Intenção e promessa permitida
Cliente quer instalar split, resolver defeito ou agendar limpeza/manutenção; pode ser residencial ou comercial. Precisa saber **quais equipamentos/serviços**, **onde atende** e **como solicitar orçamento**. Evitar prometer diagnóstico remoto, redução de consumo, descontaminação ou cobertura técnica não confirmada.

### Hero
- **Título modelo:** “Instalação e manutenção de ar-condicionado em {cidade}”.
- **Subtítulo:** “Atendimento para [tipos confirmados] em [região real]. Solicite informações sobre disponibilidade e orçamento.”
- **Principal:** “Solicitar orçamento no WhatsApp” (se há número), senão canal válido.
- **Secundário:** “Conhecer serviços”.
- **Imagem:** técnico instalando/manuseando equipamento ou foto real da equipe; evitar fotografias genéricas de sala luxuosa como única prova.
- **Mobile:** WhatsApp e ligação; não afirmar atendimento imediato.

### Ordem de seções
1. Hero contextualizado + localização.
2. Grade de serviços técnicos disponíveis.
3. Tipos de imóveis e equipamentos, **somente confirmados**.
4. Diferenciais técnicos reais / marcas atendidas quando comprovadas.
5. Trabalhos realizados apenas se fotos próprias autorizadas.
6. Fluxo de orçamento, visita técnica, instalação/manutenção conforme prática da empresa.
7. FAQ por tipo de atendimento.
8. Contato.

### Serviços independentes
`split_installation`, `preventive_maintenance`, `aircon_cleaning`, `diagnostics_repair`, `refrigeration_piping`, `commercial_hvac`, `maintenance_contracts`. IDs ilustrativos a harmonizar com catálogo final. Não presumir que todo instalador seja assistência técnica, trate VRF ou faça contrato corporativo.

### Módulos opcionais
Marcas/linhas de equipamentos com comprovação; modalidades residencial/comercial; galerias; agendamento; FAQ “O que informar para receber orçamento?”; tipos de instalações; urgência apenas se confirmada.

### FAQ sugerida (respostas a produzir a partir de dados reais)
- Instalam e fazem manutenção do mesmo tipo de aparelho?
- Quais marcas e modelos atendem?
- Como solicitar um orçamento de instalação?
- A vistoria é necessária? Qual a região atendida?
- Fazem manutenção preventiva em empresas/condomínios?

### Cuidados editoriais e técnicos
Não usar “autorizada” sem vínculo comprovado; não prometer economia energética, eliminação microbiológica, prazo, refrigeração industrial ou garantias sem evidência. Reutilizar `ServicesGrid`, `FAQ`, hero e contato; **não** construir animações técnicas novas.

### Teste de perfil mínimo
Empresa que só instala split: menu, CTA, título, tópicos do formulário, SEO e imagens não podem mencionar limpeza, reparos ou marcas.

---

## 2. Dedetizadoras e desentupidoras (`controle_pragas_desentupimento`)

### Intenção e estrutura
É uma **família comercial com dois subperfis independentes**: `pest_control` e `drain_cleaning`. Muitas empresas oferecem só um. Ativar ambos exclusivamente com evidência. Intenção varia entre prevenção programada e problema urgente; por isso CTA e hierarquia são condicionais.

### Hero
**Somente dedetização:**
- “Controle de pragas para residências e empresas em {cidade}”.
- CTA: “Solicitar atendimento” / “Falar no WhatsApp”.

**Somente desentupimento:**
- “Desentupimento em {cidade} e região”.
- CTA: “Ligar para solicitar atendimento” quando telefone válido e urgência caracterizar a demanda; WhatsApp alternativo.

**Ambos comprovados:**
- “Soluções para controle de pragas e desentupimento em {cidade}”.
- Primeira dobra deve permitir escolher rapidamente a área desejada, sem mascarar diferença operacional.

### Ordem
1. Hero com canais diretos e localização.
2. “Qual problema você precisa resolver?” → serviços confirmados.
3. Área de atendimento e disponibilidade real.
4. Processo e orientações de segurança (somente documentadas).
5. Licenças e autorizações verificadas quando aplicáveis.
6. FAQ específico.
7. Contato.
Se urgência verdadeira, antecipar disponibilidade e ligação; se serviço programado, priorizar segurança/procedimento.

### Catálogos independentes
**Dedetização:** `cockroach_control`, `ant_control`, `rodent_control`, `termite_control`, `other_pests`, `commercial_pest_control`.
**Desentupimento:** `sink_drain`, `floor_drain`, `toilet`, `sewer_lines`, `hydrojetting`, `inspection`.
Não exibir uma praga, método ou tecnologia por mera presença do segmento.

### Módulos
Subnavegação por problema, tipos de locais (residencial/comercial), prevenção e preparo pós-serviço, documentos sanitários quando houver e forem relevantes, zonas atendidas, telefone emergencial somente se confirmado.

### FAQ
- Existe atendimento hoje ou fora do horário?
- Como é feito o orçamento?
- É preciso preparar ou desocupar o ambiente?
- Quais cuidados existem para crianças e animais?
- A empresa possui as licenças pertinentes?
- Qual serviço cobre o problema apresentado?

### Cuidados
Sem “resultado definitivo”, “100% seguro”, “atendimento 24 horas”, aprovação sanitária ou método químico específico sem fonte. Não minimizar riscos relacionados a produtos. Reutilizar cards, FAQ, contatos. Dois subperfis não justificam duas bases React.

### Testes mínimos
Dedetizadora sem desentupimento; desentupidora sem dedetização; empresa com ambos. Zero referências cruzadas nos dois cenários exclusivos.

---

## 3. Serralherias e portões automáticos (`serralheria`) — **PRIMEIRO PERFIL NOVO**

### Estratégia
Venda de soluções sob medida, fabricação, qualidade de acabamento e confiança técnica. **A fotografia real do trabalho pode ser argumento central.** A automação de portões não é serviço presumido de toda serralheria. Preservar estética premium e tornar layout visualmente orientado a obras.

### Hero
- **Título:** “Portões, estruturas metálicas e soluções sob medida em {cidade}” — construir dinamicamente apenas com categorias confirmadas; se apenas grades, título deve citar grades, não portões.
- **Subtítulo:** serviços confirmados, área de atendimento, processo de solicitação de orçamento.
- **Principal:** “Solicitar orçamento no WhatsApp”.
- **Secundário:** “Ver projetos realizados” **somente se portfólio real**; senão “Conhecer serviços”.
- **Foto:** obra real (portão, estrutura, acabamento) quando autorizada. Alternativa stock com “imagem ilustrativa”, sem sugerir obra própria.

### Ordem
1. Hero + contato + cidade/área.
2. **Portfólio real** (quando há material); do contrário, grade de soluções.
3. Catálogo de serviços.
4. Materiais, aplicações, acabamentos e diferenciais **confirmados**.
5. Como funciona: contato → levantamento/medição → orçamento → fabricação/instalação, adaptado ao processo verificado.
6. Avaliações reais autorizadas.
7. FAQ.
8. Contato.

### Serviços configuráveis
`metal_gates`, `automatic_gates`, `railings`, `handrails`, `guardrails`, `metal_structures`, `metal_doors`, `welding_repairs`, `gate_motor_maintenance`. Não confundir fabricar portão e consertar automatizador; possibilidade de manter subgrupos `metalwork`/`gate_automation`.

### Elementos visuais
- Galeria com categorias e descrições honestas (portões, grades, estruturas etc.).
- Fotos de detalhe/acabamento, antes/depois apenas de casos reais.
- Cards fotografados e chamadas para orçamento sob medida.
- Fotos reais > banco de imagem, mas ausência de fotos não bloqueia uma prévia; neste caso ocultar “obras realizadas” e rotular material ilustrativo.

### FAQ
- Trabalham sob medida?
- Fazem visita técnica/medição?
- Instalam ou consertam portões automáticos?
- Quais localidades atendem?
- Como enviar medidas/fotos para orçamento?
- Trabalham com quais materiais/acabamentos? (somente dados verificados)

### Cuidados
Sem garantia implícita, resistência estrutural presumida, materiais não documentados, prazo de fabricação fictício ou imagens de obras de terceiros rotuladas como próprias. Se a empresa não fizer portões, todo o site deve permanecer coerente com sua atuação.

### Guia direto ao Codex
**Começar por esse preset** como teste da modularidade. Reutilizar `HomePage` hero, `ServicesGrid`, `Gallery`, `FAQ`, `ContactSection`; trocar strings/hrefs/ícones e ativação por dados. Provar em duas demos: (A) somente portões e grades com nenhuma imagem própria; (B) catálogo maior com galeria real simulada por fixtures explicitamente demonstrativas, sem atribuir obras a empresa real. Testar links e SEO.

---

## 4. Chaveiros (`chaveiros`)

### Intenção
Contato rápido para problema frequentemente urgente, ou encomenda de cópia/manutenção. **Menos narrativa, mais acesso a telefone, WhatsApp, área e horário real.** Não reproduzir automaticamente hero imenso com formulário longo e 12 seções.

### Hero
- **Título:** “Chaveiro em {cidade} — serviços residenciais, comerciais e automotivos” apenas se os três âmbitos forem confirmados; caso contrário, título restrito.
- **Principal:** “Ligar agora” se telefone válido.
- **Secundário:** “Chamar no WhatsApp” se verificado.
- **Complemento:** bairro/endereço de loja ou área móvel atendida, horários verificáveis.
- **Imagem:** fechadura/ferramenta/equipe em atividade; evitar animações decorativas.

### Ordem compacta
1. Hero, telefone e WhatsApp.
2. Serviços por tipo de problema.
3. Região atendida, tipo de loja/atendimento externo e horários.
4. Como funciona o atendimento; eventuais regras de autorização.
5. FAQ curto.
6. Contato, eventualmente rota para loja real.

### Serviços
`door_opening`, `key_duplication`, `lock_replacement`, `lock_installation`, `car_keys`, `digital_locks`, `safes`, `emergency_locksmith`.

### Módulos
Barra mobile com **ligar primeiro** para intenção urgente, WhatsApp depois. Eventual mapa/rota somente se loja física. Depoimentos reais opcionais; galeria extensa desativada por padrão; formulário curto e opcional.

### FAQ
- Atende meu bairro/região?
- Qual é o horário e a disponibilidade?
- Trabalha com chave automotiva e qual tecnologia?
- Instala fechadura digital?
- É necessária comprovação de autorização para abrir imóvel ou veículo?

### Cuidados
Não afirmar “chego em 15 minutos”, “24h”, “imediato”, “mais barato” ou capacidade técnica sem comprovação. Para aberturas, mencionar verificação de legitimidade/acesso conforme procedimento da empresa. Não listar conserto automotivo se apenas cópia residencial.

### Teste mínimo
Chaveiro apenas de cópias na loja, sem serviços urgentes: sem chamada “emergência”, sem 24h, sem botão “ligar agora” sugerindo prontidão contínua.

---

## 5. Vidraçarias e esquadrias (`vidracaria_esquadrias`)

### Intenção
Pesquisa visual para acabamentos e projetos sob medida. Alguns clientes buscam reparo/substituição imediata; o preset deve permitir diferenciar **vidraçaria**, **esquadrias** ou ambos, sem união obrigatória.

### Hero
- **Título:** “Vidros e esquadrias sob medida para seu projeto em {cidade}” somente se ambos verificados. Para perfil exclusivo, “Vidros sob medida” ou “Esquadrias [material real]”.
- **Principal:** “Solicitar orçamento pelo WhatsApp”.
- **Secundário:** “Ver projetos” se material próprio ou “Conhecer soluções”.
- **Foto:** ambiente com vidro/esquadria representativo da atuação; não apresentar stock como obra.

### Ordem
1. Hero e região.
2. Soluções por aplicação: banheiros, fachadas, áreas externas, interiores, conforme serviços.
3. Projetos reais/galeria quando houver.
4. Materiais/vidros/perfis e diferenciais comprovados.
5. Como solicitar medição e orçamento.
6. FAQ.
7. Contato.

### Serviços
`shower_enclosures`, `mirrors`, `glass_doors`, `windows`, `glass_facades`, `glass_guardrails`, `balcony_enclosures`, `aluminum_frames`, `glass_replacement`, `repairs`.

### Módulos
Galeria por ambiente e categoria; dados sobre tipos de vidro/perfis quando confirmados; processo medição → fabricação → instalação, caso corresponda à operação. Atenção a montagem de projetos fotográficos.

### FAQ
- Fazem medidas personalizadas?
- Trabalham com vidro temperado/laminado (quando confirmado)?
- Fazem visita para medição?
- Atendem condomínios?
- Quais cidades e bairros atendem?
- Realizam substituição de vidros e reparos?

### Cuidados
Não afirmar atendimento a normas, resistência/isolamento acústico ou eficiência térmica sem documentação. Não presumir que vidraçaria instale esquadrias nem o inverso. Galeria real somente com permissão.

### Testes mínimos
Empresa apenas de box e espelhos: nenhum CTA/página de fachada, alumínio ou janelas; empresa apenas de esquadrias: não exibir serviços de vidraçaria.

---

## 6. Toldos, coberturas e calhas (`toldos_coberturas_calhas`)

### Intenção
Resolver chuva, sol, proteção/uso de ambientes, escoamento ou defeito. Mescla de projeto visual e intervenção funcional. Toldos, coberturas e calhas podem ocorrer em fornecedores distintos: três subgrupos independentes.

### Hero
- **Título exemplo:** “Toldos e coberturas sob medida em {cidade} e região”, apenas se ambos habilitados.
- **Variante calhas:** “Instalação e manutenção de calhas e rufos em {cidade}”.
- **Principal:** “Pedir orçamento no WhatsApp”.
- **Secundário:** “Ver soluções” / “Conhecer trabalhos” se houver projetos reais.
- **Foto:** cobertura/toldo instalado ou calhas em serviço, coerente com o grupo.

### Ordem
1. Hero contextualizado e região.
2. Tipos de soluções habilitadas.
3. Fotos de instalações reais, quando houver.
4. Aplicações (garagem, varanda, comércio, telhado), somente aderentes.
5. Materiais/opções e processo de medição quando confirmados.
6. FAQ.
7. Contato.

### Serviços independentes
**Toldos:** `retractable_awnings`, `fixed_awnings`.
**Coberturas:** `polycarbonate_roofs`, `metal_roofs`, `pergolas`.
**Calhas:** `gutters`, `flashing`, `gutter_repair`, `gutter_cleaning`.
Não permitir que “coberturas de policarbonato” implique calhas, ou vice-versa.

### Módulos
Fotos por aplicação e material, visita/medição, tipos de cobertura, opção residencial/comercial, manutenção e reparos. O conjunto pode ser mais visual (toldos) ou técnico/utilitário (calhas).

### FAQ
- Fazem projetos sob medida e visita técnica?
- Quais materiais trabalham?
- Consertam instalações existentes?
- Quais regiões atendem?
- Quais informações ou fotos são necessárias para um orçamento?
- Realizam instalações para empresas?

### Cuidados
Não prometer impermeabilidade absoluta, resistência a ventos, vida útil, garantia ou capacidade estrutural sem prova. Não misturar soluções que o fornecedor não oferece.

### Testes mínimos
Empresa somente de calhas e rufos: nenhuma imagem de toldos nem menção a pergolado. Empresa somente de toldos: nenhuma página de limpeza de calhas.

---

## 7. Matriz de experiência por preset

| Preset | CTA primário típico (condicional) | Segundo CTA | Galeria | Página inicial |
|---|---|---|---|---|
| Climatização | WhatsApp orçamento | Serviços | Opcional | Técnico, serviços em destaque |
| Dedetização | WhatsApp atendimento | Problemas atendidos | Baixa prioridade | Segurança, problema, região |
| Desentupimento | Ligar/WhatsApp conforme urgência | Serviços | Baixa prioridade | Contato cedo, clareza |
| Serralheria | WhatsApp orçamento | Obras reais ou serviços | Alta se comprovada | Projetos sob medida |
| Chaveiros | Ligar | WhatsApp | Baixa | Muito compacta, urgência factual |
| Vidraçaria/esquadrias | WhatsApp orçamento | Projetos/soluções | Alta se comprovada | Aplicações e portfólio |
| Toldos/coberturas/calhas | WhatsApp orçamento | Soluções | Média/alta se comprovada | Aplicações por subgrupo |
| Eletricistas (legado) | WhatsApp/telefone conforme perfil | Serviços | Opcional | Manter regressão, modernizar |

**Importante:** a matriz não é um conjunto de promessas fixas: a empresa pode ter serviços técnicos sem urgência, não ter galeria, ser somente B2B, operar sem loja física ou não usar WhatsApp.

## 8. Testes transversais dos seis novos presets

- **Ativação seletiva:** cada segmento com catálogo completo e com apenas 1–2 serviços.
- **Coerência:** nenhuma página/ícone/URL/CTA/FAQ/meta/imagem faz alusão a serviço desativado.
- **Região:** não inferir bairros nem 24h; cidade correta nos lugares relevantes.
- **Evidências:** sem reviews ou portfólio fictício; badge apenas se certificado comprovado.
- **Canais:** com WhatsApp, sem WhatsApp, só telefone, nenhum; último cenário deve impedir publicação funcional.
- **Preview:** zero envio real, sem mensagem de “enviado” fictícia.
- **Visual:** desktop e mobile, com e sem galeria, sem widget tapando conteúdo.
- **Eletricista:** preservação funcional de rotas e layout aprovado.
- **Simplicidade:** preservar componentes comuns; nenhuma arquitetura ornamental.

## 9. Como Codex deve consumir este documento

1. Ler [plano](./PLANO-DE-ACAO.md) e [arquitetura](./ARQUITETURA-MODULAR.md).
2. Avaliar divergências entre especificação e código real; reportar, não “resolver” refatorando metade do projeto.
3. Primeiro PR de implementação: **eletricista + serralheria**, com dados fictícios claramente marcados e casos mínimos; sem tocar outros presets.
4. Só após revisão, seguir sequência documentada. Se faltarem informações de um prospecto, **desligar** a informação/módulo e relatar lacuna.
5. Não executar contatos comerciais, deploys públicos ou merge sem autorização específica.
