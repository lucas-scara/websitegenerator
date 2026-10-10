import { isServiceEnabled } from '../services.js'
import { asset } from '../business.js'
import { copy } from '../business.js'
import { Check, Info } from 'lucide-react'
import { useSEO } from '../lib/useSEO.js'
import { renderMd } from '../lib/md.jsx'
import Reveal from '../lib/Reveal.jsx'
import PageHero from '../components/PageHero.jsx'
import ContactSection from '../components/ContactSection.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { QuoteBtn } from '../components/Buttons.jsx'

/* All prices and terms verbatim from /pricing */
const GROUPS = [
 {service: '/electrical-installation', title: 'Pequenos serviços elétricos', label: 'Conte o que precisa', lines: [{name: 'Iluminação, tomadas e melhorias do dia a dia', price: 'Solicite um orçamento', unit: 'Conforme suas necessidades'}]},
 {service: '/rewiring', title: 'Reformas e instalações', label: 'Planeje o serviço', lines: [{name: 'Converse sobre escopo e materiais', price: 'Solicite um orçamento', unit: 'Para seu projeto'}]},
 {service: '/electrical-repairs', title: 'Avaliação de falhas', label: 'Descreva o problema', lines: [{name: 'Avaliação e próximos passos', price: 'Entre em contato', unit: 'Consulte a disponibilidade'}]},
 {title: 'Agendamento', lines: [{name: 'Data desejada', text: 'Entre em contato para combinar um horário adequado.'}]},
 {title: 'Seu orçamento', accent: true, lines: [{name: 'Entenda os custos', text: 'Peça por escrito o escopo, os materiais, a mão de obra e eventuais cobranças adicionais.'}]},
 {title: 'Acesso e localização', lines: [{name: 'Dados do imóvel', text: 'Informe o endereço e os requisitos de acesso ao fazer contato.'}]},
]
const VISIBLE_GROUPS = GROUPS.filter((group) => !group.service || isServiceEnabled(group.service))
const FINE_PRINT = ['Confira quais materiais e custos estão incluídos no orçamento.', 'Confirme escopo e prazo antes do início do serviço.']

export default function PricesPage() {
  useSEO({
    title: copy("Orçamentos elétricos para sua casa | Your Company"),
    description: "Peça um orçamento para o serviço elétrico que seu imóvel precisa.",
    path: '/pricing',
    image: asset("/images/panel-testing.jpg"),
  })
  return (
    <>
      <PageHero
        image={asset("/images/panel-testing.jpg")}
        imageAlt={"Orçamentos elétricos para sua casa"}
        crumbs={[{ label: "Início", href: '/' }, { label: "Orçamentos", href: '/pricing' }]}
        eyebrow={"Orçamentos e condições · solicite uma proposta"}
        h1={"Orçamentos elétricos para sua casa"}
        intro={[
          "Descreva o serviço desejado. O orçamento pode considerar o imóvel, o escopo e os materiais necessários.",
          "Entre em contato para conversar sobre os próximos passos e verificar disponibilidade.",
        ]}
      />

      <section className="relative px-6 sm:px-10 lg:px-16 pt-20 sm:pt-28 pb-10">
        <div className="max-w-7xl mx-auto">
          <SectionHeading eyebrow={"Orçamentos e condições"} title={"Orçamentos e"} flourish={"condições"} lead={"Confira no orçamento o escopo, os materiais, a mão de obra e os impostos aplicáveis."} />
          <Reveal delay={120} className="mt-8 inline-flex items-center gap-2 rounded-full bg-deep text-white px-4 py-2 font-mono text-[11px] uppercase tracking-widest">{"Entre em contato para conversar sobre suas necessidades."}</Reveal>

          <div className="mt-8 grid md:grid-cols-2 gap-5">
            {VISIBLE_GROUPS.map((g, i) => (
              <Reveal key={g.title} delay={(i % 2) * 100}>
                <article className={`h-full rounded-4xl border p-6 sm:p-8 transition-all duration-500 hover:-translate-y-1 ${g.accent ? 'bg-deep text-white border-deep shadow-2xl shadow-deep/20' : 'bg-white border-divider shadow-sm hover:shadow-xl hover:shadow-primary/10'}`}>
                  <div className="flex items-start justify-between gap-4">
                    <h3 className={`font-display font-bold text-xl sm:text-2xl leading-tight ${g.accent ? 'text-white' : 'text-ink'}`}>{g.title}</h3>
                    <span className={`font-mono text-[10px] uppercase tracking-widest pt-1 ${g.accent ? 'text-accent' : 'text-primary/60'}`}>{String(i + 1).padStart(2, '0')}</span>
                  </div>
                  {g.intro && <p className={`mt-3 text-sm leading-relaxed ${g.accent ? 'text-white/70' : 'text-muted'}`}>{g.intro}</p>}
                  <ul className={`mt-5 divide-y ${g.accent ? 'divide-white/10' : 'divide-divider'}`}>
                    {g.lines.map((l) => (
                      <li key={l.name} className="py-4 first:pt-0 last:pb-0">
                        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                          <span className={`font-semibold ${g.accent ? 'text-white' : 'text-ink'}`}>{l.name}</span>
                          {l.price && (
                            <span className="flex items-baseline gap-1.5">
                              <span className={`font-display font-extrabold text-2xl sm:text-3xl tabular-nums ${g.accent ? 'text-accent' : 'text-primary-dark'}`}>{l.price}</span>
                              <span className={`text-xs ${g.accent ? 'text-white/60' : 'text-muted'}`}>{l.unit}</span>
                            </span>
                          )}
                        </div>
                        {l.text && <p className={`mt-1.5 text-sm leading-relaxed ${g.accent ? 'text-white/70' : 'text-muted'}`}>{l.text}</p>}
                        {l.note && <p className={`mt-1 text-xs italic ${g.accent ? 'text-white/50' : 'text-muted'}`}>{l.note}</p>}
                      </li>
                    ))}
                  </ul>
                  {g.footnote && <p className={`mt-4 text-xs italic ${g.accent ? 'text-white/50' : 'text-muted'}`}>{g.footnote}</p>}
                </article>
              </Reveal>
            ))}
          </div>

          <Reveal className="mt-12 rounded-4xl bg-primary/5 border border-primary/15 p-6 sm:p-8">
            <div className="flex items-center gap-3 mb-4">
              <span className="h-9 w-9 rounded-2xl bg-primary/10 text-primary-dark flex items-center justify-center"><Info className="h-4 w-4" /></span>
              <h2 className="font-display font-bold text-2xl text-ink">{"Detalhes para conferir:"}</h2>
            </div>
            <ul className="space-y-3">
              {FINE_PRINT.map((f, i) => (
                <li key={i} className="flex items-start gap-3 text-[15px] text-muted leading-relaxed [&_strong]:text-ink">
                  <span className="mt-1 h-6 w-6 shrink-0 rounded-full bg-primary/10 text-primary-dark flex items-center justify-center"><Check className="h-3.5 w-3.5" strokeWidth={3} /></span>
                  <span>{renderMd(f, `fine-${i}`)}</span>
                </li>
              ))}
            </ul>
            <div className="mt-6"><QuoteBtn>{"Peça um orçamento"}</QuoteBtn></div>
          </Reveal>
        </div>
      </section>

      <ContactSection />
    </>
  )
}
