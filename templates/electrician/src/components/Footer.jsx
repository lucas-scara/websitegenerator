import { Link } from 'react-router-dom'
import { Phone, Mail, MapPin, Clock } from 'lucide-react'
import { SITE, FOOTER_MENU, AREA, SEGMENT } from '../site.js'
import { formatPhone, whatsappHref, whatsappMessage } from '../business.js'
import { ContactBtns } from './Buttons.jsx'
import { WhatsAppIcon, InstagramIcon } from './Icons.jsx'
import Reveal from '../lib/Reveal.jsx'
import Logo from './Logo.jsx'

function instagramHref(value) {
  if (/^https:\/\/(www\.)?instagram\.com\//.test(value)) return value
  const handle = value.replace(/^@/, '')
  return /^[A-Za-z0-9._]{1,30}$/.test(handle) ? `https://instagram.com/${handle}` : ''
}

export default function Footer() {
  const insta = SITE.instagram && instagramHref(SITE.instagram)
  const contacts = [
    SITE.whatsapp && { Icon: WhatsAppIcon, label: 'WhatsApp', value: formatPhone(SITE.whatsapp), href: whatsappHref(whatsappMessage()), external: true },
    SITE.phoneHref && { Icon: Phone, label: 'Telefone', value: SITE.phone, href: SITE.phoneHref },
    SITE.email && { Icon: Mail, label: 'E-mail', value: SITE.email, href: SITE.emailHref },
    SITE.address && { Icon: MapPin, label: 'Endereço', value: SITE.address },
    (SITE.serviceArea || !SITE.address) && AREA && { Icon: MapPin, label: 'Atendimento', value: AREA },
    SITE.hours && { Icon: Clock, label: 'Horário', value: SITE.hours },
    insta && { Icon: InstagramIcon, label: 'Instagram', value: SITE.instagram.replace(/^https:\/\/(www\.)?instagram\.com\//, '@').replace(/\/$/, ''), href: insta, external: true },
  ].filter(Boolean)

  return (
    <footer className="relative bg-deep text-white rounded-t-6xl mt-8 overflow-hidden">
      <div className="absolute inset-0 grid-bg opacity-15" />
      <div className="absolute -top-32 left-1/2 -translate-x-1/2 h-64 w-[40rem] rounded-full bg-primary/20 blur-3xl" />

      <div className="relative px-6 sm:px-10 lg:px-16 pt-20 pb-28 lg:pb-10 max-w-7xl mx-auto">
        <Reveal className="border-b border-white/10 pb-12 mb-12">
          <h2 className="font-display font-extrabold text-4xl sm:text-6xl leading-[0.98] tracking-tight max-w-3xl">
            {SEGMENT.noun}{SITE.city ? ` em ${SITE.city}` : ''}
            <span className="font-serif italic font-medium text-primary-light block">peça seu orçamento.</span>
          </h2>
          <ContactBtns className="mt-8" onDark />
        </Reveal>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-4">
            <div className="mb-5"><Logo tone="light" size="lg" /></div>
            {SITE.cnpj && <p className="text-white/70 text-sm">CNPJ {SITE.cnpj}</p>}
            {SITE.paymentMethods.length > 0 && (
              <p className="text-white/55 text-sm mt-4">Pagamento: {SITE.paymentMethods.join(', ')}</p>
            )}
          </div>

          <div className="lg:col-span-5">
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-primary-light mb-4">Contato</p>
            <ul className="space-y-3 text-sm">
              {contacts.map(({ Icon, label, value, href, external }) => (
                <li key={label} className="flex items-start gap-3">
                  <Icon className="h-4 w-4 mt-0.5 shrink-0 text-primary-light" />
                  <span className="min-w-0">
                    <span className="block text-white/40 text-xs">{label}</span>
                    {href
                      ? <a href={href} {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})} className="text-white/85 hover:text-primary-light transition break-words">{value}</a>
                      : <span className="text-white/85 break-words">{value}</span>}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-3">
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-primary-light mb-4">Navegação</p>
            <ul className="space-y-2">
              {FOOTER_MENU.map((m) => (
                <li key={m.href}><Link to={m.href} className="text-sm text-white/75 hover:text-primary-light transition">{m.label}</Link></li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-14 pt-8 border-t border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-3 text-white/50 text-xs">
          <span>© {new Date().getFullYear()} {SITE.name}</span>
          {SITE.preview && <span>Prévia demonstrativa · imagens meramente ilustrativas</span>}
        </div>
      </div>
    </footer>
  )
}
