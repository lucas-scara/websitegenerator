import { Star, ArrowUpRight } from 'lucide-react'
import { SITE } from '../site.js'
import Reveal from '../lib/Reveal.jsx'
import SectionHeading from './SectionHeading.jsx'

/* Only verified reviews with a public source are shown; without them the section does not exist. */
export default function Reviews() {
  if (!SITE.reviews.length) return null
  return (
    <section className="py-24 sm:py-32 px-6 sm:px-10 lg:px-16">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8 mb-12">
          <SectionHeading eyebrow="Avaliações" title="O que dizem" flourish="os clientes." />
          {SITE.google && (
            <a href={SITE.google.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 font-semibold text-primary-dark">
              Ver avaliações no Google <ArrowUpRight className="h-4 w-4" />
            </a>
          )}
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {SITE.reviews.slice(0, 6).map((r, i) => (
            <Reveal key={i} delay={(i % 3) * 80}>
              <figure className="h-full rounded-4xl bg-surface border border-divider p-7 flex flex-col">
                {r.rating > 0 && (
                  <div className="flex gap-0.5 text-amber-500" aria-label={`${r.rating} de 5 estrelas`}>
                    {Array.from({ length: Math.round(r.rating) }, (_, j) => <Star key={j} className="h-4 w-4 fill-current" />)}
                  </div>
                )}
                <blockquote className="mt-4 text-ink leading-relaxed flex-1">“{r.text}”</blockquote>
                <figcaption className="mt-6 text-sm">
                  <span className="font-semibold text-ink">{r.author}</span>{' '}
                  <a href={r.source_url} target="_blank" rel="noopener noreferrer" className="text-muted underline underline-offset-4">fonte</a>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
