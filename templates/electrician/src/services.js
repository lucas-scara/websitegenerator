import catalog from '../services.json'
import { BUSINESS } from './business.js'

export const SERVICE_IDS = Object.keys(catalog)
const serviceByPath = new Map(Object.entries(catalog).map(([id, path]) => [path, id]))
const enabled = new Set(BUSINESS.enabled_services || [])

export function serviceEnabled(path) {
  const id = serviceByPath.get(path)
  return !id || enabled.has(id)
}

export function visibleServices(items) {
  return items.filter((item) => serviceEnabled(item.href))
}

export function visibleServiceText(items) {
  return items.filter((item) => [...item.matchAll(/\]\((\/[^)]+)\)/g)].every((match) => serviceEnabled(match[1])))
}
