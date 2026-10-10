import Reveal from '../lib/Reveal.jsx'

export default function Reviews({ dark = false, id = 'anmeldelser' }) {
  return <section id={id} className={`py-20 sm:py-28 px-6 sm:px-10 lg:px-16 ${dark ? 'bg-deep text-white' : ''}`}>
    <div className="max-w-7xl mx-auto"><Reveal>
      <h2 className="font-display font-extrabold text-4xl sm:text-5xl">Vamos conversar</h2>
      <div className="mt-8 rounded-4xl border border-primary/20 p-10">
        <p className="text-lg">Um bom serviço elétrico começa com uma conversa.</p>
        <p className="mt-3 opacity-60">Conte o que precisa e converse sobre os próximos passos.</p>
      </div>
    </Reveal></div>
  </section>
}
