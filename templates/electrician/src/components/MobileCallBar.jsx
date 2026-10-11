import { useEffect, useState } from 'react'
import { Phone, Mail } from 'lucide-react'
import { channels } from '../business.js'
import { WhatsAppIcon } from './Icons.jsx'

const ICONS = { whatsapp: WhatsAppIcon, phone: Phone, email: Mail }

/* One persistent contact bar on phones/tablets: the two best verified channels, nothing else. */
export function MobileCallBar() {
  const list = channels().slice(0, 2)
  if (!list.length) return null
  return (
    <div className="lg:hidden fixed bottom-0 inset-x-0 z-40 px-3 pb-3 pb-safe pointer-events-none">
      <div className="pointer-events-auto glass-dark rounded-full p-1.5 flex gap-1.5 shadow-2xl shadow-deep/40 border border-white/10">
        {list.map((c, i) => {
          const Icon = ICONS[c.kind]
          const cls = c.kind === 'whatsapp' ? 'bg-whatsapp text-deep' : i === 0 ? 'bg-primary text-on-primary' : 'bg-white text-deep'
          return (
            <a key={c.kind} href={c.href} {...(c.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
              className={`flex-1 inline-flex items-center justify-center gap-2 rounded-full font-semibold py-3 text-sm ${cls}`}>
              <Icon className="h-4 w-4" strokeWidth={2.4} /> {c.short}
            </a>
          )
        })}
      </div>
    </div>
  )
}

/* Desktop: discreet floating WhatsApp button, shown after the hero so it never covers the hero form. */
export function FloatingWhatsApp() {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > window.innerHeight * 0.8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  const wa = channels().find((c) => c.kind === 'whatsapp')
  if (!wa) return null
  return (
    <a href={wa.href} target="_blank" rel="noopener noreferrer" aria-label="Conversar no WhatsApp" tabIndex={visible ? 0 : -1}
      className={`hidden lg:inline-flex fixed bottom-6 right-6 z-40 items-center gap-2 rounded-full bg-whatsapp text-deep font-semibold pl-4 pr-5 py-3.5 shadow-2xl shadow-deep/30 hover:bg-whatsapp-dark transition-all duration-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}>
      <WhatsAppIcon className="h-5 w-5" /> WhatsApp
    </a>
  )
}
