import { asset } from '../business.js'
import { copy } from '../business.js'
import { Phone, Mail, MapPin, Building2, FileBadge2, Hash } from 'lucide-react'
import { useSEO } from '../lib/useSEO.js'
import { SITE } from '../site.js'
import Reveal from '../lib/Reveal.jsx'
import PageHero from '../components/PageHero.jsx'
import ContactSection from '../components/ContactSection.jsx'

export default function ContactPage() {
  useSEO({
    title: copy("Contato | Your Company"),
    description: "Tem dúvidas sobre nossos serviços? Entre em contato por telefone ou e-mail para conversar sobre seu projeto.",
    path: '/contact',
    image: asset("/images/house-dusk.jpg"),
  })
  const details = [
    { Icon: Building2, label: copy("Your Company"), value: SITE.address },
    { Icon: Phone, label: "Telefone:", value: SITE.phone, href: SITE.phoneHref },
    { Icon: Mail, label: 'E-mail:', value: SITE.email, href: SITE.emailHref },
    { Icon: Hash, label: "Cadastro da empresa:", value: SITE.cvr },
    { Icon: FileBadge2, label: "Serviços elétricos", value: SITE.authNumber },
    { Icon: Hash, label: "Identificação:", value: SITE.ean },
  ]
  return (
    <>
      <PageHero
        image={asset("/images/house-dusk.jpg")}
        imageAlt={"Interior moderno — imagem ilustrativa"}
        crumbs={[{ label: "Início", href: '/' }, { label: "Contato", href: '/contact' }]}
        eyebrow={"Contato · vamos conversar"}
        h1={"Contato"}
        intro={[
          "Tem dúvidas sobre nossos serviços? Entre em contato para conversar sobre seu projeto.",
          "Se preferir, ligue para esclarecer suas dúvidas.",
        ]}
        ctas={[{ label: SITE.phone, href: SITE.phoneHref }, { label: "Envie um e-mail", href: SITE.emailHref }]}
      />

      <section className="px-6 sm:px-10 lg:px-16 pt-16 sm:pt-24 pb-6">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-12 gap-8">
          <Reveal className="lg:col-span-5">
            <div className="h-full rounded-5xl bg-white border border-divider p-6 sm:p-8 shadow-xl shadow-primary/5">
              <span className="font-mono text-[11px] uppercase tracking-[0.28em] text-primary-dark">{"╱ Dados da empresa"}</span>
              <ul className="mt-5 divide-y divide-divider">
                {details.filter(d => d.value).map((d) => (
                  <li key={d.label + d.value} className="py-3.5 flex items-start gap-3">
                    <span className="mt-0.5 h-9 w-9 shrink-0 rounded-2xl bg-primary/10 text-primary-dark flex items-center justify-center"><d.Icon className="h-4 w-4" strokeWidth={2.2} /></span>
                    <span>
                      <span className="block font-mono text-[10px] uppercase tracking-widest text-muted">{d.label}</span>
                      {d.href ? <a href={d.href} className="font-display font-semibold text-ink hover:text-primary-dark transition break-all">{d.value}</a> : <span className="font-display font-semibold text-ink">{d.value}</span>}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
          <Reveal delay={120} className="lg:col-span-7">
            <div className="h-full min-h-[380px] rounded-5xl overflow-hidden border border-divider shadow-xl shadow-primary/5 bg-white relative">
              <div className="p-12 text-muted">Entre em contato para confirmar a área atendida.</div>
              <div className="absolute bottom-4 left-4 flex items-center gap-2 bg-white/90 backdrop-blur-sm rounded-full pl-3 pr-4 py-1.5 shadow-lg text-deep">
                <MapPin className="h-3.5 w-3.5 text-primary" />
                <span className="font-mono text-[10px] uppercase tracking-widest">{SITE.address}</span>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <ContactSection />
    </>
  )
}
