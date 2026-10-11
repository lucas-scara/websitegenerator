import meta from './segment.json'

/*
 * Segment preset: what a glazier (vidraçaria) *may* offer. Only services listed in the business
 * `enabled_services` are rendered. Copy describes the service in general terms and never states facts
 * about a specific company (prices, deadlines, guarantees, certifications, standards, availability, brands).
 * Illustrative stock photographs (see stock-images.json) are bundled; services without a photo fall back to the themed design.
 */
export default {
  ...meta,
  hero: {
    title: 'Vidraçaria',
    titleNoCity: 'Vidraçaria',
    flourishNoCity: 'vidros sob medida',
    image: meta.hero_image,
    alt: 'Box de vidro transparente em banheiro de mármore claro (imagem ilustrativa)',
  },
  servicesHeading: { title: 'Serviços de vidraçaria', flourish: 'para casa e comércio.' },
  process: [
    { title: 'Envie as medidas', text: 'Informe o tipo de serviço e as medidas do vão, ou mande uma foto do local.' },
    { title: 'Escolha o vidro e o acabamento', text: 'Defina tipo de vidro, cor e ferragens, tirando dúvidas direto com a empresa.' },
    { title: 'Receba o orçamento', text: 'Peça o orçamento com o que está incluso e o prazo antes de contratar o serviço.' },
  ],
  services: {
    'shower-enclosures': {
      image: '/images/vidracaria/shower-enclosures.jpg',
      alt: 'Box de vidro transparente em banheiro com revestimento claro — imagem ilustrativa',
      label: "Box para banheiro", icon: 'ShowerHead',
      short: "Box de vidro sob medida para o banheiro, com diferentes tipos de abertura.",
      intro: "Box para banheiro em vidro, feito conforme as medidas do espaço, com opções de abertura como porta de giro, de correr ou fixo.",
      checklist: ["Medidas do vão (largura e altura)", "Tipo de abertura desejada (giro, correr, fixo)", "Cor do vidro (incolor, fumê, jateado) e das ferragens", "Foto do banheiro e do local do box"],
      faq: [{ q: "Quem tira as medidas do box?", a: "Em geral o orçamento começa com as medidas e uma foto do vão. Pergunte se a empresa faz a medição no local antes de fechar o pedido." }],
    },
    'mirrors': {
      image: '/images/vidracaria/mirrors.jpg',
      alt: 'Espelho redondo com moldura fina em parede clara — imagem ilustrativa',
      label: "Espelhos", icon: 'RectangleVertical',
      short: "Espelhos sob medida para banheiro, sala, quarto e comércio.",
      intro: "Espelhos cortados sob medida para banheiros, salas, quartos, closets e lojas, em diferentes formatos e acabamentos de borda.",
      checklist: ["Medidas aproximadas e formato (retangular, redondo, orgânico)", "Ambiente onde será instalado", "Tipo de acabamento (borda lapidada, bisotê, moldura)", "Foto da parede"],
      faq: [{ q: "Dá para pedir espelho em formato diferente?", a: "Em geral é possível cortar em vários formatos, como redondo ou orgânico. Envie as medidas e uma foto do ambiente e peça orientação." }],
    },
    'glass-doors': {
      image: '/images/vidracaria/glass-doors.jpg',
      alt: 'Porta de vidro de correr com perfis escuros — imagem ilustrativa',
      label: "Portas de vidro", icon: 'DoorClosed',
      short: "Portas de vidro de abrir ou de correr para ambientes internos e comerciais.",
      intro: "Portas de vidro de giro ou de correr para casas, escritórios e comércios, conforme o tipo de ambiente e o vão disponível.",
      checklist: ["Medidas do vão e se há batente ou trilho", "Tipo de abertura (giro ou correr)", "Cor do vidro e das ferragens", "Foto do local"],
      faq: [{ q: "Qual a diferença entre porta de giro e de correr?", a: "A de giro precisa de espaço para abrir; a de correr ocupa o vão lateral. A escolha depende do espaço disponível e do uso do ambiente." }],
    },
    'glass-replacement': {
      image: '/images/vidracaria/glass-replacement.jpg',
      alt: 'Janela aberta em parede clara com moldura de madeira — imagem ilustrativa',
      label: "Troca de vidros", icon: 'Square',
      short: "Troca de vidros quebrados ou trincados em portas, janelas e outros vãos.",
      intro: "Reposição de vidros quebrados, trincados ou riscados em janelas, portas e outras peças, de acordo com o tipo de vidro e a esquadria.",
      checklist: ["Medidas do vidro ou do vão", "Tipo de vidro atual (liso, canelado, temperado, laminado)", "Local onde está instalado (janela, porta, box)", "Foto da peça danificada"],
      faq: [{ q: "Preciso levar as medidas do vidro?", a: "Ajuda muito. Se não for possível medir, envie uma foto com uma referência de tamanho e peça orientação sobre como proceder." }],
    },
    'glass-guardrails': {
      image: '/images/vidracaria/glass-guardrails.jpg',
      alt: 'Guarda-corpo de vidro em varanda de edifício — imagem ilustrativa',
      label: "Guarda-corpos de vidro", icon: 'Fence',
      short: "Guarda-corpos de vidro para varandas, sacadas e escadas.",
      intro: "Guarda-corpos em vidro para varandas, sacadas, escadas e mezaninos, com diferentes tipos de fixação e acabamento.",
      checklist: ["Local de instalação (varanda, escada, mezanino)", "Comprimento e altura desejados", "Tipo de fixação (perfil, botão, chumbado)", "Foto do local e, em condomínio, se há regras do prédio"],
      faq: [{ q: "Condomínios têm regras para guarda-corpo?", a: "Muitos condomínios têm regras próprias sobre alterações em fachada e varanda. Confira com a administração antes de pedir o orçamento." }],
    },
    'balcony-enclosures': {
      image: '/images/vidracaria/balcony-enclosures.jpg',
      alt: 'Varandas de edifício fechadas com vidro — imagem ilustrativa',
      label: "Fechamento de sacadas", icon: 'PanelTop',
      short: "Fechamento de sacadas e varandas com vidro.",
      intro: "Fechamento de sacadas e varandas com vidro, em sistemas de correr ou de recolher, conforme o espaço e as regras do condomínio.",
      checklist: ["Medidas da sacada (largura e altura)", "Se o imóvel é em condomínio e se há padrão de fachada", "Tipo de sistema desejado", "Foto da sacada"],
      faq: [{ q: "Preciso de autorização do condomínio?", a: "Em edifícios é comum haver regras sobre o fechamento de sacadas. Verifique com a administração antes de contratar o serviço." }],
    },
    'aluminum-frames': {
      image: '/images/vidracaria/aluminum-frames.jpg',
      alt: 'Porta com esquadria escura e vidro — imagem ilustrativa',
      label: "Esquadrias de alumínio", icon: 'Frame',
      short: "Esquadrias de alumínio para portas, janelas e vãos.",
      intro: "Esquadrias de alumínio para portas, janelas e divisórias, nas cores e perfis disponíveis, feitas conforme as medidas do vão.",
      checklist: ["Medidas do vão e quantidade de peças", "Tipo de esquadria (porta, janela, divisória)", "Cor do alumínio e do vidro", "Foto do local e se é obra nova ou substituição"],
      faq: [{ q: "Dá para trocar a esquadria antiga?", a: "Em geral sim. Informe as medidas do vão e se a esquadria atual será retirada, e peça orientação sobre o procedimento." }],
    },
    'windows': {
      image: '/images/vidracaria/windows.jpg',
      alt: 'Ambiente com janelas de vidro e esquadrias escuras — imagem ilustrativa',
      label: "Janelas", icon: 'AppWindow',
      short: "Janelas de vidro de abrir, de correr e fixas.",
      intro: "Janelas de vidro de correr, de abrir ou fixas para casas, apartamentos e comércios, conforme o ambiente e o vão.",
      checklist: ["Medidas do vão e número de folhas", "Tipo de abertura (correr, abrir, maxim-ar, fixa)", "Cor da esquadria e tipo de vidro", "Foto do local"],
      faq: [{ q: "Posso pedir janelas de modelos diferentes?", a: "Sim, é possível pedir orçamento para vários ambientes. Informe o tipo de abertura de cada um e envie as medidas." }],
    },
  },
}
