import { useEffect, useRef } from 'react'
import { SERVICES, SEGMENT } from '../site.js'
import { asset } from '../business.js'
import SectionHeading from './SectionHeading.jsx'
import { ContactBtns } from './Buttons.jsx'

/*
 * "Como pedir": sticky cards that stack on scroll. Stacking itself is pure CSS (position: sticky);
 * the receding effect on the covered card (scale, blur, fade) comes from GSAP + ScrollTrigger, which is
 * imported on demand only when the section is about to enter the viewport, so it never weighs on first load.
 * Without GSAP (slow network, reduced motion) the cards still stack.
 */

/* One illustrative photo per step, spread over the enabled services so each card differs and none shows a service the business does not offer. */
function stepImages(count) {
  const withPhoto = SERVICES.filter((s) => s.image)
  const fallback = SEGMENT.hero.image ? [{ image: asset(SEGMENT.hero.image), alt: SEGMENT.hero.alt }] : []
  const pool = withPhoto.length ? withPhoto : fallback
  if (!pool.length) return Array(count).fill(null)
  return Array.from({ length: count }, (_, i) => pool[Math.round((i * (pool.length - 1)) / Math.max(count - 1, 1))])
}

export default function ProcessStack() {
  const ref = useRef(null)
  const steps = SEGMENT.process
  const images = stepImages(steps.length)

  useEffect(() => {
    const root = ref.current
    if (!root || !('IntersectionObserver' in window)) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let ctx
    let cancelled = false
    const io = new IntersectionObserver(async ([entry]) => {
      if (!entry.isIntersecting) return
      io.disconnect()
      try {
        const [{ gsap }, { ScrollTrigger }] = await Promise.all([import('gsap'), import('gsap/ScrollTrigger')])
        if (cancelled) return
        gsap.registerPlugin(ScrollTrigger)
        const blur = window.innerWidth < 640 ? 3 : 6 // blur is costly on small phones
        ctx = gsap.context(() => {
          const cards = gsap.utils.toArray('.process-card')
          cards.forEach((card, i) => {
            if (i === cards.length - 1) return
            // Explicit neutral start: tweening a filter from "none" makes GSAP interpolate from zeros (black card).
            gsap.fromTo(card, { scale: 1, filter: 'blur(0px) saturate(1) brightness(1)' }, {
              scrollTrigger: { trigger: card, start: 'top top+=100', endTrigger: cards[cards.length - 1], end: 'top top+=120', scrub: 1 },
              scale: 0.92,
              filter: `blur(${blur}px) saturate(0.7) brightness(0.94)`, // no opacity: translucent cards would show the one beneath
              ease: 'none',
            })
          })
        }, root)
      } catch {
        /* GSAP is an enhancement: the sticky stack keeps working without it */
      }
    }, { rootMargin: '900px 0px' })
    io.observe(root)
    return () => { cancelled = true; io.disconnect(); ctx?.revert() }
  }, [])

  return (
    <section id="como-pedir" ref={ref} className="relative px-4 sm:px-6 py-20 sm:py-28">
      <div className="max-w-7xl mx-auto mb-12 sm:mb-16 px-2 sm:px-10">
        <SectionHeading eyebrow="Como pedir" title="Seu orçamento" flourish="em três passos." />
      </div>
      <ol className="space-y-6 sm:space-y-8">
        {steps.map((step, i) => {
          const photo = images[i]
          const n = String(i + 1).padStart(2, '0')
          return (
            <li key={step.title} className="process-card sticky top-24 sm:top-28 mx-auto max-w-6xl bg-gradient-to-br from-surface to-background border border-divider rounded-4xl sm:rounded-5xl overflow-hidden shadow-2xl shadow-primary/5">
              <div className="grid lg:grid-cols-5">
                <div className="lg:col-span-3 p-7 sm:p-12 lg:p-14 flex flex-col justify-between gap-6 lg:min-h-[400px]">
                  <span className="font-mono text-[11px] sm:text-xs uppercase tracking-[0.25em] text-muted">Passo {i + 1} de {steps.length}</span>
                  <div>
                    <span aria-hidden="true" className="font-display font-extrabold text-7xl sm:text-9xl leading-none text-primary/15 block -mb-2 sm:-mb-4">{n}</span>
                    <h3 className="font-display font-bold text-3xl sm:text-5xl text-ink leading-[1.05] tracking-tight">{step.title}</h3>
                  </div>
                  <p className="text-muted text-base sm:text-lg leading-relaxed max-w-lg">{step.text}</p>
                </div>
                <div className="lg:col-span-2 relative overflow-hidden h-56 sm:h-72 lg:h-auto bg-deep">
                  {photo
                    ? <img src={photo.image} alt={photo.alt} loading="lazy" className="absolute inset-0 w-full h-full object-cover" />
                    : <div className="absolute inset-0 bg-gradient-to-br from-primary-dark/70 via-deep to-deep grid-bg" />}
                  <div className="absolute inset-0 bg-gradient-to-t from-deep/50 via-transparent to-transparent" />
                  <span className="absolute top-4 left-4 flex items-center gap-2 bg-white/90 backdrop-blur-sm rounded-full pl-3 pr-4 py-1.5 shadow-lg font-mono text-[10px] uppercase tracking-widest text-ink">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary" />Passo {n}
                  </span>
                  {photo && <span className="absolute bottom-3 right-4 font-mono text-[10px] uppercase tracking-widest text-white/75">imagem ilustrativa</span>}
                </div>
              </div>
            </li>
          )
        })}
      </ol>
      <div className="max-w-6xl mx-auto mt-10 px-2 sm:px-0"><ContactBtns /></div>
    </section>
  )
}
