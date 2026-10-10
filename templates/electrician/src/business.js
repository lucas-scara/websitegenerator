const input = window.WEBSITE_BUSINESS || {}
export const BUSINESS = {
  name: 'Sua Empresa de Elétrica', phone: 'Entre em contato', email: 'Entre em contato',
  street: 'Entre em contato para confirmar a área atendida', zip: '', city: '', cvr: '', authNumber: '', ean: '',
  hours: [['Disponibilidade', 'Consulte-nos']], hoursNote: 'Entre em contato para combinar um horário.',
  certLine: 'Serviços elétricos para residências e empresas.', facebook: '', facebookPageId: '', privacy: '', cookies: '', elfsightClass: '', mapQuery: '',
  ...input,
  address: [input.street, input.zip, input.city].filter(Boolean).join(', ') || 'Entre em contato para confirmar a área atendida',
  domain: window.location.origin + (window.WEBSITE_BASE || ''),
  phoneHref: input.phone ? 'tel:' + input.phone.replace(/[^+0-9]/g, '') : (window.WEBSITE_BASE || '') + '/contact',
  emailHref: input.email ? 'mailto:' + input.email : (window.WEBSITE_BASE || '') + '/contact',
}
export function copy(text) {
  return text.replaceAll('Your Company', BUSINESS.name)
    .replaceAll('Your phone', BUSINESS.phone).replaceAll('Your email', BUSINESS.email)
}

export function asset(path) { return (window.WEBSITE_BASE || "") + path }
