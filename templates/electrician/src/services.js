import catalog from '../service-catalog.json'
import { BUSINESS, asset } from './business.js'
import SEGMENT from './segments/electrician.js'

export { SEGMENT }
export const SERVICE_CATALOG = catalog

/*
 * Single source for every service mention (menu, cards, routes, form, FAQ, footer, SEO).
 * Deny by default: an ID must exist in the catalog, in the preset and in enabled_services.
 */
const enabled = new Set(BUSINESS.enabled_services)
export const SERVICES = Object.entries(SEGMENT.services)
  .filter(([id]) => catalog[id] && enabled.has(id))
  .map(([id, s]) => ({ ...s, id, href: catalog[id], image: asset(s.image) }))
