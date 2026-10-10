import { isServiceEnabled } from '../services.js'
import { asset } from '../business.js'
import { copy } from '../business.js'
import { useSEO } from '../lib/useSEO.js'
import { GALLERY, GALLERY_FILTERS } from '../site.js'
import PageHero from '../components/PageHero.jsx'
import Gallery from '../components/Gallery.jsx'
import ContactSection from '../components/ContactSection.jsx'

export default function ReferencesPage() {
  const lighting = isServiceEnabled('/electrical-installation')
  useSEO({ title: copy("Inspiração | Your Company"), description: "Imagens ilustrativas dos serviços apresentados nesta prévia.", path: '/inspiration', image: asset(lighting ? "/images/outdoor-lighting.jpg" : "/images/ev-charging.jpg") })
  return (
    <>
      <PageHero
        image={asset(lighting ? "/images/outdoor-lighting.jpg" : "/images/ev-charging.jpg")}
        imageAlt={lighting ? "Ambientes residenciais — imagem ilustrativa" : "Recarga de veículo elétrico — imagem ilustrativa"}
        crumbs={[{ label: "Início", href: '/' }, { label: "Inspiração", href: '/inspiration' }]}
        eyebrow={"Inspiração · imagens ilustrativas"}
        h1={"Inspiração"}
        intro={["Veja referências dos serviços apresentados nesta prévia. Todas as imagens são ilustrativas."]}
      />
      <section className="px-6 sm:px-10 lg:px-16 pt-16 sm:pt-24 pb-10">
        <div className="max-w-7xl mx-auto">
          <Gallery items={GALLERY} filters={GALLERY_FILTERS} />
        </div>
      </section>
      <ContactSection />
    </>
  )
}
