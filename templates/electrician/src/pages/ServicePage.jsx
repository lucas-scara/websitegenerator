import { Link } from 'react-router-dom'
import { Check, ArrowRight } from 'lucide-react'
import { SITE, SERVICES, SEGMENT } from '../site.js'
import { useSEO } from '../lib/useSEO.js'
import Reveal from '../lib/Reveal.jsx'
import PageHero from '../components/PageHero.jsx'
import ContactSection from '../components/ContactSection.jsx'
import FAQ from '../components/FAQ.jsx'
import { ContactBtns } from '../components/Buttons.jsx'

/* One page per enabled service, generated from the segment preset. */
export default function ServicePage({ service }) {
  const where = SITE.city ? ` em ${SITE.city}` : ''
  useSEO({ title: `${service.label}${where} | ${SITE.name}`, description: service.intro, path: service.href, image: service.image })
  const others = SERVICES.filter((s) => s.id !== service.id)
  return (
    <>
      <PageHero
        image={service.image}
        imageAlt={service.alt}
        crumbs={[{ label: 'Início', href: '/' }, { label: 'Serviços', href: '/servicos' }, { label: service.label, href: service.href }]}
        eyebrow={`${SEGMENT.activity}${where}`}
        h1={service.label}
        intro={[service.intro]}
        service={service.label}
      />
      <section className="px-6 sm:px-10 lg:px-16 pt-20 sm:pt-28 pb-8">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 lg:gap-16">
          <article className="lg:col-span-8 max-w-3xl">
            <Reveal>
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-primary-dark">╱ Antes de pedir o orçamento</span>
              <h2 className="font-display font-bold text-3xl sm:text-4xl text-ink tracking-tight leading-[1.1] mt-3">O que informar</h2>
            </Reveal>
            <Reveal as="ul" className="mt-6 space-y-3">
              {service.checklist.map((item) => (
                <li key={item} className="flex items-start gap-3 text-ink text-base leading-relaxed">
                  <span className="mt-0.5 h-6 w-6 shrink-0 rounded-full bg-primary/10 text-primary-dark flex items-center justify-center"><Check className="h-3.5 w-3.5" strokeWidth={3} /></span>
                  {item}
                </li>
              ))}
            </Reveal>
            <ContactBtns className="mt-8" service={service.label} />
            {service.faq?.length > 0 && <div className="mt-16"><FAQ items={service.faq} /></div>}
          </article>
          {others.length > 0 && (
            <aside className="lg:col-span-4">
              <Reveal className="lg:sticky lg:top-28 rounded-4xl bg-white border border-divider p-6">
                <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-primary-dark">Outros serviços</p>
                <ul className="mt-3 divide-y divide-divider">
                  {others.map((s) => (
                    <li key={s.href}>
                      <Link to={s.href} className="group flex items-center justify-between py-2.5 text-[15px] font-medium text-ink hover:text-primary-dark transition-colors">
                        {s.label} <ArrowRight className="h-4 w-4 text-ink/30 group-hover:text-primary transition-all" />
                      </Link>
                    </li>
                  ))}
                </ul>
              </Reveal>
            </aside>
          )}
        </div>
      </section>
      <ContactSection service={service.label} />
    </>
  )
}
