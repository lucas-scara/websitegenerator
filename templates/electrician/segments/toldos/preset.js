import meta from './segment.json'

/*
 * Segment preset: what an awning, roofing and gutter company (toldos, coberturas e calhas) *may* offer. Only
 * services listed in the business `enabled_services` are rendered, so awnings, roofs and gutters stay independent:
 * the copy of each service never implies another group. Copy describes the service in general terms and never
 * states facts about a specific company (prices, deadlines, guarantees, certifications, standards, availability, brands).
 * Illustrative stock photographs (see stock-images.json) are bundled; services without a photo fall back to the themed design.
 */
export default {
  ...meta,
  hero: {
    title: 'Proteção contra sol e chuva',
    titleNoCity: 'Proteção contra sol e chuva',
    flourishNoCity: 'sob medida',
    image: meta.hero_image,
    alt: 'Toldo retrátil de lona clara aberto sob céu azul, com folhagem ao lado (imagem ilustrativa)',
  },
  servicesHeading: { title: 'Serviços da empresa', flourish: 'para o seu espaço.' },
  process: [
    { title: 'Envie o local e as medidas', text: 'Informe o tipo de serviço e as medidas aproximadas, ou mande fotos do local.' },
    { title: 'Escolha o modelo e o material', text: 'Defina modelo, cor e material, tirando dúvidas direto com a empresa.' },
    { title: 'Receba o orçamento', text: 'Peça o orçamento com o que está incluso e o prazo antes de contratar o serviço.' },
  ],
  services: {
    'retractable-awnings': {
      image: '/images/toldos/retractable-awnings.jpg',
      alt: 'Toldo listrado verde e amarelo aberto contra o céu — imagem ilustrativa',
      label: "Toldos retráteis", icon: 'Umbrella',
      short: "Toldos que abrem e recolhem, para sombra quando precisar.",
      intro: "Toldos retráteis para varandas, terraços, áreas externas e comércios, que podem ser abertos para dar sombra e recolhidos quando não são necessários.",
      checklist: ["Largura e projeção desejadas", "Local da instalação (parede, teto, viga)", "Cor e tipo de tecido", "Foto do local"],
      faq: [{ q: "O toldo retrátil é manual ou motorizado?", a: "Depende do modelo oferecido. Pergunte à empresa quais acionamentos estão disponíveis e como funciona cada um." }],
    },
    'fixed-awnings': {
      image: '/images/toldos/fixed-awnings.jpg',
      alt: 'Toldo azul fixo com borda ondulada sobre parede de tijolos — imagem ilustrativa',
      label: "Toldos fixos", icon: 'Blinds',
      short: "Toldos fixos para fachadas, entradas, janelas e áreas externas.",
      intro: "Toldos fixos para fachadas de lojas, entradas, janelas e áreas externas, em diferentes formatos, cores e tipos de estrutura.",
      checklist: ["Largura e projeção desejadas", "Local da instalação e tipo de parede", "Formato, cor e tipo de tecido ou material", "Foto da fachada ou do local"],
      faq: [{ q: "Posso escolher a cor e o formato do toldo fixo?", a: "Em geral há várias opções de cor e formato. Peça à empresa as alternativas disponíveis e envie uma foto do local." }],
    },
    'polycarbonate-roofs': {
      image: '/images/toldos/polycarbonate-roofs.jpg',
      alt: 'Cobertura translúcida com estrutura metálica contra o céu azul — imagem ilustrativa',
      label: "Coberturas de policarbonato", icon: 'Warehouse',
      short: "Coberturas translúcidas para garagens, passagens, varandas e áreas externas.",
      intro: "Coberturas de policarbonato para garagens, corredores, varandas e áreas de serviço, que protegem o espaço e deixam passar a luz natural.",
      checklist: ["Medidas da área a cobrir", "Local da instalação e tipo de apoio", "Cor e tipo de chapa", "Foto do local"],
      faq: [{ q: "Preciso informar a inclinação do local?", a: "Ajuda bastante. Envie fotos e medidas do espaço e peça orientação sobre a estrutura adequada ao seu caso." }],
    },
    'metal-roofs': {
      image: '/images/toldos/metal-roofs.jpg',
      alt: 'Telhado de chapa metálica clara em casa com água-furtada — imagem ilustrativa',
      label: "Coberturas metálicas", icon: 'House',
      short: "Coberturas e telhados em chapa metálica para casas, galpões e áreas externas.",
      intro: "Coberturas em telha ou chapa metálica para casas, galpões, garagens e áreas externas, conforme o uso e o tipo de estrutura.",
      checklist: ["Medidas e formato da área", "Tipo de estrutura existente ou a executar", "Tipo e cor da telha", "Foto do local"],
      faq: [{ q: "Dá para instalar sobre a estrutura que já tenho?", a: "Depende da estrutura. Envie fotos e peça à empresa uma avaliação do que pode ser aproveitado." }],
    },
    'pergolas': {
      image: '/images/toldos/pergolas.jpg',
      alt: 'Pérgola escura em jardim com sofás de vime — imagem ilustrativa',
      label: "Pérgolas", icon: 'Tent',
      short: "Pérgolas para jardins, quintais, varandas e áreas de lazer.",
      intro: "Pérgolas em diferentes materiais para jardins, quintais, varandas e áreas gourmet, criando um espaço sombreado para uso ao ar livre.",
      checklist: ["Medidas da área", "Material desejado (madeira, metal, alumínio)", "Tipo de cobertura (aberta, ripada, fechada)", "Foto do local"],
      faq: [{ q: "Posso combinar a pérgola com outro tipo de cobertura?", a: "Em geral é possível combinar materiais. Descreva o que você imagina e peça a opinião da empresa." }],
    },
    'gutters': {
      image: '/images/toldos/gutters.jpg',
      alt: 'Tubo de queda metálico encostado em parede de concreto — imagem ilustrativa',
      label: "Calhas", icon: 'Droplets',
      short: "Instalação de calhas e tubos de queda para conduzir a água da chuva.",
      intro: "Instalação de calhas e tubos de queda em telhados de casas, comércios e galpões, para conduzir a água da chuva até o ponto de descarte.",
      checklist: ["Comprimento do beiral ou da área a atender", "Tipo de telhado", "Material desejado (galvanizado, alumínio, PVC)", "Foto do telhado e do local de descida"],
      faq: [{ q: "Como é feito o orçamento de calhas?", a: "Em geral se informa o comprimento a ser atendido e o tipo de telhado. Pergunte se a empresa faz medição no local." }],
    },
    'flashing': {
      image: '/images/toldos/flashing.jpg',
      alt: 'Telhado metálico com água-furtada e acabamentos nos encontros — imagem ilustrativa',
      label: "Rufos", icon: 'Layers',
      short: "Rufos e acabamentos nos encontros do telhado com paredes e platibandas.",
      intro: "Rufos instalados nos encontros do telhado com paredes, muros e platibandas, como acabamento para o telhado.",
      checklist: ["Local onde o rufo será instalado", "Medidas aproximadas do trecho", "Material desejado", "Foto do encontro telhado/parede"],
      faq: [{ q: "Rufo e calha são a mesma coisa?", a: "Não. O rufo é um acabamento nos encontros do telhado; a calha conduz a água da chuva. Informe qual serviço você precisa." }],
    },
    'gutter-repair': {
      image: '/images/toldos/gutter-repair.jpg',
      alt: 'Calha e beiral de casa contra o céu nublado — imagem ilustrativa',
      label: "Reparo de calhas", icon: 'Wrench',
      short: "Reparo de calhas, emendas e tubos de queda com defeitos.",
      intro: "Reparo de calhas e tubos de queda com vazamentos, emendas soltas, entupimentos de passagem ou peças danificadas.",
      checklist: ["Descrição do problema (vazamento, calha solta, peça quebrada)", "Altura e acesso ao local", "Material da calha atual", "Fotos da área com defeito"],
      faq: [{ q: "A calha precisa ser trocada ou dá para consertar?", a: "Depende do estado da peça. Envie fotos e peça uma avaliação antes de decidir." }],
    },
    'gutter-cleaning': {
      image: '/images/toldos/gutter-cleaning.jpg',
      alt: 'Detalhe de calha metálica com gotas de água — imagem ilustrativa',
      label: "Limpeza de calhas", icon: 'Sparkles',
      short: "Limpeza de calhas para retirar folhas e sujeira acumuladas.",
      intro: "Limpeza de calhas e tubos de queda para retirar folhas, terra e outros resíduos acumulados que atrapalham a passagem da água.",
      checklist: ["Comprimento aproximado das calhas", "Altura e acesso ao telhado", "Presença de árvores próximas", "Fotos das calhas"],
      faq: [{ q: "De quanto em quanto tempo limpar as calhas?", a: "Varia conforme o local e a presença de árvores por perto. Peça à empresa uma orientação para o seu caso." }],
    },
  },
}
