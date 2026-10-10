import { asset } from '../business.js'
import { copy } from '../business.js'
import { Link } from 'react-router-dom'
import { Building2, Home, ArrowRight, Siren, Plug, Hammer, Wrench, BatteryCharging, ShieldAlert, Box, Zap, Layers, HousePlus, LayoutGrid } from 'lucide-react'
import { useSEO } from '../lib/useSEO.js'
import { HOME_SERVICES } from '../site.js'
import Reveal from '../lib/Reveal.jsx'
import PageHero from '../components/PageHero.jsx'
import ServicesGrid from '../components/ServicesGrid.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import ContactSection from '../components/ContactSection.jsx'
import Reviews from '../components/Reviews.jsx'

const ALL = [
  { Icon: Siren, label: "Reparos elétricos", href: '/electrical-repairs', text: "Converse conosco sobre o serviço elétrico, o prazo desejado e o orçamento para seu imóvel." },
  { Icon: Plug, label: "Instalações elétricas", href: '/electrical-installation', text: "Iluminação, tomadas e atualização de instalações elétricas." },
  { Icon: ShieldAlert, label: "Dispositivo DR", href: '/rcd-protection', text: "Dispositivo de proteção para situações de falha elétrica." },
  { Icon: Box, label: "Instalação de quadro elétrico", href: '/electrical-enclosures', text: "Soluções para o quadro elétrico da sua casa ou empresa." },
  { Icon: Zap, label: "Troca de quadro elétrico", href: '/consumer-units', text: "Atualização do quadro elétrico conforme as necessidades do imóvel." },
  { Icon: Hammer, label: "Reforma elétrica", href: '/rewiring', text: "Atualização de instalações que já não atendem às necessidades do imóvel." },
  { Icon: Layers, label: "Projetos elétricos", href: '/electrical-contracting', text: "Planejamento e execução de serviços elétricos para projetos maiores." },
  { Icon: HousePlus, label: "Ampliações", href: '/extensions', text: "Instalações elétricas para novos cômodos e ampliações." },
  { Icon: LayoutGrid, label: "Reforma completa", href: '/renovations', text: "Serviços elétricos nas etapas de uma reforma residencial." },
  { Icon: Wrench, label: "Manutenção elétrica", href: '/maintenance', text: "Manutenção e verificação da instalação elétrica." },
  { Icon: BatteryCharging, label: "Carregador para veículo elétrico", href: '/ev-charging', text: "Converse sobre opções de recarga para seu imóvel." },
]

export default function ServicesPage() {
  useSEO({
    title: copy("Conheça os serviços | Your Company"),
    description: "Converse conosco sobre o serviço elétrico, o prazo desejado e o orçamento para seu imóvel.",
    path: '/services',
    image: asset("/images/panel-testing.jpg"),
  })
  const segments = [
    { Icon: Building2, title: "Condomínios", text: "Converse conosco sobre o serviço elétrico, o prazo desejado e o orçamento para seu imóvel." },
    { Icon: Home, title: "Proprietários", text: "Converse conosco sobre o serviço elétrico, o prazo desejado e o orçamento para seu imóvel." },
  ]
  return (
    <>
      <PageHero
        image={asset("/images/panel-testing.jpg")}
        imageAlt={copy("Your Company — conheça os serviços")}
        crumbs={[{ label: "Início", href: '/' }, { label: "Serviços", href: '/services' }]}
        eyebrow={"Serviços elétricos"}
        h1={"Conheça os serviços"}
        intro={["Conheça os serviços elétricos apresentados nesta prévia e converse sobre o que seu imóvel precisa."]}
      />

      <section className="px-6 sm:px-10 lg:px-16 pt-20 sm:pt-28 pb-8">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-5">
          {segments.map((s, i) => (
            <Reveal key={s.title} delay={i * 120}>
              <article className="h-full rounded-5xl bg-white border border-divider p-7 sm:p-10 shadow-sm hover:shadow-xl hover:shadow-primary/10 hover:border-primary/40 transition-all duration-500">
                <span className="h-12 w-12 rounded-2xl bg-primary/10 text-primary-dark flex items-center justify-center mb-6"><s.Icon className="h-6 w-6" strokeWidth={2.2} /></span>
                <h3 className="font-display font-bold text-2xl sm:text-3xl text-ink tracking-tight">{s.title}</h3>
                <p className="text-muted text-[15px] sm:text-base leading-relaxed mt-4">{s.text}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="px-6 sm:px-10 lg:px-16 py-16 sm:py-24">
        <div className="max-w-7xl mx-auto">
          <SectionHeading eyebrow={"Nossos serviços"} title={"Soluções elétricas,"} flourish={"em um só lugar."} className="mb-12" />
          <ServicesGrid items={HOME_SERVICES} />
          <div className="mt-6 grid sm:grid-cols-2 lg:grid-cols-3 gap-px bg-divider rounded-4xl overflow-hidden border border-divider">
            {ALL.map((s, i) => (
              <Reveal key={s.href} delay={(i % 3) * 60}>
                <Link to={s.href} className="group flex h-full items-start gap-4 bg-white p-6 hover:bg-background transition-colors">
                  <span className="h-10 w-10 shrink-0 rounded-2xl bg-primary/10 text-primary-dark flex items-center justify-center group-hover:bg-primary group-hover:text-deep transition-colors"><s.Icon className="h-5 w-5" strokeWidth={2.2} /></span>
                  <span className="flex-1">
                    <span className="font-display font-semibold text-ink group-hover:text-primary-dark transition-colors block">{s.label}</span>
                    <span className="text-sm text-muted leading-snug block mt-1">{s.text}</span>
                  </span>
                  <ArrowRight className="h-4 w-4 text-ink/30 group-hover:text-primary group-hover:translate-x-0.5 transition-all mt-1" />
                </Link>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <Reviews />
      <ContactSection />
    </>
  )
}
