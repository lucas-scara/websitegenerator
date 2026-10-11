import meta from './segment.json'

/*
 * Segment preset: what a pest control and drain unclogging company (dedetização e desentupimento) *may* offer.
 * Only services listed in the business `enabled_services` are rendered, so pest control and drain unclogging stay
 * independent: the copy of each service never implies the other group. Copy describes the service in general terms
 * and never states facts about a specific company (prices, deadlines, guarantees, certifications, products,
 * results, availability, brands). Illustrative stock photographs (see stock-images.json) are bundled; services without
 * a photo fall back to the themed design.
 */
export default {
  ...meta,
  hero: {
    title: 'Dedetização e desentupimento',
    titleNoCity: 'Dedetização e desentupimento',
    flourishNoCity: 'para o seu imóvel',
    image: meta.hero_image,
    alt: 'Profissional com pulverizador costal aplicando produto ao redor de uma casa (imagem ilustrativa)',
  },
  servicesHeading: { title: 'Serviços da empresa', flourish: 'para o seu imóvel.' },
  process: [
    { title: 'Conte o que está acontecendo', text: 'Descreva o problema e o tipo de imóvel, ou mande fotos do local para a empresa avaliar.' },
    { title: 'Tire suas dúvidas', text: 'Pergunte como o serviço é feito e o que muda na sua rotina antes de contratar.' },
    { title: 'Receba o orçamento', text: 'Peça o orçamento com o que está incluso e o prazo antes de contratar o serviço.' },
  ],
  services: {
    'pest-control': {
      image: '/images/dedetizacao/pest-control.jpg',
      alt: 'Mão segurando um pulverizador amarelo em funcionamento — imagem ilustrativa',
      label: "Dedetização", icon: 'SprayCan',
      short: "Controle de pragas urbanas em casas, apartamentos e comércios.",
      intro: "Dedetização para casas, apartamentos, comércios e outros ambientes, com aplicação feita por profissionais da empresa.",
      checklist: ["Tipo de imóvel e metragem aproximada", "Qual praga você vê no local", "Onde ela costuma aparecer", "Se há crianças, animais ou plantas no ambiente"],
      faq: [{ q: "O que preciso informar para pedir o orçamento?", a: "Em geral, o tipo de imóvel, o tamanho aproximado e a praga que você observa. Pergunte à empresa como se preparar para a aplicação." }],
    },
    'cockroaches-ants': {
      image: '/images/dedetizacao/cockroaches-ants.jpg',
      alt: 'Barata sobre uma superfície cinza — imagem ilustrativa',
      label: "Baratas e formigas", icon: 'Bug',
      short: "Atendimento para baratas e formigas em cozinhas, áreas de serviço e comércios.",
      intro: "Atendimento para problemas com baratas e formigas em casas, apartamentos, restaurantes e outros comércios.",
      checklist: ["Onde os insetos aparecem (cozinha, banheiro, área externa)", "Há quanto tempo você nota o problema", "Tipo de imóvel", "Fotos do inseto ou do local, se possível"],
      faq: [{ q: "Como saber qual inseto é?", a: "Se puder, envie uma foto do inseto e do local onde aparece. Isso ajuda a empresa a entender o seu caso." }],
    },
    'termites': {
      label: "Cupins", icon: 'Worm',
      short: "Avaliação e atendimento para cupins em móveis, portas e madeiramentos.",
      intro: "Atendimento para cupins em móveis, portas, batentes e madeiramentos de casas e comércios.",
      checklist: ["Onde você percebeu sinais (móvel, porta, forro, estrutura)", "Tipo de imóvel", "Fotos dos sinais observados", "Há quanto tempo você notou"],
      faq: [{ q: "Posso enviar fotos para a empresa avaliar?", a: "Sim. Fotos dos sinais e do local ajudam a empresa a orientar os próximos passos." }],
    },
    'rodents': {
      label: "Ratos e roedores", icon: 'Rat',
      short: "Atendimento para ratos e outros roedores em casas e comércios.",
      intro: "Atendimento para problemas com ratos e outros roedores em casas, comércios, depósitos e áreas externas.",
      checklist: ["Onde você viu ou ouviu os animais", "Tipo de imóvel", "Sinais observados (fezes, roeduras, ruídos)", "Fotos do local, se possível"],
      faq: [{ q: "O que informar sobre o problema?", a: "Diga onde os sinais aparecem e há quanto tempo. Quanto mais detalhes, melhor a empresa entende o seu caso." }],
    },
    'drain-unclogging': {
      image: '/images/dedetizacao/drain-unclogging.jpg',
      alt: 'Detalhe do ralo de uma pia de aço inox — imagem ilustrativa',
      label: "Desentupimento de pias e ralos", icon: 'ShowerHead',
      short: "Desentupimento de pias, ralos, vasos sanitários e tubulações internas.",
      intro: "Desentupimento de pias, ralos, tanques, vasos sanitários e tubulações internas de casas, apartamentos e comércios.",
      checklist: ["Qual ponto está entupido (pia, ralo, vaso, tanque)", "Se a água está descendo devagar ou parou", "Tipo de imóvel", "Se o problema é só em um ponto ou em vários"],
      faq: [{ q: "Preciso saber a causa do entupimento?", a: "Não. Descreva o que está acontecendo e a empresa orienta como avaliar o seu caso." }],
    },
    'sewer-unclogging': {
      image: '/images/dedetizacao/sewer-unclogging.jpg',
      alt: 'Ralo linear de grelha metálica em piso molhado — imagem ilustrativa',
      label: "Desentupimento de esgoto", icon: 'Waves',
      short: "Desentupimento de redes de esgoto e tubulações de maior porte.",
      intro: "Desentupimento de redes de esgoto e tubulações de maior porte em casas, prédios e comércios.",
      checklist: ["Onde o problema aparece (banheiro, quintal, rua, vários pontos)", "Se há retorno de água ou mau cheiro", "Tipo de imóvel", "Fotos ou vídeo do local, se possível"],
      faq: [{ q: "O que informar para o orçamento?", a: "Descreva onde o problema aparece e se afeta um ou vários pontos do imóvel. Fotos ajudam a empresa a entender a situação." }],
    },
    'grease-trap': {
      label: "Caixa de gordura", icon: 'Droplets',
      short: "Limpeza e desentupimento de caixas de gordura em casas e cozinhas comerciais.",
      intro: "Limpeza e desentupimento de caixas de gordura em casas, restaurantes e cozinhas comerciais.",
      checklist: ["Tipo de imóvel ou estabelecimento", "Onde fica a caixa de gordura", "Sinais do problema (água parada, retorno)", "Foto da caixa, se possível"],
      faq: [{ q: "Serve para cozinhas de comércios?", a: "Pergunte à empresa se atende o seu tipo de estabelecimento e informe o que acontece na cozinha." }],
    },
    'storm-drains': {
      image: '/images/dedetizacao/storm-drains.jpg',
      alt: 'Calçada molhada com folhas acumuladas junto ao ralo — imagem ilustrativa',
      label: "Ralos e canaletas externos", icon: 'Wrench',
      short: "Desentupimento de ralos, canaletas e grelhas de áreas externas.",
      intro: "Desentupimento de ralos, canaletas e grelhas de quintais, calçadas, garagens e outras áreas externas.",
      checklist: ["Onde fica o ralo ou a canaleta", "Se a água empoça quando chove ou ao lavar o piso", "Presença de folhas ou terra no local", "Fotos da área"],
      faq: [{ q: "Posso pedir só para a área externa?", a: "Sim. Informe qual ponto externo está com problema e peça o orçamento para esse serviço." }],
    },
  },
}
