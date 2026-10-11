import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { asset } from '../business.js'
import { SITE, SERVICES, SEGMENT } from '../site.js'
import { useSEO } from '../lib/useSEO.js'
import Reveal from '../lib/Reveal.jsx'
import PageHero from '../components/PageHero.jsx'
import ServicesGrid from '../components/ServicesGrid.jsx'
import ContactSection from '../components/ContactSection.jsx'

export default function ServicesPage() {
  const where = SITE.city ? ` em ${SITE.city}` : ''
  useSEO({
    title: `Serviços | ${SITE.name}`,
    description: `${SERVICES.map((s) => s.label).join(', ')}${where}. Peça seu orçamento.`,
    path: '/servicos',
    image: SERVICES[0]?.image,
  })
  return (
    <>
      <PageHero
        image={SERVICES[0]?.image || asset(SEGMENT.hero.image)}
        imageAlt={SERVICES[0]?.alt || SEGMENT.hero.alt}
        crumbs={[{ label: 'Início', href: '/' }, { label: 'Serviços', href: '/servicos' }]}
        eyebrow={`${SEGMENT.activity}${where}`}
        h1="Nossos serviços"
        intro={['Escolha o serviço para ver o que informar no pedido de orçamento.']}
      />
      <section className="px-6 sm:px-10 lg:px-16 py-20 sm:py-28">
        <div className="max-w-7xl mx-auto">
          <ServicesGrid items={SERVICES.slice(0, 6)} />
          {SERVICES.length > 6 && (
            <div className="mt-6 grid sm:grid-cols-2 lg:grid-cols-3 gap-px bg-divider rounded-4xl overflow-hidden border border-divider">
              {SERVICES.slice(6).map((s, i) => (
                <Reveal key={s.href} delay={(i % 3) * 60}>
                  <Link to={s.href} className="group flex h-full items-start gap-4 bg-white p-6 hover:bg-background transition-colors">
                    <span className="flex-1">
                      <span className="font-display font-semibold text-ink group-hover:text-primary-dark transition-colors block">{s.label}</span>
                      <span className="text-sm text-muted leading-snug block mt-1">{s.short}</span>
                    </span>
                    <ArrowRight className="h-4 w-4 text-ink/30 group-hover:text-primary group-hover:translate-x-0.5 transition-all mt-1" />
                  </Link>
                </Reveal>
              ))}
            </div>
          )}
        </div>
      </section>
      <ContactSection />
    </>
  )
}
