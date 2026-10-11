import { Link } from 'react-router-dom'
import { ArrowRight, MapPin, Clock, Star, CalendarCheck, CreditCard } from 'lucide-react'
import { asset } from '../business.js'
import { SITE, SERVICES, HOME_SERVICES, SEGMENT, AREA, SEO_TITLE, SEO_DESCRIPTION } from '../site.js'
import { useSEO } from '../lib/useSEO.js'
import Reveal from '../lib/Reveal.jsx'
import QuoteForm from '../components/QuoteForm.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import ServicesGrid from '../components/ServicesGrid.jsx'
import FAQ from '../components/FAQ.jsx'
import Reviews from '../components/Reviews.jsx'
import { Btn, ContactBtns } from '../components/Buttons.jsx'
import ProcessStack from '../components/ProcessStack.jsx'
import ContactSection from '../components/ContactSection.jsx'
import { HeroMark } from '../components/Logo.jsx'

const listLabels = (items) => {
  const names = items.map((s) => s.label.toLowerCase())
  return names.length > 1 ? names.slice(0, -1).join(', ') + ' e ' + names.at(-1) : names[0] || ''
}

/* Verified proof points. Payment joins the proof bar only when there is another fact beside it;
   alone it becomes a hero pill, so the bar never shows a single sparse item on desktop. */
function proofFacts() {
  const base = [
    SITE.google && { Icon: Star, value: SITE.google.rating.toFixed(1).replace('.', ','), label: SITE.google.count ? `${SITE.google.count} avaliações no Google` : 'nota no Google', href: SITE.google.url },
    SITE.foundedYear && { Icon: CalendarCheck, value: `Desde ${SITE.foundedYear}`, label: 'em atividade' },
  ].filter(Boolean)
  const pay = SITE.paymentMethods.length > 0
  if (base.length && pay) return { facts: [...base, { Icon: CreditCard, value: 'Pagamento', label: SITE.paymentMethods.join(', ') }], payPill: false }
  return { facts: base, payPill: pay }
}

function Hero() {
  const featured = SERVICES.slice(0, 3)
  const chips = [
    AREA && { Icon: MapPin, text: `Atende ${AREA}` },
    SITE.hours && { Icon: Clock, text: SITE.hours },
    proofFacts().payPill && { Icon: CreditCard, text: `Pagamento: ${SITE.paymentMethods.join(', ')}` },
  ].filter(Boolean)

  // Long single words (e.g. "Ar-condicionado") would overflow the hero column at the largest size.
  const heroTitle = SITE.city ? SEGMENT.hero.title : SEGMENT.hero.titleNoCity
  const longest = Math.max(...heroTitle.split(/[\s-]+/).map((w) => w.length))
  const titleSize = longest >= 12 ? 'text-4xl sm:text-6xl lg:text-7xl' : 'text-5xl sm:text-7xl lg:text-8xl'

  return (
    <section className="relative min-h-[88svh] lg:min-h-[100dvh] w-full overflow-hidden bg-deep rounded-b-5xl sm:rounded-b-6xl">
      <div className="absolute inset-0">
        {SEGMENT.hero.image
          ? <img src={asset(SEGMENT.hero.image)} alt={SEGMENT.hero.alt} className="w-full h-full object-cover object-center" fetchPriority="high" />
          : <>
              <div className="absolute inset-0 grid-bg opacity-20" />
              <HeroMark className="absolute -right-16 top-1/2 -translate-y-1/2 h-[120%] max-h-[900px] w-auto opacity-60" />
            </>}
        <div className="absolute inset-0 bg-gradient-to-tr from-deep/95 via-deep/65 to-primary/20" />
        <div className="absolute inset-0 bg-gradient-to-t from-deep via-deep/30 to-transparent" />
      </div>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 right-[18%] h-2 w-2 rounded-full bg-accent/70 animate-float" />
        <div className="absolute top-[55%] right-[10%] h-1.5 w-1.5 rounded-full bg-white/40 animate-float" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-[40%] right-[26%] h-1 w-1 rounded-full bg-primary-light/70 animate-float" style={{ animationDelay: '3s' }} />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 pt-28 sm:pt-36 lg:pt-40 pb-16 sm:pb-24 min-h-[88svh] lg:min-h-[100dvh] grid lg:grid-cols-12 gap-10 lg:gap-12 items-center">
        <div className="lg:col-span-7">
          {SITE.place && (
            <p className="rise inline-flex items-center gap-2 font-mono text-[11px] sm:text-xs uppercase tracking-[0.25em] text-primary-light">
              <span className="h-1.5 w-1.5 rounded-full bg-accent" /> {SITE.name} · {SITE.place}
            </p>
          )}
          <h1 className="font-display font-extrabold text-white leading-[0.95] tracking-tight mt-5">
            <span className={`rise block ${titleSize}`}>{heroTitle}</span>
            <span className={`rise block font-serif italic font-medium text-primary-light ${titleSize} mt-1`} style={{ lineHeight: '0.95' }}>
              {SITE.city ? `em ${SITE.city}` : SEGMENT.hero.flourishNoCity}
            </span>
          </h1>
          <p className="rise max-w-xl text-white/80 text-base sm:text-lg mt-7 leading-relaxed">
            {featured.length > 0 ? `${(SERVICES.length > 3 ? featured.map((s) => s.label.toLowerCase()).join(', ') + ' e outros serviços' : listLabels(featured)).replace(/^./, (c) => c.toUpperCase())}. ` : ''}
            {SITE.whatsapp ? 'Peça seu orçamento pelo WhatsApp.' : 'Entre em contato e peça seu orçamento.'}
          </p>
          <ContactBtns className="rise mt-9" size="lg" onDark />
          {SERVICES.length > 1 && (
            <Link to="/servicos" className="rise mt-5 inline-flex items-center gap-2 text-white/80 hover:text-white font-medium">
              Ver todos os serviços <ArrowRight className="h-4 w-4" />
            </Link>
          )}
          {chips.length > 0 && (
            <ul className="rise mt-8 flex flex-wrap gap-2">
              {chips.map(({ Icon, text }) => (
                <li key={text} className="inline-flex items-center gap-2 rounded-full bg-white/10 border border-white/15 backdrop-blur-md px-4 py-2 text-sm text-white/85">
                  <Icon className="h-4 w-4 text-primary-light" /> {text}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="rise hidden lg:block lg:col-span-5">
          <QuoteForm id="orcamento-topo" />
        </div>
      </div>
    </section>
  )
}

/* Short proof strip — only facts supplied with the business data. */
function Facts() {
  const { facts } = proofFacts()
  if (!facts.length) return null
  return (
    <section className="relative z-20 -mt-10 sm:-mt-12 mb-10 sm:mb-14 px-4 sm:px-10 lg:px-16">
      <Reveal className="max-w-5xl mx-auto bg-white rounded-3xl sm:rounded-4xl border border-ink/[0.06] shadow-2xl shadow-deep/20 px-5 sm:px-8 py-5 sm:py-6">
        <ul className={`grid gap-5 sm:gap-8 sm:divide-x divide-ink/10 ${['', 'sm:grid-cols-1', 'sm:grid-cols-2', 'sm:grid-cols-3'][facts.length]}`}>
          {facts.map(({ Icon, value, label, href }) => {
            const body = (
              <>
                <span className="h-10 w-10 shrink-0 rounded-2xl bg-primary/10 text-primary-dark flex items-center justify-center"><Icon className="h-5 w-5" strokeWidth={2.2} /></span>
                <span className="leading-tight">
                  <span className="font-display font-extrabold text-xl text-ink block">{value}</span>
                  <span className="text-[13px] text-muted">{label}</span>
                </span>
              </>
            )
            return <li key={value}>{href ? <a href={href} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3">{body}</a> : <div className="flex items-center gap-3">{body}</div>}</li>
          })}
        </ul>
      </Reveal>
    </section>
  )
}

/* FAQ answered strictly from business data; questions without data are left out. */
function homeFaq() {
  const how = SITE.whatsapp
    ? 'Clique em “Pedir orçamento no WhatsApp” ou preencha o formulário: a conversa abre com sua mensagem pronta. Se puder, envie fotos do local.'
    : SITE.phoneHref ? `Ligue para ${SITE.phone} e descreva o serviço.` : `Envie um e-mail para ${SITE.email} descrevendo o serviço.`
  return [
    { q: 'Como peço um orçamento?', a: how },
    SERVICES.length > 0 && { q: 'Quais serviços vocês fazem?', a: `${listLabels(SERVICES).replace(/^./, (c) => c.toUpperCase())}. Veja os detalhes na [página de serviços](/servicos).` },
    AREA && { q: 'Onde vocês atendem?', a: `Atendemos ${AREA}. Informe seu bairro ao pedir o orçamento.` },
    SITE.hours && { q: 'Qual é o horário de atendimento?', a: SITE.hours + '.' },
    SITE.paymentMethods.length > 0 && { q: 'Quais formas de pagamento são aceitas?', a: SITE.paymentMethods.join(', ') + '.' },
  ].filter(Boolean)
}

function localBusinessLd() {
  return {
    '@context': 'https://schema.org',
    '@type': SEGMENT.schema_type,
    name: SITE.name,
    url: SITE.domain + '/',
    ...(SITE.phoneHref && { telephone: SITE.phoneHref.replace('tel:', '') }),
    ...(SITE.email && { email: SITE.email }),
    ...(SITE.city && { address: { '@type': 'PostalAddress', ...(SITE.street && { streetAddress: SITE.street }), addressLocality: SITE.city, ...(SITE.state && { addressRegion: SITE.state }), ...(SITE.zip && { postalCode: SITE.zip }), addressCountry: 'BR' } }),
    ...(SITE.serviceArea && { areaServed: SITE.serviceArea }),
  }
}

export default function HomePage() {
  useSEO({ title: SEO_TITLE, description: SEO_DESCRIPTION, path: '/', image: SEGMENT.hero.image && asset(SEGMENT.hero.image) })
  return (
    <>
      <script type="application/ld+json">{JSON.stringify(localBusinessLd())}</script>
      <Hero />
      <Facts />
      {HOME_SERVICES.length > 0 && (
        <section className="relative py-24 sm:py-32 px-6 sm:px-10 lg:px-16">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8 mb-12 sm:mb-16">
              <SectionHeading eyebrow="Serviços" title={SEGMENT.servicesHeading.title} flourish={SEGMENT.servicesHeading.flourish} />
              {SERVICES.length > HOME_SERVICES.length && <Reveal delay={120}><Btn to="/servicos" variant="outline">Ver todos os serviços</Btn></Reveal>}
            </div>
            <ServicesGrid items={HOME_SERVICES} />
          </div>
        </section>
      )}
      <ProcessStack />
      <Reviews />
      {SITE.about && (
        <section className="py-24 sm:py-32 px-6 sm:px-10 lg:px-16">
          <div className="max-w-4xl mx-auto">
            <SectionHeading eyebrow="Sobre" title={SITE.name} />
            <Reveal className="prose-template mt-6 text-muted text-lg leading-relaxed"><p>{SITE.about}</p></Reveal>
          </div>
        </section>
      )}
      <section className="py-20 sm:py-28 px-6 sm:px-10 lg:px-16">
        <div className="max-w-3xl mx-auto"><FAQ items={homeFaq()} /></div>
      </section>
      <ContactSection />
    </>
  )
}
