import meta from './segment.json'

/*
 * Segment preset: what a locksmith (chaveiro) *may* offer. Only services listed in the business
 * `enabled_services` are rendered. Copy describes the service in general terms and never states facts
 * about a specific company (prices, deadlines, guarantees, certifications, availability, brands).
 * Illustrative stock photographs (see stock-images.json) are bundled; services without a photo fall back to the themed design.
 */
export default {
  ...meta,
  hero: {
    title: 'Chaveiro',
    titleNoCity: 'Chaveiro',
    flourishNoCity: 'chaves, fechaduras e portas',
    image: meta.hero_image,
    alt: 'Chave dentro do cilindro de uma fechadura (imagem ilustrativa)',
  },
  servicesHeading: { title: 'Serviços de chaveiro', flourish: 'para casa, carro e empresa.' },
  process: [
    { title: 'Conte o que precisa', text: 'Descreva a situação e o tipo de porta, fechadura ou chave envolvidos.' },
    { title: 'Envie uma foto', text: 'Uma foto da fechadura ou da chave ajuda a preparar o atendimento.' },
    { title: 'Receba o orçamento', text: 'Peça o orçamento com o que está incluso e o prazo antes de contratar o serviço.' },
  ],
  services: {
    'door-opening': {
      image: '/images/chaveiros/door-opening.jpg',
      alt: 'Chaves penduradas na fechadura de uma porta — imagem ilustrativa',
      label: "Abertura de portas", icon: 'DoorOpen',
      short: "Abertura de portas de casas, apartamentos e comércios quando a chave não está disponível.",
      intro: "Abertura de portas trancadas, como quando a chave foi esquecida, perdida ou quebrou na fechadura, buscando preservar o máximo possível a porta e o cilindro.",
      checklist: ["Tipo de porta (madeira, ferro, vidro)", "Tipo de fechadura ou trinco", "Se a chave está presa ou quebrada na fechadura", "Foto da fechadura e da porta"],
      faq: [{ q: "Preciso comprovar que o imóvel é meu?", a: "É comum que o profissional peça um comprovante de que você é morador ou responsável pelo local antes de abrir. Tenha um documento à mão." }],
    },
    'key-duplication': {
      image: '/images/chaveiros/key-duplication.jpg',
      alt: 'Chaves virgens organizadas sobre uma superfície escura — imagem ilustrativa',
      label: "Cópia de chaves", icon: 'KeyRound',
      short: "Cópias de chaves comuns, de segurança e tetra para casa e empresa.",
      intro: "Cópia de chaves de portas, portões, cadeados e armários, incluindo modelos de segurança e tetra, conforme o tipo de chave.",
      checklist: ["Leve a chave original ou envie uma foto dela", "Quantidade de cópias", "Tipo de chave (comum, tetra, segurança)", "Se a chave tem código ou restrição de cópia"],
      faq: [{ q: "Todas as chaves podem ser copiadas?", a: "A maioria sim, mas chaves com restrição de cópia ou códigos específicos podem exigir procedimento diferente. Envie uma foto para saber." }],
    },
    'lock-replacement': {
      image: '/images/chaveiros/lock-replacement.jpg',
      alt: 'Maçaneta de aço em porta escura — imagem ilustrativa',
      label: "Troca de fechaduras", icon: 'Lock',
      short: "Troca de fechaduras e miolos após perda de chave, mudança ou desgaste.",
      intro: "Troca de fechaduras e cilindros em portas internas e externas, seja por perda de chaves, mudança de endereço, desgaste ou defeito.",
      checklist: ["Motivo da troca (perda de chave, desgaste, defeito)", "Tipo de porta e de fechadura atual", "Se deseja trocar só o miolo ou a fechadura inteira", "Foto da fechadura, de frente e de lado"],
      faq: [{ q: "Dá para trocar só o miolo?", a: "Em muitos casos sim, conforme o modelo da fechadura. Envie uma foto para avaliar se basta trocar o cilindro." }],
    },
    'lock-installation': {
      image: '/images/chaveiros/lock-installation.jpg',
      alt: 'Porta de madeira clara com puxador e fechadura escura — imagem ilustrativa',
      label: "Instalação de fechaduras", icon: 'LockKeyhole',
      short: "Instalação de fechaduras, trincos e puxadores em portas novas ou existentes.",
      intro: "Instalação de fechaduras, trincos e reforços de segurança em portas de madeira, ferro, alumínio e vidro.",
      checklist: ["Tipo de porta e material", "Modelo de fechadura, se já comprou", "Quantidade de portas", "Medidas aproximadas ou foto da porta"],
      faq: [{ q: "Preciso já ter a fechadura?", a: "Não necessariamente. Você pode pedir orientação sobre o tipo mais adequado antes de comprar." }],
    },
    'car-keys': {
      image: '/images/chaveiros/car-keys.jpg',
      alt: 'Chave de carro com controle sobre uma superfície azul — imagem ilustrativa',
      label: "Chaves automotivas", icon: 'Car',
      short: "Cópia e programação de chaves e controles de veículos.",
      intro: "Serviços com chaves de veículos, como cópia de chaves, chaves com chip e reposição de controles, conforme a marca e o modelo do carro.",
      checklist: ["Marca, modelo e ano do veículo", "Se ainda existe uma chave original", "Tipo de chave (simples, com chip, canivete, presença)", "Documento do veículo, quando solicitado"],
      faq: [{ q: "É possível fazer chave de carro sem a original?", a: "Depende do modelo e da tecnologia da chave. Informe a marca, o modelo e o ano e peça orientação." }],
    },
    'digital-locks': {
      image: '/images/chaveiros/digital-locks.jpg',
      alt: 'Mão segurando um celular ao lado de uma fechadura eletrônica — imagem ilustrativa',
      label: "Fechaduras digitais", icon: 'Smartphone',
      short: "Instalação de fechaduras com senha, biometria ou aplicativo.",
      intro: "Instalação e configuração de fechaduras digitais, com acesso por senha, cartão, biometria ou aplicativo, em portas residenciais e comerciais.",
      checklist: ["Modelo da fechadura digital, se já comprou", "Tipo e espessura da porta", "Forma de acesso desejada (senha, biometria, aplicativo)", "Foto da porta e da fechadura atual"],
      faq: [{ q: "Qualquer porta aceita fechadura digital?", a: "Depende do material e da espessura da porta. Envie uma foto e as medidas para avaliar a compatibilidade." }],
    },
    'safes': {
      image: '/images/chaveiros/safes.jpg',
      alt: 'Porta de cofre com roda de travamento — imagem ilustrativa',
      label: "Cofres", icon: 'Vault',
      short: "Abertura, manutenção e instalação de cofres.",
      intro: "Serviços com cofres residenciais e comerciais, como abertura, manutenção de segredo e fechadura e instalação.",
      checklist: ["Tipo de cofre (embutir, sobrepor, digital, de chave)", "Marca e modelo, se souber", "Se perdeu a chave ou esqueceu o código", "Foto do cofre"],
      faq: [{ q: "Esqueci o código do cofre. Há o que fazer?", a: "Em muitos casos há procedimento próprio. Informe a marca e o modelo e peça orientação." }],
    },
  },
}
