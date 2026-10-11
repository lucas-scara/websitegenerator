import { useState } from 'react'
import { Mail } from 'lucide-react'
import { SITE, SERVICES } from '../site.js'
import { whatsappHref } from '../business.js'
import { WhatsAppIcon } from './Icons.jsx'

function Field({ label, optional, children }) {
  return (
    <label className="block">
      <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted mb-1.5 block">
        {label} {optional && <span className="normal-case tracking-normal">(opcional)</span>}
      </span>
      {children}
    </label>
  )
}

const input = 'w-full bg-background border border-divider rounded-2xl px-4 py-3 text-ink placeholder-muted/60 focus:border-primary focus:ring-4 focus:ring-primary/15 outline-none transition font-body text-base'

/*
 * Message composer: the site never receives or stores data. Submitting opens the visitor's own
 * WhatsApp (or e-mail app) with the text filled in, addressed to the verified business contact.
 */
export default function QuoteForm({ id, service, title = 'Peça seu orçamento', className = '' }) {
  const [form, setForm] = useState({ name: '', topic: service || '', place: '', message: '' })
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const channel = SITE.whatsapp ? 'whatsapp' : SITE.email ? 'email' : null
  if (!channel) return null

  const compose = () => [
    `Olá, ${SITE.name}! Meu nome é ${form.name.trim()}.`,
    form.topic ? `Gostaria de um orçamento para: ${form.topic}.` : 'Gostaria de pedir um orçamento.',
    form.place.trim() && `Local: ${form.place.trim()}.`,
    form.message.trim(),
  ].filter(Boolean).join('\n')

  const submit = (e) => {
    e.preventDefault()
    const text = compose()
    const href = channel === 'whatsapp'
      ? whatsappHref(text)
      : `mailto:${SITE.email}?subject=${encodeURIComponent('Pedido de orçamento')}&body=${encodeURIComponent(text)}`
    window.open(href, '_blank', 'noopener')
  }

  return (
    <form id={id} onSubmit={submit} className={`bg-surface border border-divider rounded-4xl p-6 sm:p-8 shadow-xl shadow-primary/5 text-ink ${className}`}>
      <h3 className="font-display font-bold text-xl sm:text-2xl leading-tight">{title}</h3>
      <p className="text-muted text-sm mt-1.5">
        {channel === 'whatsapp' ? 'Preencha e sua mensagem abre pronta no WhatsApp.' : 'Preencha e sua mensagem abre pronta no seu e-mail.'}
      </p>
      <div className="grid gap-4 mt-6">
        <Field label="Seu nome">
          <input className={input} name="name" required value={form.name} onChange={set('name')} placeholder="Como podemos chamar você?" autoComplete="given-name" />
        </Field>
        {SERVICES.length > 0 && (
          <Field label="Serviço" optional>
            <select className={`${input} ${form.topic ? '' : 'text-muted'}`} name="topic" value={form.topic} onChange={set('topic')}>
              <option value="">Escolha um serviço</option>
              {SERVICES.map((s) => <option key={s.id} value={s.label}>{s.label}</option>)}
              <option value="Outro serviço">Outro serviço</option>
            </select>
          </Field>
        )}
        <Field label="Bairro e cidade" optional>
          <input className={input} name="place" value={form.place} onChange={set('place')} placeholder={SITE.city ? `Ex.: Centro, ${SITE.city}` : 'Ex.: Centro'} autoComplete="address-level2" />
        </Field>
        <Field label="Detalhes" optional>
          <textarea className={`${input} min-h-[96px] resize-y`} name="message" value={form.message} onChange={set('message')} placeholder="Conte rapidamente o que precisa" />
        </Field>
      </div>
      <button type="submit" className={`magnetic-btn mt-6 w-full inline-flex items-center justify-center gap-2 rounded-full font-semibold px-6 py-4 ${channel === 'whatsapp' ? 'bg-whatsapp text-deep hover:bg-whatsapp-dark' : 'bg-primary text-on-primary hover:bg-primary-dark hover:text-white'}`}>
        {channel === 'whatsapp' ? <WhatsAppIcon className="h-5 w-5" /> : <Mail className="h-5 w-5" />}
        {channel === 'whatsapp' ? 'Continuar no WhatsApp' : 'Continuar no e-mail'}
      </button>
      <p className="text-xs text-muted mt-3 text-center">Este site não envia nem armazena seus dados.</p>
    </form>
  )
}
