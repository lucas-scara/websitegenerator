import { Link } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, Phone, Mail } from 'lucide-react'
import { WhatsAppIcon } from './Icons.jsx'
import { channels } from '../business.js'

const base = 'inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-colors'
const sizes = { sm: 'px-4 py-2 text-sm', md: 'px-6 py-3.5 text-[15px]', lg: 'px-7 py-4 text-base' }
const variants = {
  primary: 'magnetic-btn bg-primary text-on-primary shadow-lg shadow-primary/30 hover:bg-primary-dark hover:text-white',
  dark: 'magnetic-btn bg-deep text-white shadow-lg shadow-deep/20 hover:bg-ink',
  glass: 'lift-on-hover bg-white/10 backdrop-blur-md text-white border border-white/20 hover:bg-white/15',
  outline: 'lift-on-hover bg-transparent text-ink border border-ink/15 hover:border-primary hover:text-primary-dark',
  whatsapp: 'magnetic-btn bg-whatsapp text-deep shadow-lg shadow-whatsapp/30 hover:bg-whatsapp-dark',
}
const ICONS = { phone: Phone, email: Mail, whatsapp: WhatsAppIcon, up: ArrowUpRight, arrow: ArrowRight }

export function Btn({ href, to, children, variant = 'primary', size = 'md', icon = 'arrow', className = '', external, ...rest }) {
  const Icon = icon === 'none' ? null : ICONS[icon] || ArrowRight
  const leading = ['phone', 'email', 'whatsapp'].includes(icon)
  const cls = `group ${base} ${sizes[size]} ${variants[variant]} ${className}`
  const inner = (
    <>
      {Icon && leading && <Icon className="h-4 w-4 shrink-0" strokeWidth={2.4} />}
      <span>{children}</span>
      {Icon && !leading && <Icon className="h-4 w-4 transition-transform group-hover:translate-x-0.5" strokeWidth={2.4} />}
    </>
  )
  if (to) return <Link to={to} className={cls} {...rest}>{inner}</Link>
  if (href) return <a href={href} className={cls} {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})} {...rest}>{inner}</a>
  return <button type="button" className={cls} {...rest}>{inner}</button>
}

/* Verified contact buttons in priority order; renders nothing when no channel exists. */
export function ContactBtns({ service, limit = 2, size = 'md', onDark = false, short = false, className = '' }) {
  const list = channels(service).slice(0, limit)
  if (!list.length) return null
  return (
    <div className={`flex flex-wrap gap-3 ${className}`}>
      {list.map((c, i) => (
        <Btn key={c.kind} href={c.href} external={c.external} icon={c.kind} size={size}
          variant={i === 0 ? (c.kind === 'whatsapp' ? 'whatsapp' : 'primary') : onDark ? 'glass' : 'outline'}>
          {short ? c.short : c.label}
        </Btn>
      ))}
    </div>
  )
}
