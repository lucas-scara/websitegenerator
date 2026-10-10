import catalog from '../service-catalog.json'
import { BUSINESS } from './business.js'

export const SERVICE_CATALOG = catalog
const enabled = new Set(Array.isArray(BUSINESS.enabled_services) ? BUSINESS.enabled_services : [])
export const enabledServiceIds = Object.keys(catalog).filter((id) => enabled.has(id))
const serviceByPath = Object.fromEntries(Object.entries(catalog).map(([id, path]) => [path, id]))

export function isServiceEnabled(path) {
  const id = serviceByPath[path]
  return !id || enabled.has(id)
}

export function enabledItems(items) {
  return items.filter((item) => isServiceEnabled(item.href))
}
