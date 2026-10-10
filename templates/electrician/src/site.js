import { enabledItems, isServiceEnabled } from './services.js'
import { asset } from './business.js'
import { BUSINESS } from './business.js'
export const SITE = BUSINESS


/* Primary navigation — mirrors the original site's menu hierarchy */
const ALL_NAV = [
  { label: "Início", href: '/' },
  {
    label: "Serviços",
    href: '/services',
    children: [
      { label: "Reparos elétricos", href: '/electrical-repairs', blurb: "Entre em contato para conversar sobre suas necessidades." },
      {
        label: "Instalações elétricas",
        href: '/electrical-installation',
        blurb: "Iluminação, tomadas e novas instalações",
        children: [
          { label: "Dispositivo DR", href: '/rcd-protection' },
          { label: "Instalação de quadro elétrico", href: '/electrical-enclosures' },
          { label: "Troca de quadro elétrico", href: '/consumer-units' },
        ],
      },
      {
        label: "Reforma elétrica",
        href: '/rewiring',
        blurb: "Atualização elétrica para sua casa",
        children: [
          { label: "Projetos elétricos", href: '/electrical-contracting' },
          { label: "Ampliações", href: '/extensions' },
          { label: "Reforma completa", href: '/renovations' },
        ],
      },
      { label: "Manutenção elétrica", href: '/maintenance', blurb: "Cuidados com a instalação elétrica" },
      { label: "Carregador para veículo elétrico", href: '/ev-charging', blurb: "Instalação de carregadores para veículos elétricos" },
    ],
  },
  { label: "Orçamentos", href: '/pricing' },
  { label: "Inspiração", href: '/inspiration' },
  { label: "Sobre", href: '/about' },
  { label: "Contato", href: '/contact' },
]

/* Footer menu — identical items/labels to the original footer (legacy hrefs resolved to their redirect targets) */
const ALL_FOOTER_MENU = [
  { label: "Início", href: '/' },
  { label: "Serviços", href: '/services' },
  { label: "Reforma completa", href: '/renovations' },
  { label: "Reparos elétricos", href: '/electrical-repairs' },
  { label: "Instalações elétricas", href: '/electrical-installation' },
  { label: "Eletricista", href: '/maintenance' },
  { label: "Pontos de recarga", href: '/ev-charging' },
  { label: "Inspiração", href: '/inspiration' },
  { label: "Ampliações", href: '/extensions' },
  { label: "Orçamentos", href: '/pricing' },
  { label: "Contato", href: '/contact' },
]

/* Local landing pages */
export const AREAS = { elektriker: [{label: 'Serviços elétricos na região', href: '/contact'}], installatoer: [], renovering: [] }

/* The six service cards from the original front page (labels, blurbs, images and targets verbatim) */
const ALL_HOME_SERVICES = [
  {
    title: "Reparos elétricos",
    text: "Converse conosco sobre falhas, quedas de energia e necessidades elétricas em casa.",
    href: '/electrical-repairs',
    image: asset("/images/panel-testing.jpg"),
    alt: "Quadro elétrico — imagem ilustrativa",
    icon: 'Siren',
  },
  {
    title: "Ampliações",
    text: "Instalações elétricas para novos espaços e ampliações residenciais.",
    href: '/extensions',
    image: asset("/images/house-dusk.jpg"),
    alt: "Casa iluminada ao anoitecer — imagem ilustrativa",
    icon: 'HousePlus',
  },
  {
    title: "Reforma completa",
    text: "Atualização de instalações elétricas em reformas residenciais.",
    href: '/renovations',
    image: asset("/images/interior.jpg"),
    alt: "Cozinha renovada — imagem ilustrativa",
    icon: 'Hammer',
  },
  {
    title: "Manutenção elétrica",
    text: "Serviços elétricos residenciais com atenção à qualidade e à segurança.",
    href: '/maintenance',
    image: asset("/images/electrician.jpg"),
    alt: "Eletricista com ferramentas — imagem ilustrativa",
    icon: 'Wrench',
  },
  {
    title: "Carregadores para veículos elétricos",
    text: "Instalação de carregadores para veículos elétricos em residências.",
    href: '/ev-charging',
    image: asset("/images/ev-charging.jpg"),
    alt: "Recarga de veículo elétrico — imagem ilustrativa",
    icon: 'BatteryCharging',
  },
  {
    title: "Instalações elétricas",
    text: "Instalações elétricas para diferentes necessidades residenciais.",
    href: '/electrical-installation',
    image: asset("/images/cafe-lighting.jpg"),
    alt: "Luminárias decorativas — imagem ilustrativa",
    icon: 'Plug',
  },
]

/* Project gallery (from /inspiration) */
const ALL_GALLERY = [
  { src: asset("/images/pendant.jpg"), alt: "Luminária pendente — imagem ilustrativa", category: "Iluminação", service: "/electrical-installation" },
  { src: asset("/images/outdoor-lighting.jpg"), alt: "Iluminação de jardim — imagem ilustrativa", category: "Áreas externas", service: "/electrical-installation" },
  { src: asset("/images/lamp-detail.jpg"), alt: "Detalhe de luminária — imagem ilustrativa", category: "Iluminação", service: "/electrical-installation" },
  { src: asset("/images/interior.jpg"), alt: "Iluminação de cozinha — imagem ilustrativa", category: "Interiores", service: "/electrical-installation" },
  { src: asset("/images/ev-charging.jpg"), alt: "Recarga de veículo elétrico — imagem ilustrativa", category: "Recarga de veículos elétricos", service: "/ev-charging" },
  { src: asset("/images/cafe-lighting.jpg"), alt: "Luminárias de vidro — imagem ilustrativa", category: "Iluminação", service: "/electrical-installation" },
  { src: asset("/images/house-dusk.jpg"), alt: "Casa ao anoitecer — imagem ilustrativa", category: "Áreas externas", service: "/electrical-installation" },
]
const ALL_GALLERY_FILTERS = ["Todos", "Iluminação", "Interiores", "Áreas externas", "Recarga de veículos elétricos"]

export const TRUST_STATS = [
  { value: 'Cuidado', label: 'em cada detalhe' },
  { value: 'Qualidade', label: 'no trabalho' },
  { value: 'Clareza', label: 'na comunicação' },
  { value: 'Local', label: 'atendimento' },
]

export const BADGES = []

/* Old-site paths that 301'd — preserved as client-side redirects */
export const REDIRECTS = {}

export const GALLERY = ALL_GALLERY.filter((item) => !item.service || isServiceEnabled(item.service))
function visibleNavChildren(children) {
  return children.flatMap((child) => {
    const nested = child.children ? enabledItems(child.children) : []
    return isServiceEnabled(child.href)
      ? [{ ...child, ...(child.children ? { children: nested } : {}) }]
      : nested // Keep verified child services visible when their parent service is off.
  })
}
export const NAV = ALL_NAV.filter((item) => item.href !== '/inspiration' || GALLERY.length).map((item) => item.children ? { ...item, children: visibleNavChildren(item.children) } : item)
export const FOOTER_MENU = enabledItems(ALL_FOOTER_MENU).filter((item) => item.href !== '/inspiration' || GALLERY.length)
export const HOME_SERVICES = enabledItems(ALL_HOME_SERVICES)
export const GALLERY_FILTERS = ALL_GALLERY_FILTERS.filter((label) => label === 'Todos' || GALLERY.some((item) => item.category === label))
