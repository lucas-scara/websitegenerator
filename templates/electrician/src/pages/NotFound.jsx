import { useSEO } from '../lib/useSEO.js'
import { Btn } from '../components/Buttons.jsx'
import { SITE } from '../site.js'

export default function NotFound() {
  useSEO({ title: `Página não encontrada | ${SITE.name}`, description: 'Esta página não existe.', path: '/404' })
  return (
    <section className="min-h-[70vh] flex items-center px-6 pt-36 pb-24 bg-deep text-white rounded-b-6xl">
      <div className="max-w-2xl mx-auto text-center">
        <span className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light">404</span>
        <h1 className="font-display font-extrabold text-5xl sm:text-6xl text-white mt-4 tracking-tight">Página <span className="font-serif italic font-medium text-primary-light">não encontrada.</span></h1>
        <p className="text-white/65 mt-6">Esta página não existe ou mudou de endereço.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Btn to="/">Voltar ao início</Btn>
          <Btn to="/contato" variant="glass">Contato</Btn>
        </div>
      </div>
    </section>
  )
}
