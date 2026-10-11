const input = window.WEBSITE_BUSINESS || {}
const base = window.WEBSITE_BASE || ''
const digits = (value) => String(value || '').replace(/\D/g, '')
const text = (value) => (typeof value === 'string' ? value.trim() : '')

/* Brazilian numbers become 55 + DDD + number; explicit international numbers keep their country code. */
export function toWhatsApp(raw) {
  const value = text(raw)
  if (!value) return ''
  let d = digits(value)
  if (value.startsWith('+')) return d.length >= 10 && d.length <= 15 ? d : ''
  d = d.replace(/^0+/, '')
  if (d.startsWith('55') && (d.length === 12 || d.length === 13)) return d
  if (d.length === 10 || d.length === 11) return '55' + d
  return ''
}

/* (14) 99999-9999 for Brazilian numbers; anything else is shown as supplied. */
export function formatPhone(raw) {
  const value = text(raw)
  const n = toWhatsApp(value)
  if (!n.startsWith('55')) return value
  const local = n.slice(2)
  const ddd = local.slice(0, 2)
  const rest = local.slice(2)
  return `(${ddd}) ${rest.slice(0, rest.length - 4)}-${rest.slice(-4)}`
}

const phone = text(input.phone)
const phoneDigits = toWhatsApp(phone)
// The scraped public phone is presumed to be WhatsApp unless the operator says otherwise (AGENTS.md).
const whatsapp = input.whatsapp === false ? '' : toWhatsApp(input.whatsapp) || phoneDigits
const email = text(input.email)
const city = text(input.city)
const state = text(input.state).toUpperCase()
const street = text(input.street)
const zip = text(input.zip)

export const BUSINESS = {
  name: text(input.name) || 'Sua empresa',
  phone: phone ? formatPhone(phone) : '',
  phoneHref: phone ? 'tel:' + (phoneDigits ? '+' + phoneDigits : phone.replace(/[^+0-9]/g, '')) : '',
  whatsapp,
  email,
  emailHref: email ? 'mailto:' + email : '',
  street,
  zip,
  city,
  state,
  place: [city, state].filter(Boolean).join('/'),
  address: street ? [street, [city, state].filter(Boolean).join(' - '), zip].filter(Boolean).join(', ') : '',
  serviceArea: text(input.service_area),
  hours: text(input.hours),
  cnpj: text(input.cnpj),
  about: text(input.about),
  instagram: text(input.instagram),
  paymentMethods: Array.isArray(input.payment_methods) ? input.payment_methods.filter((m) => typeof m === 'string' && m.trim()) : [],
  foundedYear: Number.isInteger(input.founded_year) ? input.founded_year : null,
  google: input.google_rating && input.google_reviews_url ? { rating: Number(input.google_rating), count: Number(input.google_reviews_count) || 0, url: input.google_reviews_url } : null,
  reviews: Array.isArray(input.reviews) ? input.reviews.filter((r) => r && r.author && r.text && r.source_url) : [],
  enabled_services: Array.isArray(input.enabled_services) ? input.enabled_services : [],
  preview: input.preview !== false,
  domain: window.location.origin + base,
}

export function whatsappHref(message) {
  if (!BUSINESS.whatsapp) return ''
  return `https://wa.me/${BUSINESS.whatsapp}` + (message ? `?text=${encodeURIComponent(message)}` : '')
}

/* Default opening message; mentions the service when the visitor is on a service page. */
export function whatsappMessage(service) {
  return `Olá, ${BUSINESS.name}! Encontrei o site de vocês e gostaria de pedir um orçamento` + (service ? ` para ${service.toLowerCase()}.` : '.')
}

/* Ordered, verified contact channels. The first one is the primary call to action. */
export function channels(service) {
  return [
    BUSINESS.whatsapp && { kind: 'whatsapp', label: 'Pedir orçamento no WhatsApp', short: 'WhatsApp', href: whatsappHref(whatsappMessage(service)), external: true },
    BUSINESS.phoneHref && { kind: 'phone', label: 'Ligar ' + BUSINESS.phone, short: 'Ligar', href: BUSINESS.phoneHref },
    BUSINESS.emailHref && { kind: 'email', label: 'Enviar e-mail', short: 'E-mail', href: BUSINESS.emailHref },
  ].filter(Boolean)
}

export function asset(path) { return base + path }
