import { Phone, Mail, MapPin, Clock } from 'lucide-react'
import { SITE, AREA } from '../site.js'
import { channels, formatPhone } from '../business.js'
import { WhatsAppIcon } from './Icons.jsx'
import QuoteForm from './QuoteForm.jsx'
import Reveal from '../lib/Reveal.jsx'

const ICONS = { whatsapp: WhatsAppIcon, phone: Phone, email: Mail }
const LABELS = { whatsapp: 'WhatsApp', phone: 'Telefone', email: 'E-mail' }

/* Closing contact block: verified channels, area/hours when known, and the message composer. */
export default function ContactSection({ heading = 'Fale com a gente', service, id = 'contato' }) {
  const rows = [
    ...channels(service).map((c) => ({ Icon: ICONS[c.kind], label: LABELS[c.kind], value: c.kind === 'email' ? SITE.email : c.kind === 'whatsapp' ? formatPhone(SITE.whatsapp) : SITE.phone, href: c.href, external: c.external })),
    SITE.address && { Icon: MapPin, label: 'Endereço', value: SITE.address },
    (SITE.serviceArea || !SITE.address) && AREA && { Icon: MapPin, label: 'Atendimento', value: AREA },
    SITE.hours && { Icon: Clock, label: 'Horário', value: SITE.hours },
  ].filter(Boolean)
  return (
    <section id={id} className="relative py-24 sm:py-32 px-6 sm:px-10 lg:px-16 bg-background overflow-hidden scroll-mt-24">
      <div className="absolute -top-24 right-0 h-72 w-72 rounded-full bg-primary/10 blur-3xl pointer-events-none" />
      <div className="max-w-7xl mx-auto grid lg:grid-cols-12 gap-10 lg:gap-16">
        <div className="lg:col-span-5">
          <Reveal>
            <span className="font-mono text-[11px] sm:text-xs uppercase tracking-[0.28em] text-primary-dark">╱ Contato</span>
            <h2 className="font-display font-extrabold text-4xl sm:text-5xl md:text-6xl text-ink mt-4 leading-[1.04] tracking-tight">{heading}</h2>
            <p className="text-muted text-lg mt-6 leading-relaxed max-w-md">
              Conte o que precisa{SITE.whatsapp ? ' pelo WhatsApp' : ''} e peça seu orçamento.
            </p>
          </Reveal>
          <div className="mt-10 space-y-4">
            {rows.map(({ Icon, label, value, href, external }, i) => {
              const inner = (
                <>
                  <span className="h-12 w-12 shrink-0 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-primary-dark" />
                  </span>
                  <span className="min-w-0">
                    <span className="block font-mono text-[10px] uppercase tracking-widest text-muted">{label}</span>
                    <span className="font-display font-semibold text-ink text-lg break-words">{value}</span>
                  </span>
                </>
              )
              return (
                <Reveal key={label} delay={i * 80}>
                  {href
                    ? <a href={href} {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})} className="lift-on-hover flex items-center gap-4">{inner}</a>
                    : <div className="flex items-center gap-4">{inner}</div>}
                </Reveal>
              )
            })}
          </div>
        </div>
        <div className="lg:col-span-7">
          <Reveal delay={120}><QuoteForm id="orcamento" service={service} /></Reveal>
        </div>
      </div>
    </section>
  )
}
