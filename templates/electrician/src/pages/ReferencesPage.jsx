import { asset } from '../business.js'
import { copy } from '../business.js'
import { useSEO } from '../lib/useSEO.js'
import { GALLERY, GALLERY_FILTERS } from '../site.js'
import PageHero from '../components/PageHero.jsx'
import Gallery from '../components/Gallery.jsx'
import ContactSection from '../components/ContactSection.jsx'

export default function ReferencesPage() {
  useSEO({ title: copy("Inspiração | Your Company"), description: "Inspiração para iluminação e interiores com imagens ilustrativas.", path: '/inspiration', image: asset("/images/outdoor-lighting.jpg") })
  return (
    <>
      <PageHero
        image={asset("/images/outdoor-lighting.jpg")}
        imageAlt={"Ambientes residenciais — imagem ilustrativa"}
        crumbs={[{ label: "Início", href: '/' }, { label: "Inspiração", href: '/inspiration' }]}
        eyebrow={"Inspiração · imagens ilustrativas"}
        h1={"Inspiração"}
        intro={["Veja referências de iluminação e interiores. Todas as imagens são ilustrativas."]}
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
