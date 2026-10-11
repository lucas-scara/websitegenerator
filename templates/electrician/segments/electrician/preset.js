import meta from './segment.json'

/*
 * Segment preset: what an electrician *may* offer. Only services listed in the business
 * `enabled_services` are rendered. Copy describes the service in general terms and never
 * states facts about a specific company (prices, deadlines, guarantees, certifications).
 */
export default {
  ...meta,
  hero: {
    image: meta.hero_image,
    alt: 'Casa iluminada ao anoitecer — imagem ilustrativa',
    title: 'Eletricista',
    titleNoCity: 'Serviços',
    flourishNoCity: 'elétricos',
  },
  aboutImage: '/images/electrician/electrician.jpg',
  servicesHeading: { title: 'Serviços elétricos', flourish: 'para o seu imóvel.' },
  process: [
    { title: 'Conte o que precisa', text: 'Descreva o serviço e, se possível, envie fotos do quadro, da tomada ou do local do problema.' },
    { title: 'Combine os detalhes', text: 'Alinhe endereço, acesso ao imóvel e o melhor dia para avaliação ou execução.' },
    { title: 'Receba o orçamento', text: 'Peça o orçamento com escopo, materiais e prazo antes de autorizar o serviço.' },
  ],
  services: {
    'electrical-repairs': {
      label: 'Reparos elétricos', icon: 'Siren', image: '/images/electrician/panel-testing.jpg', alt: 'Teste em quadro elétrico — imagem ilustrativa',
      short: 'Disjuntor que desarma, tomada sem energia, curto ou cheiro de queimado.',
      intro: 'Reparos para falhas na instalação: disjuntores que desarmam, tomadas e interruptores sem funcionar, pontos aquecendo ou queda de energia em parte do imóvel.',
      checklist: ['O que parou de funcionar e desde quando', 'Se o disjuntor desarma e em qual situação', 'Fotos do quadro e do ponto com problema', 'Bairro e cidade do imóvel'],
      faq: [{ q: 'O que fazer enquanto o eletricista não chega?', a: 'Se houver cheiro de queimado, faísca ou aquecimento, desligue o disjuntor do circuito (ou o geral) e não tente religar repetidamente.' }],
    },
    'electrical-installation': {
      label: 'Instalações elétricas', icon: 'Plug', image: '/images/electrician/cafe-lighting.jpg', alt: 'Luminárias decorativas — imagem ilustrativa',
      short: 'Tomadas, interruptores, iluminação, chuveiro e novos circuitos.',
      intro: 'Instalação de novos pontos de tomada e iluminação, chuveiro elétrico, luminárias e circuitos dedicados, como os de ar-condicionado e forno.',
      checklist: ['Quais pontos ou equipamentos serão instalados', 'Potência dos aparelhos (chuveiro, ar-condicionado, forno)', 'Fotos do local e do quadro elétrico', 'Se o imóvel é casa, apartamento ou comércio'],
      faq: [{ q: 'Meu quadro aguenta um novo chuveiro ou ar-condicionado?', a: 'Depende da carga atual, da fiação e do disjuntor geral. Envie fotos do quadro e a potência do aparelho para uma avaliação.' }],
    },
    'service-entrance': {
      label: 'Padrão de entrada', icon: 'Gauge', image: '/images/electrician/house-dusk.jpg', alt: 'Fachada de casa — imagem ilustrativa',
      short: 'Montagem ou adequação do padrão para ligação nova ou aumento de carga.',
      intro: 'O padrão de entrada reúne caixa de medição, disjuntor geral e aterramento na entrada do imóvel. É exigido pela distribuidora para ligação nova, mudança de categoria ou aumento de carga.',
      checklist: ['Se é ligação nova, aumento de carga ou troca do padrão', 'Foto do padrão atual, se houver', 'Principais equipamentos do imóvel', 'Endereço do imóvel'],
      faq: [{ q: 'Quem faz a ligação depois que o padrão fica pronto?', a: 'A ligação é feita pela distribuidora de energia, conforme as regras e a vistoria dela. Confirme com a empresa como funciona o acompanhamento do pedido.' }],
    },
    'consumer-units': {
      label: 'Troca de quadro elétrico', icon: 'Zap', image: '/images/electrician/panel-testing.jpg', alt: 'Quadro de distribuição — imagem ilustrativa',
      short: 'Substituição de quadro antigo, fusíveis ou disjuntores subdimensionados.',
      intro: 'Substituição do quadro de distribuição antigo por um novo, com disjuntores adequados às cargas atuais do imóvel e circuitos identificados.',
      checklist: ['Foto do quadro atual, aberto e fechado', 'Quais aparelhos de maior potência existem', 'Se há disjuntores desarmando com frequência'],
      faq: [{ q: 'Quando vale a pena trocar o quadro?', a: 'Quadros com fusíveis, sem espaço para novos circuitos ou com disjuntores que desarmam com frequência costumam pedir avaliação.' }],
    },
    'electrical-enclosures': {
      label: 'Instalação de quadro elétrico', icon: 'Box', image: '/images/electrician/panel-testing.jpg', alt: 'Quadro elétrico — imagem ilustrativa',
      short: 'Quadro novo para obra, ampliação ou separação de circuitos.',
      intro: 'Instalação de quadro de distribuição em obras, ampliações ou imóveis que precisam separar circuitos para mais segurança e organização.',
      checklist: ['Tipo de imóvel e etapa da obra', 'Quantidade aproximada de circuitos', 'Fotos ou planta do local'],
      faq: [{ q: 'Preciso de projeto para instalar um quadro novo?', a: 'Depende do tamanho da instalação e das exigências da distribuidora ou do condomínio. Informe o caso para receber orientação.' }],
    },
    'rcd-protection': {
      label: 'Dispositivo DR', icon: 'ShieldAlert', image: '/images/electrician/panel-testing.jpg', alt: 'Disjuntores em quadro — imagem ilustrativa',
      short: 'Proteção contra choque elétrico por fuga de corrente.',
      intro: 'O dispositivo DR desliga o circuito ao detectar fuga de corrente, reduzindo o risco de choque elétrico. A norma brasileira NBR 5410 prevê seu uso em circuitos de áreas molhadas, como banheiros, cozinhas e áreas externas.',
      checklist: ['Foto do quadro elétrico', 'Se o imóvel já tem algum DR instalado', 'Se há aterramento na instalação'],
      faq: [{ q: 'O DR desarma toda hora. É defeito?', a: 'Nem sempre: desarmes frequentes podem indicar fuga de corrente em algum aparelho ou circuito. Vale pedir uma avaliação em vez de retirar o dispositivo.' }],
    },
    rewiring: {
      label: 'Reforma elétrica', icon: 'Hammer', image: '/images/electrician/interior.jpg', alt: 'Interior em reforma — imagem ilustrativa',
      short: 'Troca de fiação antiga e atualização da instalação.',
      intro: 'Atualização de instalações antigas: troca de fiação, revisão de circuitos, aterramento e adequação às cargas atuais do imóvel.',
      checklist: ['Idade aproximada da instalação', 'Problemas observados (aquecimento, quedas, choques)', 'Fotos do quadro e de pontos antigos', 'Se o imóvel estará ocupado durante o serviço'],
      faq: [{ q: 'É preciso quebrar paredes para trocar a fiação?', a: 'Depende de como a instalação foi feita e do estado dos conduítes. Isso é avaliado antes do orçamento.' }],
    },
    maintenance: {
      label: 'Manutenção elétrica', icon: 'Wrench', image: '/images/electrician/electrician.jpg', alt: 'Eletricista com ferramentas — imagem ilustrativa',
      short: 'Revisão preventiva de quadros, tomadas e conexões.',
      intro: 'Revisão preventiva da instalação: aperto de conexões, verificação de quadros, tomadas e iluminação, para residências, condomínios e comércios.',
      checklist: ['Tipo de imóvel e tamanho aproximado', 'Se a manutenção é pontual ou periódica', 'Pontos que já apresentaram problema'],
      faq: [{ q: 'Com que frequência fazer manutenção elétrica?', a: 'Depende do uso e da idade da instalação. Imóveis comerciais e condomínios costumam ter rotinas próprias; consulte a empresa para o seu caso.' }],
    },
    'electrical-contracting': {
      label: 'Projetos elétricos', icon: 'Layers', image: '/images/electrician/lighting.jpg', alt: 'Projeto de iluminação — imagem ilustrativa',
      short: 'Planejamento da instalação para obras e reformas maiores.',
      intro: 'Planejamento da instalação elétrica para construções e reformas: distribuição de circuitos, pontos de tomada e iluminação e dimensionamento do quadro.',
      checklist: ['Planta ou croqui do imóvel', 'Etapa da obra', 'Equipamentos previstos (ar-condicionado, forno, aquecedor)'],
      faq: [{ q: 'O projeto inclui a execução?', a: 'Depende de cada empresa. Pergunte se o orçamento cobre apenas o projeto ou também a execução.' }],
    },
    extensions: {
      label: 'Ampliações', icon: 'HousePlus', image: '/images/electrician/house-dusk.jpg', alt: 'Casa ao anoitecer — imagem ilustrativa',
      short: 'Instalação elétrica para novos cômodos, edículas e áreas externas.',
      intro: 'Instalação elétrica para novos cômodos, edículas, garagens e áreas externas, considerando se o quadro atual comporta os novos circuitos.',
      checklist: ['O que será construído ou ampliado', 'Fotos do quadro atual', 'Equipamentos previstos no novo espaço'],
      faq: [{ q: 'A ampliação exige aumento de carga?', a: 'Pode exigir, dependendo dos equipamentos previstos. Nesse caso a distribuidora de energia também precisa ser consultada.' }],
    },
    renovations: {
      label: 'Reforma completa', icon: 'LayoutGrid', image: '/images/electrician/interior.jpg', alt: 'Cozinha reformada — imagem ilustrativa',
      short: 'Parte elétrica de reformas de casas, apartamentos e comércios.',
      intro: 'Execução da parte elétrica em reformas completas, em conjunto com a obra: novos pontos, iluminação, quadro e circuitos dedicados.',
      checklist: ['Escopo da reforma e cronograma da obra', 'Planta ou fotos dos ambientes', 'Se há arquiteto ou engenheiro responsável'],
      faq: [{ q: 'Em que etapa da obra o eletricista entra?', a: 'Normalmente antes do reboco e do forro, para passar tubulação, e depois no acabamento. Combine as etapas com a empresa.' }],
    },
    'ev-charging': {
      label: 'Carregador veicular', icon: 'BatteryCharging', image: '/images/electrician/ev-charging.jpg', alt: 'Recarga de veículo elétrico — imagem ilustrativa',
      short: 'Circuito e instalação para carregador de carro elétrico.',
      intro: 'Instalação de circuito dedicado e do carregador (wallbox) para veículos elétricos e híbridos plug-in, com avaliação da capacidade do quadro e do padrão de entrada.',
      checklist: ['Modelo do carregador ou do veículo', 'Distância entre o quadro e a vaga', 'Fotos do quadro e do padrão de entrada', 'Se é casa ou condomínio'],
      faq: [{ q: 'Preciso de autorização do condomínio?', a: 'Em condomínios, normalmente sim. Verifique as regras do condomínio antes de agendar a instalação.' }],
    },
  },
}
