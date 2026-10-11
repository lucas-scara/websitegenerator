import { BUSINESS } from './business.js'
import { SERVICES, SEGMENT } from './services.js'

export const SITE = BUSINESS
export { SERVICES, SEGMENT }

export const HOME_SERVICES = SERVICES.slice(0, 6)

export const NAV = [
  { label: 'Início', href: '/' },
  ...(SERVICES.length ? [{ label: 'Serviços', href: '/servicos', children: SERVICES.map((s) => ({ label: s.label, href: s.href, blurb: s.short })) }] : []),
  { label: 'Contato', href: '/contato' },
]

export const FOOTER_MENU = [
  { label: 'Início', href: '/' },
  ...(SERVICES.length ? [{ label: 'Serviços', href: '/servicos' }] : []),
  ...SERVICES.map((s) => ({ label: s.label, href: s.href })),
  { label: 'Contato', href: '/contato' },
]

/* Old English/Danish paths from earlier previews resolve to the Portuguese routes, never to disabled services. */
const known = new Set(['/contato', ...(SERVICES.length ? ['/servicos'] : []), ...SERVICES.map((s) => s.href)])
export const REDIRECTS = Object.fromEntries(
  Object.entries(SEGMENT.legacy_paths).map(([from, to]) => [from, known.has(to) ? to : '/'])
)

/* Display helpers shared by the hero, footer and contact blocks. */
export const AREA = BUSINESS.serviceArea || BUSINESS.place
export const SEO_TITLE = (BUSINESS.city ? SEGMENT.seo_title : SEGMENT.seo_title_no_city)
  .replace('{noun}', SEGMENT.noun).replace('{city}', BUSINESS.city).replace('{name}', BUSINESS.name)
export const SEO_DESCRIPTION = (BUSINESS.city ? SEGMENT.seo_description : SEGMENT.seo_description_no_city)
  .replace('{activity}', SEGMENT.activity).replace('{city}', BUSINESS.city).replace('{name}', BUSINESS.name)
