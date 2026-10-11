import meta from './segment.json'

/*
 * Segment preset: what a climatização (air-conditioning) company *may* offer. Only services listed in the
 * business `enabled_services` are rendered. Copy describes the service in general terms and never
 * states facts about a specific company (prices, deadlines, guarantees, certifications, brands, savings).
 * Illustrative stock photographs (see stock-images.json) are bundled; services without a photo fall back to the themed design.
 */
export default {
  ...meta,
  hero: {
    title: 'Ar-condicionado',
    titleNoCity: 'Ar-condicionado',
    flourishNoCity: 'instalação e manutenção',
    image: meta.hero_image,
    alt: 'Unidade externa de ar-condicionado em parede de tijolos (imagem ilustrativa)',
  },
  servicesHeading: { title: 'Serviços de ar-condicionado', flourish: 'para casa e empresa.' },
  process: [
    { title: 'Conte o que precisa', text: 'Descreva o serviço e informe o tipo e a marca do aparelho, se já existir.' },
    { title: 'Envie fotos do local', text: 'Fotos do ambiente, da parede e do ponto da unidade externa ajudam a preparar a avaliação.' },
    { title: 'Receba o orçamento', text: 'Peça o orçamento com o que está incluso e o prazo antes de autorizar o serviço.' },
  ],
  services: {
    'split-installation': {
      image: '/images/climatizacao/split-installation.jpg',
      alt: 'Unidades externas de ar-condicionado em parede de tijolos — imagem ilustrativa',
      label: "Instalação de ar-condicionado", icon: 'Snowflake',
      short: "Instalação de aparelhos split em casas, apartamentos e comércios.",
      intro: "Instalação de ar-condicionado split, com fixação das unidades interna e externa, ligação elétrica, tubulação e dreno.",
      checklist: ["Modelo e capacidade do aparelho, se já comprou", "Cômodo e tamanho aproximado do ambiente", "Onde ficará a unidade externa", "Fotos da parede e do ponto de instalação"],
      faq: [{ q: "Preciso já ter o aparelho para pedir o orçamento?", a: "Não necessariamente. Informe o tamanho do ambiente e o uso, e peça orientação sobre a capacidade antes de comprar." }],
    },
    'preventive-maintenance': {
      image: '/images/climatizacao/maintenance.jpg',
      alt: 'Condensadoras de ar-condicionado em fachada — imagem ilustrativa',
      label: "Manutenção preventiva", icon: 'Fan',
      short: "Revisão periódica para manter o aparelho funcionando bem.",
      intro: "Revisão de aparelhos de ar-condicionado com verificação dos componentes, filtros, dreno e funcionamento geral.",
      checklist: ["Tipo e marca do aparelho", "Há quanto tempo foi a última revisão", "Quantidade de aparelhos", "Se notou barulho, cheiro ou queda de desempenho"],
      faq: [{ q: "Com que frequência fazer a manutenção?", a: "Depende do uso e do ambiente. Peça uma orientação ao descrever como o aparelho é utilizado." }],
    },
    'aircon-cleaning': {
      image: '/images/climatizacao/cleaning.jpg',
      alt: 'Mãos removendo a grade de um difusor de ar no teto — imagem ilustrativa',
      label: "Limpeza de ar-condicionado", icon: 'Sparkles',
      short: "Higienização das unidades interna e externa e dos filtros.",
      intro: "Limpeza de ar-condicionado com higienização de filtros, serpentina, bandeja de dreno e demais partes acessíveis.",
      checklist: ["Tipo do aparelho (split, janela, cassete)", "Quantidade de aparelhos", "Se há mau cheiro ou respingos de água", "Há quanto tempo foi a última limpeza"],
      faq: [{ q: "Que informações ajudam a organizar a limpeza?", a: "Quantidade e tipo de aparelhos, além de fotos das unidades, ajudam a preparar a visita." }],
    },
    'diagnostics-repair': {
      image: '/images/climatizacao/repair.jpg',
      alt: 'Condensadora de ar-condicionado em parede — imagem ilustrativa',
      label: "Conserto de ar-condicionado", icon: 'Wrench',
      short: "Avaliação e reparo de aparelhos que não gelam, vazam ou fazem barulho.",
      intro: "Avaliação de aparelhos com problemas, como falta de refrigeração, vazamento de água, ruídos ou falha ao ligar, e reparo conforme o caso.",
      checklist: ["O que o aparelho está fazendo", "Marca e modelo, se souber", "Se aparece código de erro no display", "Fotos ou vídeo curto do problema"],
      faq: [{ q: "O aparelho não gela: o que informar?", a: "Descreva o sintoma, a marca e o modelo, e envie fotos das unidades. Isso ajuda a preparar a avaliação." }],
    },
    'aircon-relocation': {
      image: '/images/climatizacao/relocation.jpg',
      alt: 'Unidade externa de ar-condicionado em suporte na parede — imagem ilustrativa',
      label: "Troca e remoção de aparelhos", icon: 'ThermometerSnowflake',
      short: "Retirada, mudança de local ou substituição de aparelhos.",
      intro: "Remoção de ar-condicionado, mudança do aparelho para outro ambiente ou endereço e substituição por um novo.",
      checklist: ["Se o aparelho será removido, trocado ou mudado de lugar", "Tipo e capacidade do aparelho atual", "Local atual e local novo", "Fotos das unidades e da instalação"],
      faq: [{ q: "É possível mudar o aparelho de lugar?", a: "Em geral sim, conforme a distância e as condições do local. Envie fotos do ponto atual e do novo." }],
    },
    'refrigeration-piping': {
      image: '/images/climatizacao/piping.jpg',
      alt: 'Tubulação metálica e unidades de ar-condicionado em fachada — imagem ilustrativa',
      label: "Infraestrutura e tubulação", icon: 'Cable',
      short: "Preparo de tubulação, dreno e pontos elétricos para o aparelho.",
      intro: "Execução de infraestrutura para ar-condicionado, como tubulação de cobre, dreno e pontos de energia, antes ou durante a instalação.",
      checklist: ["Distância entre as unidades interna e externa", "Se o imóvel está em obra ou já pronto", "Número de ambientes atendidos", "Fotos ou planta do local"],
      faq: [{ q: "Dá para deixar a infraestrutura pronta antes do aparelho?", a: "Sim, é comum em obras e reformas. Informe o número de ambientes e peça orientação." }],
    },
    'commercial-hvac': {
      image: '/images/climatizacao/commercial.jpg',
      alt: 'Equipe em cobertura com unidades de climatização — imagem ilustrativa',
      label: "Climatização comercial", icon: 'Building2',
      short: "Ar-condicionado para lojas, escritórios, clínicas e salas comerciais.",
      intro: "Instalação e manutenção de ar-condicionado em ambientes comerciais, com mais de um aparelho ou necessidades específicas de cada espaço.",
      checklist: ["Tipo de estabelecimento", "Quantidade de ambientes e aparelhos", "Se já existe sistema instalado", "Horário em que o local pode receber o serviço"],
      faq: [{ q: "Vocês atendem estabelecimentos com vários aparelhos?", a: "Informe a quantidade de ambientes e aparelhos ao pedir o orçamento para alinhar o atendimento." }],
    },
    'maintenance-contracts': {
      image: '/images/climatizacao/maintenance.jpg',
      alt: 'Condensadoras de ar-condicionado em fachada — imagem ilustrativa',
      label: "Contratos de manutenção", icon: 'ClipboardCheck',
      short: "Visitas periódicas combinadas para empresas e condomínios.",
      intro: "Manutenção contratada com visitas periódicas definidas em conjunto, para estabelecimentos e condomínios com vários aparelhos.",
      checklist: ["Quantidade e tipo de aparelhos", "Periodicidade desejada das visitas", "Tipo de imóvel ou estabelecimento", "Lista ou fotos dos equipamentos"],
      faq: [{ q: "Como funciona um contrato de manutenção?", a: "Periodicidade e escopo são combinados caso a caso. Informe os equipamentos para receber uma proposta." }],
    },
  },
}
