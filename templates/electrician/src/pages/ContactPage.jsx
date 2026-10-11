import { asset } from '../business.js'
import { SITE, SEGMENT, AREA } from '../site.js'
import { useSEO } from '../lib/useSEO.js'
import PageHero from '../components/PageHero.jsx'
import ContactSection from '../components/ContactSection.jsx'

export default function ContactPage() {
  useSEO({
    title: `Contato | ${SITE.name}`,
    description: `Fale com ${SITE.name}${SITE.city ? ` em ${SITE.city}` : ''} e peça seu orçamento.`,
    path: '/contato',
    image: SEGMENT.hero.image && asset(SEGMENT.hero.image),
  })
  return (
    <>
      <PageHero
        image={SEGMENT.hero.image && asset(SEGMENT.hero.image)}
        imageAlt={SEGMENT.hero.alt}
        crumbs={[{ label: 'Início', href: '/' }, { label: 'Contato', href: '/contato' }]}
        eyebrow={AREA ? `Atendimento · ${AREA}` : 'Contato'}
        h1="Fale com a gente"
        intro={['Conte o que precisa e peça seu orçamento.']}
        showForm={false}
      />
      <ContactSection heading="Canais de atendimento" />
    </>
  )
}
