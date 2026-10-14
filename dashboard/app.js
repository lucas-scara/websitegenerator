'use strict';
const $ = (selector) => document.querySelector(selector);
const state = { batches: [], jobs: [], events: [], workers: [], operations: [], stage_runs: [], templates: [], commercial_attempts: [], legacy_submissions: [], gmail_authorization: {}, gmail_followups: {}, settings: { batch_size: 3, max_workers: 3 } };
let batchFilter = 'all', stageFilter = 'all', selectedJob = null, previousSignature = '', connected = false;
const commercialSelection = new Map();
const commercialApprovalFeedbackByBatch = new Map();
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const STAGES = { queued: 'Na fila', reviewing: 'Em análise', extracting: 'Coletando dados', building: 'Gerando', checking: 'Verificando', deploying: 'Publicando', ready: 'Prévia pronta', contacting: 'Tentativa de contato', complete: 'Contato efetuado', sent: 'Enviado', sent_external: 'Contato externo comprovado', uncertain: 'Resultado incerto', blocked: 'Bloqueado', skipped: 'Ignorado', manual: 'Contato manual', simulated: 'Simulado', pending: 'Pendente', prepared: 'Preparado', replied: 'Respondeu', interested: 'Interessado', not_interested: 'Sem interesse', opted_out: 'Não contatar', failed_no_send: 'Falha sem envio', whatsapp_manual: 'WhatsApp manual', no_channel: 'Sem canal', form: 'Formulário', email: 'E-mail', not_sent: 'Não enviado', attempting: 'Tentativa reservada', submitted: 'Enviado', manual_required: 'Contato manual necessário' };
const production = (job) => job.data?.preview_verified === true && safeURL(job.preview_url) ? 'Prévia verificada' : label(job.stage);
const label = (value) => STAGES[value] || String(value || 'queued').replace(/[_-]/g, ' ');
const time = (value) => { const date = new Date(value); return Number.isNaN(date.getTime()) ? 'Time unavailable' : date.toLocaleString('pt-BR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); };
function safeURL(value) { try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) ? url.href : null; } catch { return null; } }
function isManual(job) { return job.stage === 'manual' || job.contact_status === 'manual_required' || job.data?.outreach_mode === 'manual'; }
function stageLabel(job) { return isManual(job) ? (job.stage === 'manual' ? 'Contato manual' : `Manual · ${label(job.stage)}`) : label(job.stage); }
function contactLink(value, kind) {
  if (typeof value !== 'string' || !value.trim()) return 'Indisponível';
  const text = value.trim();
  const valid = kind === 'email' ? /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/.test(text) : /^\+?[0-9 () .-]+$/.test(text) && /[0-9]/.test(text);
  if (!valid) return escapeHTML(text);
  const href = kind === 'email' ? `mailto:${encodeURIComponent(text)}` : `tel:${text.replace(/[^+0-9]/g, '')}`;
  return `<a href="${escapeHTML(href)}">${escapeHTML(text)}</a>`;
}
const contactRecord = (value, legacyKey = 'value') => value && typeof value === 'object' && !Array.isArray(value) ? value : typeof value === 'string' ? { [legacyKey]: value } : {};
function phoneNumber(value) {
  if (typeof value !== 'string' || !/^\+?[0-9 () .-]+$/.test(value.trim())) return null;
  const raw = value.trim(), digits = raw.replace(/\D/g, '');
  if (!/^\d{10,15}$/.test(digits) || raw.indexOf('+') > 0) return null;
  const local = digits.startsWith('55') && [12, 13].includes(digits.length) ? digits.slice(2) : digits;
  const display = /^[1-9]\d{9,10}$/.test(local) && [10, 11].includes(local.length)
    ? `(${local.slice(0, 2)}) ${local.slice(2, -4)}-${local.slice(-4)}` : raw;
  return { digits, dial: `${raw.startsWith('+') ? '+' : ''}${digits}`, display: digits.startsWith('55') && [12, 13].includes(digits.length) ? `+55 ${display}` : display };
}
function whatsappNumber(value) {
  const phone = phoneNumber(value);
  if (!phone) return null;
  const digits = phone.digits.replace(/^0(?=\d{10,11}$)/, '');
  const full = digits.startsWith('55') && [12, 13].includes(digits.length) ? digits : [10, 11].includes(digits.length) ? `55${digits}` : null;
  return full && /^55[1-9]\d{9,10}$/.test(full) ? full : null;
}
function checkedDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}(?:T.*)?$/.test(value)) return '';
  const date = new Date(value.length === 10 ? `${value}T00:00:00Z` : value);
  return Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value.slice(0, 10)
    ? '' : new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' }).format(date);
}
function sourceEvidence(record) {
  const sources = Array.isArray(record.sources) ? record.sources : [record.source];
  const links = sources.map(safeURL).filter(Boolean).map(url => {
    const domain = new URL(url).hostname.replace(/^www\./, '');
    return `<a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer" title="${escapeHTML(url)}">${escapeHTML(domain)} ↗</a>`;
  });
  const date = checkedDate(record.checked_at);
  return `<div class="contact-evidence"><span>${links.length ? links.join(' · ') : 'Fonte não registrada'}</span>${date ? `<time datetime="${escapeHTML(record.checked_at.slice(0, 10))}">Verificado em ${date}</time>` : ''}</div>`;
}
function renderContacts(value) {
  const contacts = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const phone = contactRecord(contacts.phone), phoneValid = phoneNumber(phone.value);
  const whatsapp = contactRecord(contacts.whatsapp), whatsappStatus = whatsapp.status || (contacts.whatsapp === false ? 'nao_utiliza' : typeof contacts.whatsapp === 'string' ? 'confirmado' : '');
  const whatsappValue = typeof contacts.whatsapp === 'string' ? contacts.whatsapp : whatsapp.value;
  const whatsappSource = whatsappStatus === 'confirmado' ? whatsapp : phone;
  const sourceURL = safeURL(whatsappSource.source);
  const sourceHost = sourceURL ? new URL(sourceURL).hostname : '';
  const sourceVerified = sourceHost.includes('.') && !sourceHost.endsWith('.local') && checkedDate(whatsappSource.checked_at) && whatsappSource.checked_at.slice(0, 10) <= new Date().toISOString().slice(0, 10);
  const whatsappDigits = sourceVerified && (whatsappStatus === 'confirmado' ? whatsappNumber(whatsappValue) : whatsappStatus === 'presumido' ? whatsappNumber(phone.value) : null);
  const whatsappDisplay = whatsappDigits ? phoneNumber(whatsappStatus === 'confirmado' ? whatsappValue : phone.value).display : '';
  const email = contactRecord(contacts.email), emailStatus = email.status || (typeof contacts.email === 'string' ? 'encontrado' : '');
  const emailValue = typeof email.value === 'string' ? email.value.trim() : '';
  const emailValid = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/.test(emailValue);
  const form = contactRecord(contacts.form, 'url'), formStatus = form.status || (typeof contacts.form === 'string' ? 'encontrado' : '');
  const formURL = safeURL(form.url);
  const item = (title, content, evidence) => `<div class="contact-item"><div class="contact-label">${title}</div><div class="contact-main">${content}</div>${evidence}</div>`;
  const phoneContent = phone.value === undefined ? 'Não registrado' : phoneValid
    ? `<a href="${escapeHTML(`tel:${phoneValid.dial}`)}">${escapeHTML(phoneValid.display)}</a><button type="button" class="copy-phone" data-copy-phone="${escapeHTML(phoneValid.dial)}" aria-label="Copiar telefone ${escapeHTML(phoneValid.display)}">Copiar</button><span class="copy-phone-status" role="status" aria-live="polite"></span>` : 'Número inválido';
  const whatsappText = { confirmado: 'Confirmado', presumido: 'Presumido · telefone público', nao_utiliza: 'Não utiliza WhatsApp', nao_verificado: 'Não verificado' }[whatsappStatus] || 'Não registrado';
  const whatsappContent = `${escapeHTML(whatsappText)}${whatsappDigits ? ` · ${escapeHTML(whatsappDisplay)} · <a href="https://wa.me/${whatsappDigits}" target="_blank" rel="noopener noreferrer">Abrir WhatsApp ↗</a>` : ''}${['confirmado', 'presumido'].includes(whatsappStatus) && !whatsappDigits ? ' · Número indisponível' : ''}`;
  const emailContent = emailStatus === 'encontrado' ? emailValid ? `<a href="mailto:${escapeHTML(encodeURIComponent(emailValue))}">${escapeHTML(emailValue)}</a>` : 'Endereço inválido'
    : emailStatus === 'nao_encontrado' ? 'Não encontrado' : emailStatus === 'nao_verificado' ? 'Não verificado' : 'Não registrado';
  const formContent = formStatus === 'encontrado'
    ? `<span>Formulário existente</span>${formURL ? ` · <a href="${escapeHTML(formURL)}" target="_blank" rel="noopener noreferrer" title="${escapeHTML(formURL)}">${escapeHTML(new URL(formURL).hostname.replace(/^www\./, '') + new URL(formURL).pathname)} ↗</a>` : ' · URL inválida'}<div class="contact-detail">${form.eligible === true ? 'Apropriado para contato comercial' : form.eligible === false ? 'Não apropriado para contato comercial' : 'Elegibilidade comercial não registrada'}${typeof form.purpose === 'string' && form.purpose.trim() ? ` · Finalidade: ${escapeHTML(form.purpose.trim())}` : ''}${Array.isArray(form.restrictions) && form.restrictions.length ? ` · Restrições: ${escapeHTML(form.restrictions.filter(v => typeof v === 'string' && v.trim()).join(', '))}` : ''}</div>`
    : formStatus === 'nao_encontrado' ? 'Não encontrado' : formStatus === 'nao_verificado' ? 'Não verificado' : 'Não registrado';
  return `<section class="dialog-section contacts-section" aria-label="Contatos e fontes"><div class="meta-label">Contatos e fontes</div><div class="contact-grid">${item('Telefone', phoneContent, sourceEvidence(phone))}${item('WhatsApp', whatsappContent, sourceEvidence(whatsappStatus === 'presumido' ? phone : whatsapp))}${item('E-mail', emailContent, sourceEvidence(email))}${item('Formulário', formContent, sourceEvidence(form))}</div></section>`;
}
function manualOutreach(job) {
  if (!isManual(job)) return '';
  const data = job.data?.manual_outreach || {};
  if (job.stage !== 'manual') return `<section class="manual-outreach"><h3>Contato manual · site pendente</h3><p>A empresa aguarda a preparação do site. A prévia verificada e a mensagem aparecerão aqui quando estiverem prontas.</p><p>${escapeHTML(data.reason || job.detail || '')}</p></section>`;
  const sources = (Array.isArray(data.source_urls) ? data.source_urls : []).map(safeURL).filter(Boolean);
  return `<section class="manual-outreach" aria-labelledby="manual-heading"><h3 id="manual-heading">Contato manual necessário</h3><p>A prévia publicada foi verificada. Use os dados e a mensagem abaixo para contato manual.</p><div class="meta-label">Motivo do contato manual</div><p>${escapeHTML(data.reason || job.reason || 'O envio automático não foi possível.')}</p><dl class="manual-contacts"><dt>E-mail verificado</dt><dd>${contactLink(data.email, 'email')}</dd><dt>Telefone verificado</dt><dd>${contactLink(data.phone, 'phone')}</dd></dl>${sources.length ? `<div class="manual-sources">Fontes dos contatos: ${sources.map((url, index) => `<a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">Fonte ${index + 1} ↗</a>`).join(' · ')}</div>` : ''}<label class="meta-label" for="manual-message">Mensagem preparada</label><textarea id="manual-message" readonly rows="10" spellcheck="false">${escapeHTML(data.message || '')}</textarea>${job.commercial_requires_review ? '<p>Mensagem com número de telefone: revise antes de qualquer contato. Cópia bloqueada.</p>' : `<div class="copy-actions"><button id="copy-message" type="button"${data.message ? '' : ' disabled'}>Copiar mensagem</button><span id="copy-status" role="status" aria-live="polite">${data.message ? '' : 'Mensagem indisponível.'}</span></div>`}</section>`;
}
function contactSimulation(job) {
  if (job.stage !== 'simulated') return '';
  const data = job.data?.contact_simulation || {};
  const form = safeURL(data.form_url);
  return `<section class="manual-outreach"><h3>Contato simulado · nenhum envio</h3><p>Mensagem preparada para revisão. Nenhum formulário foi enviado.</p>${form ? `<p><a href="${escapeHTML(form)}" target="_blank" rel="noopener noreferrer">Formulário original ↗</a></p>` : ''}<label class="meta-label" for="manual-message">Mensagem preparada</label><textarea id="manual-message" readonly rows="10" spellcheck="false">${escapeHTML(data.message || '')}</textarea>${job.commercial_requires_review ? '<p>Mensagem com número de telefone: revise antes de qualquer contato. Cópia bloqueada.</p>' : `<div class="copy-actions"><button id="copy-message" type="button"${data.message ? '' : ' disabled'}>Copiar mensagem</button><span id="copy-status" role="status" aria-live="polite"></span></div>`}</section>`;
}
function commercialSection(job) {
  const contact = job.data?.commercial_contact || {};
  const attempts = state.commercial_attempts.filter(item => item.job_id === job.id);
  const legacy = state.legacy_submissions.filter(item => item.job_id === job.id);
  const history = attempts.map(item => `<li>${escapeHTML(label(item.channel))} · ${escapeHTML(label(item.status))} · ${escapeHTML(item.evidence)}${item.gmail_message_id ? ` · Gmail ID: ${escapeHTML(item.gmail_message_id)}` : ''}${item.gmail_thread_id ? ` · Thread: ${escapeHTML(item.gmail_thread_id)}` : ''} <time>${escapeHTML(time(item.created_at))}</time></li>`).join('') + legacy.map(item => `<li>Formulário legado · ${escapeHTML(label(item.status))} · ${escapeHTML(item.evidence || '')}</li>`).join('');
  const current = job.contact_status || 'not_sent';
  const requiresReview = job.commercial_requires_review === true;
  const canRegenerate = requiresReview && current === 'prepared' && Boolean(contact.message) && job.commercial_can_regenerate === true;
  const canPrepare = job.data?.preview_verified === true && ['not_sent', 'pending', 'manual_required'].includes(current) && !contact.message;
  const auth = state.gmail_authorization?.[job.id] || { mode: 'dry_run', authorized: false, reason: 'Autorização local ausente' };
  const previewHref = safeURL(job.preview_url);
  const gmailAttempt = attempts.find(item => item.source === 'gmail_api');
  const gmailSender = gmailAttempt?.sender || auth.sender || 'Não configurado';
  const gmailControls = current === 'prepared' && !requiresReview ? `<p>Autorização: ${escapeHTML(auth.mode)} · ${escapeHTML(auth.reason)}</p><button type="button" id="gmail-simulate">Simular envio</button><p>Envios reais são autorizados pela revisão do lote comercial.</p>` : current === 'uncertain' ? `<p>Resultado incerto: reconcilie a tentativa${gmailAttempt ? ' Gmail' : ''} antes de qualquer novo envio.</p>` : '';
  const gmailPanel = contact.channel === 'email' && contact.message ? `<div class="gmail-panel"><div class="meta-label">Envio Gmail</div><p>Destinatário: ${escapeHTML(contact.destination || 'Indisponível')} · Remetente: ${escapeHTML(gmailSender)}</p><p>Assunto: ${escapeHTML(contact.subject || 'Indisponível')}</p><p>Prévia: ${escapeHTML((contact.message || '').slice(0, 180))}</p>${previewHref ? `<p><a href="${escapeHTML(previewHref)}" target="_blank" rel="noopener noreferrer">Ver a prévia do site ↗</a></p>` : ''}${gmailControls}</div>` : '';
  const followup = state.gmail_followups?.[job.id] || {};
  const followupPanel = followup.available ? `<div class="gmail-panel"><div class="meta-label">Acompanhamento por e-mail</div><p>Primeiro envio: ${escapeHTML(time(followup.first_sent_at))}</p><p>Dia 4: ${escapeHTML(time(followup.day4_due_at))} · ${escapeHTML(label(followup.day4_status))}</p><p>Dia 10: ${escapeHTML(time(followup.day10_due_at))} · ${escapeHTML(label(followup.day10_status))}</p>${followup.next_touch ? `<p>${followup.due ? 'Follow-up disponível para revisão' : 'Próximo follow-up em ' + escapeHTML(time(followup.due_at))}</p><label class="meta-label" for="followup-message">Mensagem do dia ${followup.next_touch === 1 ? '4' : '10'}</label><textarea id="followup-message" readonly rows="7">${escapeHTML(followup.message)}</textarea>${followup.due && auth.authorized ? `<button type="button" id="gmail-followup" data-touch="${followup.next_touch}">Enviar follow-up na mesma conversa</button>` : ''}` : `<p>${escapeHTML(followup.reason || '')}</p>`}</div>` : '';
  const choices = current === 'prepared' ? '<option value="sent">Envio confirmado</option><option value="sent_external">Contato externo comprovado</option><option value="failed_no_send">Falhou sem envio</option><option value="uncertain">Resultado incerto</option><option value="opted_out">Não contatar</option>'
    : ['not_sent', 'pending', 'manual_required'].includes(current) ? '<option value="sent_external">Contato externo comprovado</option><option value="opted_out">Não contatar</option>'
    : current === 'uncertain' ? '<option value="opted_out">Não contatar</option>'
    : '<option value="replied">Respondeu</option><option value="interested">Interessado</option><option value="not_interested">Sem interesse</option><option value="opted_out">Não contatar</option>';
  const recordable = ['not_sent', 'pending', 'prepared', 'manual_required', 'sent', 'submitted', 'replied', 'interested', 'not_interested', 'uncertain'].includes(current);
  const beforeContact = current === 'prepared' || ['not_sent', 'pending', 'manual_required'].includes(current);
  const externalFields = beforeContact ? `<label class="external-channel"${current === 'prepared' ? ' hidden' : ''}>Canal usado <select name="channel"${current === 'prepared' ? '' : ' required'}><option value="">Selecione</option><option value="form">Formulário</option><option value="email">E-mail</option><option value="whatsapp_manual">WhatsApp manual</option></select></label><label class="send-proof">Comprovante (URL, arquivo em runs/ ou id:...) <input name="proof" required></label>` : '';
  return `<section class="dialog-section commercial-section"><h3>Contato comercial</h3><p>Canal: ${escapeHTML(label(contact.channel || 'pending'))} · Modelo: ${escapeHTML(contact.template || 'pendente')} · Status: ${escapeHTML(label(current))}</p>${requiresReview ? '<p>Mensagem com número de telefone: revise antes de qualquer envio. As ações de envio e cópia estão bloqueadas.</p>' : ''}${contact.subject ? `<p><strong>Assunto:</strong> ${escapeHTML(contact.subject)}</p>` : ''}${contact.message ? `<label class="meta-label" for="commercial-message">Mensagem preparada</label><textarea id="commercial-message" readonly rows="10">${escapeHTML(contact.message)}</textarea>${requiresReview ? '' : '<button type="button" id="copy-commercial">Copiar mensagem</button>'}` : ''}${gmailPanel}${followupPanel}${contact.whatsapp_url && !requiresReview ? `<p><a href="${escapeHTML(contact.whatsapp_url)}" target="_blank" rel="noopener noreferrer">Abrir WhatsApp com texto ↗</a> · abrir não registra envio</p>` : ''}${canRegenerate ? '<button type="button" id="regenerate-commercial">Regenerar mensagem sem telefone</button>' : ''}<p>Próxima ação: ${escapeHTML(nextCommercialAction(job))}</p>${canPrepare ? `<button type="button" id="prepare-commercial">Preparar mensagem</button>` : ''}${recordable ? `<form id="commercial-record"><label>Status <select name="status">${choices}</select></label>${externalFields}<label>Evidência observada <input name="evidence" required maxlength="1000"></label><button type="submit">Registrar resultado</button></form>` : ''}<p id="commercial-feedback" role="status"></p><div class="meta-label">Histórico de tentativas</div>${history ? `<ol class="timeline">${history}</ol>` : '<p>Nenhuma tentativa registrada.</p>'}</section>`;
}
function nextCommercialAction(job) {
  const current = job.contact_status || 'not_sent';
  return { sent: 'Aguardar resposta', submitted: 'Aguardar resposta', replied: 'Avaliar a resposta', interested: 'Continuar a conversa manualmente', not_interested: 'Encerrar abordagem', opted_out: 'Não contatar', uncertain: 'Reconciliar resultado antes de qualquer novo contato' }[current] || job.data?.commercial_contact?.next_action || 'Preparar mensagem após verificar a prévia e os contatos.';
}
function operationalDetail(job) {
  const detail = job.detail || job.reason || '';
  return job.data?.preview_verified === true && safeURL(job.preview_url) && (!detail || detail === 'Na fila') ? job.reason || '' : detail || 'Na fila';
}
function updateRecordFields(form, status) {
  const channel = form.querySelector('.external-channel'), proof = form.querySelector('.send-proof');
  if (channel) {
    channel.hidden = status !== 'sent_external';
    channel.querySelector('select').required = status === 'sent_external';
  }
  if (proof) {
    proof.hidden = !['sent', 'sent_external'].includes(status);
    proof.querySelector('input').required = !proof.hidden;
  }
}
function productionCategory(job) {
  if (job.data?.preview_verified === true && safeURL(job.preview_url)) return 'ready';
  if (['blocked', 'skipped'].includes(job.stage)) return 'attention';
  return 'working';
}
function operationSection(job) {
  const items = state.operations.filter(item => item.job_id === job.id);
  const stages = state.stage_runs.filter(item => item.job_id === job.id);
  if (!items.length && !stages.length) return '';
  const usage = item => {
    try {
      const counts = JSON.parse(item.usage_json || '{}');
      if (Number.isInteger(counts.input_tokens) && Number.isInteger(counts.output_tokens))
        return `${counts.input_tokens} entrada / ${counts.output_tokens} saída`;
    } catch (_) { /* Legacy or unavailable usage. */ }
    return 'indisponíveis';
  };
  const rows = items.map(item => {
    const duration = Number.isFinite(Number(item.duration_seconds)) && item.duration_seconds !== null ? `${Number(item.duration_seconds).toFixed(1)} s` : 'indisponível';
    const remote = safeURL(item.remote_url);
    return `<li>${escapeHTML(item.kind)} · ${escapeHTML(item.status)} · ${escapeHTML(item.executor || 'indisponível')} / ${escapeHTML(item.model || 'indisponível')} · ${escapeHTML(item.attempts)} tentativa(s) · ${duration} · tokens: ${escapeHTML(usage(item))}${item.failure ? ` · ${escapeHTML(item.failure)}` : ''}${item.artifact ? ` · Artefato: ${escapeHTML(item.artifact)}` : ''}${item.remote_id ? ` · Deploy: ${escapeHTML(item.remote_id)}` : ''}${remote ? ` · <a href="${escapeHTML(remote)}" target="_blank" rel="noopener noreferrer">Abrir prévia ↗</a>` : ''}</li>`;
  });
  const stageRows = stages.map(item => `<li>${escapeHTML(label(item.stage))} · ${escapeHTML(item.status)} · ${escapeHTML(item.executor || 'indisponível')} / ${escapeHTML(item.model || 'indisponível')} / ${escapeHTML(item.effort || 'indisponível')} · tentativa ${escapeHTML(item.attempt)} · ${item.duration_seconds === null ? 'duração indisponível' : `${Number(item.duration_seconds).toFixed(1)} s`} · tokens: ${escapeHTML(usage(item))}${item.failure ? ` · ${escapeHTML(item.failure)}` : ''}</li>`);
  return `<section class="dialog-section"><div class="meta-label">Etapas desta empresa</div><ol class="timeline">${stageRows.join('')}</ol><div class="meta-label">Operações e artefatos</div><ol class="timeline">${rows.join('')}</ol><p>Custo: indisponível sem fonte confiável.</p></section>`;
}
function category(job) {
  if (isManual(job)) return 'manual';
  if (job.stage === 'simulated') return 'simulated';
  if (['failed', 'blocked', 'uncertain', 'needs_attention', 'error', 'rejected', 'skipped'].includes(job.stage)) return 'attention';
  if (['submitted', 'sent', 'replied', 'interested', 'not_interested', 'contacted'].includes(job.contact_status) || ['contacted', 'complete', 'completed', 'sent'].includes(job.stage)) return 'contacted';
  if (job.preview_url || ['published', 'deployed', 'ready'].includes(job.stage)) return 'ready';
  return 'working';
}
function commercialApprovalPayload(batchId, jobIds, rows) {
  const byId = new Map((Array.isArray(rows) ? rows : []).map(row => [String(row.job_id), row]));
  const reviewed = {};
  for (const id of jobIds) {
    const row = byId.get(String(id));
    if (!row || row.eligible !== true || row.channel !== 'email' || typeof row.approval_digest !== 'string' || !row.approval_digest) {
      throw new Error(`A revisão de ${id} não está mais válida. Atualize o lote e revise novamente.`);
    }
    reviewed[String(id)] = row.approval_digest;
  }
  return { batch_id: batchId, job_ids: jobIds, reviewed };
}
function commercialDuration(duration) {
  if (Number.isFinite(Number(duration)) && duration !== null && typeof duration !== 'object') return `${Number(duration).toFixed(1)} s`;
  if (!duration || typeof duration !== 'object' || Array.isArray(duration)) return 'indisponível';
  const entries = Object.entries(duration).filter(([, value]) => Number.isFinite(Number(value)) && value !== null);
  if (!entries.length) return 'indisponível';
  const total = entries.reduce((sum, [, value]) => sum + Number(value), 0);
  return `${total.toFixed(1)} s (${entries.map(([stage, value]) => `${escapeHTML(label(stage)).replace(/^./, char => char.toLocaleUpperCase('pt-BR'))}: ${Number(value).toFixed(1)} s`).join(' · ')})`;
}
function commercialApprovalFeedback(data = {}) {
  const capacity = data.capacity || {};
  const approved = Number.isFinite(Number(capacity.approved_new)) ? Number(capacity.approved_new) : 0;
  const batchRemaining = Number.isFinite(Number(capacity.remaining_batch)) ? capacity.remaining_batch : '—';
  const dailyRemaining = Number.isFinite(Number(capacity.remaining_daily)) ? capacity.remaining_daily : '—';
  return `Aprovado: ${approved} contato(s). Capacidade restante após a aprovação: ${batchRemaining} no lote e ${dailyRemaining} hoje. Despacho iniciado; acompanhe os resultados abaixo.`;
}
function commercialBatchesHTML(batches = {}) {
  const entries = Object.entries(batches || {});
  if (!entries.length) return '<div class="empty commercial-empty"><div><h3>Nenhuma mensagem preparada</h3><p>As empresas elegíveis aparecerão aqui depois da verificação da prévia.</p></div></div>';
  return entries.map(([batchId, batch]) => {
    const rows = Array.isArray(batch.rows) ? batch.rows : [];
    const counts = batch.counts || {}, capacity = batch.capacity || {};
    const selected = commercialSelection.get(String(batchId)) || new Set();
    const eligibleSelected = rows.filter(row => row.eligible === true && row.channel === 'email' && selected.has(String(row.job_id)));
    const rowHTML = rows.map(row => {
      const canSelect = row.eligible === true && row.channel === 'email';
      const checked = canSelect && selected.has(String(row.job_id));
      const blockers = Array.isArray(row.blockers) ? row.blockers : [];
      return `<article class="commercial-row"><label class="commercial-select"><input type="checkbox" data-commercial-select="${escapeHTML(batchId)}" data-job-id="${escapeHTML(row.job_id)}"${checked ? ' checked' : ''}${canSelect ? '' : ' disabled'} aria-label="Selecionar ${escapeHTML(row.name)}"></label><div class="commercial-row-main"><div class="commercial-row-title"><strong>${escapeHTML(row.name || 'Empresa sem nome')}</strong><span>${escapeHTML(row.segment || '')} · ${escapeHTML(row.opportunity_type || 'Oportunidade pendente')}</span></div><p class="commercial-preview">${safeURL(row.preview_url) ? `<a href="${escapeHTML(safeURL(row.preview_url))}" target="_blank" rel="noopener noreferrer">Prévia publicada ↗</a>` : 'Prévia indisponível'} · ${escapeHTML(row.recipient || 'Sem destinatário')} · Canal: ${escapeHTML(label(row.channel || 'no_channel'))}</p><p><strong>Assunto:</strong> ${escapeHTML(row.subject || 'Indisponível')}</p><pre class="commercial-message">${escapeHTML(row.message || 'Mensagem não preparada')}</pre><div class="commercial-row-status ${row.eligible ? 'eligible' : 'blocked'}">${row.eligible ? 'Elegível para Gmail' : 'Bloqueado'} · ${escapeHTML(label(row.status || 'prepared'))}${blockers.length ? `<ul>${blockers.map(item => `<li>${escapeHTML(item)}</li>`).join('')}</ul>` : ''}</div></div></article>`;
    }).join('');
    const approvable = Number(capacity.approvable_now ?? capacity.remaining_batch ?? eligibleSelected.length);
    const dailyLimit = Number.isFinite(Number(capacity.daily_limit)) && capacity.daily_limit !== null ? `${escapeHTML(capacity.daily_limit)} tentativas globais por dia UTC · ` : '';
    const batchStatus = counts.sending ? 'Envio em andamento' : counts.uncertain ? 'Resultado incerto' : counts.blocked ? 'Bloqueadas' : counts.sent ? 'Enviadas' : eligibleSelected.length ? 'Aguardando aprovação' : 'Mensagens preparadas';
    const operations = [batch.dispatch_status ? `Despacho: ${escapeHTML(label(batch.dispatch_status))}` : '', batch.operational_failure ? `Falha operacional: ${escapeHTML(batch.operational_failure)}` : ''].filter(Boolean);
    const savedFeedback = commercialApprovalFeedbackByBatch.get(String(batchId)) || '';
    return `<section class="commercial-batch" data-batch-id="${escapeHTML(batchId)}"><header class="commercial-batch-header"><div><span class="eyebrow">Lote ${escapeHTML(batchId)}</span><h3>${escapeHTML(batchStatus)}</h3></div><div class="commercial-counts">Prospectadas ${escapeHTML(counts.prospected ?? rows.length)} · Em produção ${escapeHTML(counts.in_production ?? 0)} · Prévias verificadas ${escapeHTML(counts.previews_verified ?? 0)} · Mensagens preparadas ${escapeHTML(counts.messages_prepared ?? rows.length)} · Aguardando aprovação ${escapeHTML(counts.awaiting_approval ?? 0)} · Envio em andamento ${escapeHTML(counts.sending ?? 0)} · Enviadas ${escapeHTML(counts.sent ?? 0)} · Bloqueadas ${escapeHTML(counts.blocked ?? 0)} · Resultado incerto ${escapeHTML(counts.uncertain ?? 0)}</div></header>${operations.length ? `<p class="commercial-operation-status" role="status">${operations.join(' · ')}</p>` : ''}<div class="commercial-rows">${rowHTML || '<p>Nenhum contato comercial neste lote.</p>'}</div><footer class="commercial-batch-footer"><span>Capacidade: ${escapeHTML(capacity.prior_attempts ?? 0)} tentativas anteriores · ${escapeHTML(capacity.remaining_batch ?? 0)} restantes no lote · ${dailyLimit}${escapeHTML(capacity.remaining_daily ?? 0)} restantes hoje · esta aprovação permitirá até ${escapeHTML(Math.min(approvable, eligibleSelected.length))} envio(s) selecionado(s) · Duração total e por etapa: ${commercialDuration(batch.duration_seconds)}</span><button type="button" class="primary commercial-approve" data-approve-batch="${escapeHTML(batchId)}"${eligibleSelected.length && approvable > 0 ? '' : ' disabled'}>Aprovar seleção e iniciar envio</button><span class="commercial-feedback" role="status" aria-live="polite">${escapeHTML(savedFeedback)}</span></footer></section>`;
  }).join('');
}
function jobCard(job, index) {
  const initials = String(job.name || '?').split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
  const followup = state.gmail_followups?.[job.id];
  const followupHint = followup?.next_touch ? `<p class="job-detail">${followup.due ? `Follow-up do dia ${followup.next_touch === 1 ? '4' : '10'} para revisar` : `Próximo follow-up: ${escapeHTML(time(followup.due_at))}`}</p>` : '';
  const detail = operationalDetail(job);
  return `<button class="job-card${isManual(job) ? ' manual-card' : ''}" data-job="${escapeHTML(job.id)}" aria-label="Abrir detalhes de ${escapeHTML(job.name || 'empresa')}"><div class="job-cover"><span class="job-number">${String(index + 1).padStart(2, '0')}</span><span class="cover-monogram" aria-hidden="true">${escapeHTML(initials)}</span><span class="cover-caption">${job.preview_url ? 'Prévia ↗' : ''}</span></div><div class="job-info"><h3>${escapeHTML(job.name || 'Empresa sem nome')}</h3><div class="job-domain">${escapeHTML(job.domain || 'Sem site próprio registrado')}</div><p class="job-detail">${escapeHTML(job.data?.commercial_category || 'Sem categoria')} · ${escapeHTML(job.data?.opportunity_type || 'Tipo pendente')}</p><p class="job-detail">Contato: ${escapeHTML(label(job.contact_status || 'not_sent'))}</p><p class="job-detail">Próxima ação: ${escapeHTML(nextCommercialAction(job))}</p>${followupHint}${detail ? `<p class="job-detail">${escapeHTML(detail)}</p>` : ''}<div class="job-bottom"><span class="stage ${productionCategory(job)}">Produção: ${escapeHTML(production(job))}</span><span class="job-arrow" aria-hidden="true">↗</span></div></div></button>`;
}
function render() {
  $('#commercial-batches').innerHTML = commercialBatchesHTML(state.commercial_batches);
  const batches = state.batches;
  if (batchFilter !== 'all' && !batches.some(batch => String(batch.id) === batchFilter)) batchFilter = 'all';
  const select = $('#batch-filter');
  select.innerHTML = '<option value="all">Todos os lotes</option>' + batches.map(batch => `<option value="${escapeHTML(batch.id)}">${escapeHTML(batch.industry)} · ${escapeHTML(batch.city)} · ${escapeHTML(batch.published_count || 0)}/${escapeHTML(batch.requested_count || 3)} prévias</option>`).join('');
  select.value = batchFilter;
  const allJobs = state.jobs.filter(job => batchFilter === 'all' || String(job.batch_id) === batchFilter);
  const jobs = allJobs.filter(job => stageFilter === 'all' || category(job) === stageFilter);
  $('#edition-count').textContent = String(state.jobs.filter(job => job.data?.preview_verified === true && safeURL(job.preview_url)).length).padStart(2, '0');
  $('#sheet-count').textContent = jobs.length;
  $('#manual-count').textContent = allJobs.filter(isManual).length;
  const maxWorkers = Math.max(1, Number(state.settings.max_workers) || 3);
  const selectedBatch = batches.find(batch => String(batch.id) === batchFilter);
  const target = selectedBatch ? Number(selectedBatch.requested_count) || 3 : batches.reduce((sum, batch) => sum + (Number(batch.requested_count) || 3), 0);
  const completed = allJobs.filter(job => job.data?.preview_verified === true && safeURL(job.preview_url)).length;
  $('#capacity-note').textContent = `${completed}/${target} prévias · ${maxWorkers} em paralelo`;
  $('#funnel').textContent = `Descobertos ${allJobs.length} · Verificados ${allJobs.filter(job => job.data?.presence_status).length} · Qualificados ${allJobs.filter(job => ['A_prioritaria','B_promissora','C_potencial'].includes(job.data?.commercial_category)).length} · Publicados ${completed} · Pendências ${allJobs.filter(job => ['blocked','skipped'].includes(job.stage) || ['D_pendente','descartada'].includes(job.data?.commercial_category)).length}`;
  const activeWorkers = state.workers.filter(worker => worker.job_id && !['idle', 'complete', 'completed', 'stopped'].includes(worker.status));
  const assigned = new Set();
  $('#workers').innerHTML = Array.from({ length: maxWorkers }, (_, index) => {
    const worker = activeWorkers[index];
    const activeJob = worker && state.jobs.find(job => String(job.id) === String(worker.job_id));
    if (activeJob) assigned.add(activeJob.id);
    const queued = !worker && allJobs.filter(job => ['queued', 'pending', 'discovered'].includes(job.stage) && !assigned.has(job.id))[0];
    if (queued) assigned.add(queued.id);
    const busy = Boolean(worker), title = activeJob?.name || (worker ? 'Trabalhador ativo' : queued?.name || 'Inativo');
    const detail = activeJob ? `${stageLabel(activeJob)} · ${worker.id}` : worker ? label(worker.status) : queued ? 'Na fila' : index >= maxWorkers ? 'Em espera' : 'Disponível';
    return `<div class="worker ${busy ? 'busy' : ''}"${busy ? ` data-updated-at="${escapeHTML(worker.updated_at || '')}"` : ''}><div class="worker-number">POSTO ${String(index + 1).padStart(2, '0')} <span class="worker-dot" aria-hidden="true"></span></div><div class="worker-title">${escapeHTML(title)}</div><div class="worker-detail">${escapeHTML(detail)}</div>${busy ? '<div class="worker-age" role="status" aria-live="polite" hidden></div>' : ''}</div>`;
  }).join('');
  refreshWorkerAges();
  const queuedBatches = batches.filter(batch => (batchFilter === 'all' || String(batch.id) === batchFilter) && ['queued', 'pending'].includes(batch.status));
  $('#queue-status').hidden = !queuedBatches.length;
  $('#queue-status').textContent = `${queuedBatches.length} lote${queuedBatches.length === 1 ? '' : 's'} na fila. Peça ao Codex para executar.`;
  if (!jobs.length) {
    const filtered = state.jobs.length > 0 && (batchFilter !== 'all' || stageFilter !== 'all');
    $('#jobs').innerHTML = `<div class="empty"><div><div class="empty-mark" aria-hidden="true">✳</div><h3>${filtered ? 'Nenhum resultado' : 'Nenhuma empresa ainda'}</h3><p>${filtered ? 'Tente outro filtro.' : 'Enfileire o primeiro lote acima.'}</p></div></div>`;
  } else {
    $('#jobs').innerHTML = jobs.map(jobCard).join('');
  }
  if (selectedJob && $('#job-dialog').open) renderDialog();
}
// Update only the worker warnings as time passes; preserve form inputs, filters,
// focus, and the existing job sheet when the server state itself is unchanged.
function refreshWorkerAges() {
  const now = Date.now();
  document.querySelectorAll('.worker[data-updated-at]').forEach(element => {
    const updatedAt = Date.parse(element.dataset.updatedAt);
    const age = now - updatedAt;
    const stale = Number.isFinite(updatedAt) && age > 120000;
    const warning = element.querySelector('.worker-age');
    element.classList.toggle('stale', stale);
    warning.hidden = !stale;
    const message = stale ? `Sem atualização há ${Math.floor(age / 60000)} min · pode estar parado` : '';
    if (warning.textContent !== message) warning.textContent = message;
  });
}
function renderDialog() {
  const job = state.jobs.find(item => String(item.id) === String(selectedJob));
  if (!job) return;
  const original = safeURL(job.url), preview = safeURL(job.preview_url);
  const events = state.events.filter(event => String(event.job_id) === String(job.id)).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  $('#dialog-content').innerHTML = `<h2 id="dialog-title">${escapeHTML(job.name)}</h2><span class="stage ${productionCategory(job)}">${escapeHTML(production(job))}</span><div class="dialog-links">${original ? `<a href="${escapeHTML(original)}" target="_blank" rel="noopener noreferrer">Original ↗</a>` : ''}${preview ? `<a class="preview" href="${escapeHTML(preview)}" target="_blank" rel="noopener noreferrer">Prévia ↗</a>` : ''}</div><section class="dialog-section"><div class="meta-label">Oportunidade</div><p>${escapeHTML(job.data?.commercial_category || 'Pendente')} · ${escapeHTML(job.data?.opportunity_type || 'Não definido')}</p><p>${escapeHTML(job.data?.commercial_reason || '')}</p><div class="meta-label">Produção</div><p>${escapeHTML(production(job))} · ${escapeHTML(job.data?.presence_status || 'Presença não verificada')}</p></section>${renderContacts(job.data?.contacts)}${commercialSection(job)}${manualOutreach(job)}${contactSimulation(job)}${operationSection(job)}<section class="dialog-section"><div class="meta-label">Andamento</div>${operationalDetail(job) ? `<p>${escapeHTML(operationalDetail(job))}</p>` : ''}<div class="meta-label">Trabalhador · atualização</div><p>${escapeHTML(job.worker || 'Não atribuído')} / ${escapeHTML(time(job.updated_at))}</p></section>${job.reason ? `<section class="dialog-section"><div class="meta-label">Motivo</div><p>${escapeHTML(job.reason)}</p></section>` : ''}<section class="dialog-section"><div class="meta-label">Atividade</div>${events.length ? `<ol class="timeline">${events.map(event => `<li>${escapeHTML(event.message)}<time class="timeline-time">${escapeHTML(time(event.created_at))}</time></li>`).join('')}</ol>` : '<p>Nenhuma atividade registrada.</p>'}</section>`;
}
async function poll() {
  try {
    const response = await fetch('/api/state', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const data = await response.json();
    for (const key of ['batches', 'jobs', 'events', 'workers', 'operations', 'stage_runs', 'templates', 'commercial_attempts', 'legacy_submissions']) state[key] = Array.isArray(data[key]) ? data[key] : [];
    state.settings = data.settings || state.settings;
    state.commercial_batches = data.commercial_batches || {};
    state.gmail_authorization = data.gmail_authorization || {};
    state.gmail_followups = data.gmail_followups || {};
    const choices = '<option value="">Selecione o segmento</option><option value="all">Todos os segmentos</option>' + state.templates.map(item => `<option value="${escapeHTML(item.id)}">${escapeHTML(item.name)}</option>`).join('');
    const segmentSelect = $('#batch-form').elements.industry;
    if (segmentSelect.dataset.choices !== choices) { const value = segmentSelect.value; segmentSelect.innerHTML = choices; segmentSelect.value = value; segmentSelect.dataset.choices = choices; }
    const signature = JSON.stringify(state);
    connected = true;
    $('#connection').className = 'connection online';
    $('#connection span').textContent = 'Conectado';
    $('#clock').textContent = `ÚLTIMA SINCRONIZAÇÃO / ${new Date().toLocaleTimeString('pt-BR', {hour:'2-digit',minute:'2-digit'})}`;
    if (signature !== previousSignature) { previousSignature = signature; render(); if (selectedJob) renderDialog(); }
  } catch {
    connected = false;
    $('#connection').className = 'connection offline';
    $('#connection span').textContent = previousSignature ? 'Reconectando' : 'Desconectado';
  } finally { setTimeout(poll, document.hidden ? 8000 : 2000); }
}
$('#batch-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget, button = form.querySelector('button');
  const industry = form.elements.industry.value.trim(), city = form.elements.city.value.trim(), requestedCount = Number(form.elements.requested_count.value);
  if (!industry || !city || !Number.isInteger(requestedCount) || requestedCount < 1 || requestedCount > 100) { $('#form-message').textContent = 'Informe segmento, cidade ou estado e uma meta de 1 a 100.'; return; }
  button.disabled = true;
  $('#form-message').textContent = 'Adicionando lote…';
  try {
    const response = await fetch('/api/batches', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ industry, city, requested_count: requestedCount }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível enfileirar o lote.');
    $('#form-message').textContent = `Lote de ${requestedCount} prévias para ${industry} em ${city} enfileirado. Peça ao Codex para executar.`;
    form.reset();
    form.elements.requested_count.value = '3';
    previousSignature = '';
  } catch (error) { $('#form-message').textContent = `Não foi possível enfileirar o lote: ${error.message}`; }
  finally { button.disabled = false; }
});
$('#batch-filter').addEventListener('change', event => { batchFilter = event.target.value; render(); });
$('#commercial-batches').addEventListener('change', event => {
  const input = event.target.closest('[data-commercial-select]');
  if (!input) return;
  const batchId = String(input.dataset.commercialSelect), jobId = String(input.dataset.jobId);
  const selected = commercialSelection.get(batchId) || new Set();
  if (input.checked) selected.add(jobId); else selected.delete(jobId);
  commercialApprovalFeedbackByBatch.delete(batchId);
  commercialSelection.set(batchId, selected);
  render();
});
$('#commercial-batches').addEventListener('click', async event => {
  const button = event.target.closest('[data-approve-batch]');
  if (!button) return;
  const batchId = String(button.dataset.approveBatch), jobIds = [...(commercialSelection.get(batchId) || new Set())];
  if (!jobIds.length) return;
  const feedback = button.parentElement.querySelector('.commercial-feedback');
  button.disabled = true;
  feedback.textContent = 'Registrando aprovação e iniciando despacho sequencial…';
  try {
    const batch = state.commercial_batches?.[batchId];
    const payload = commercialApprovalPayload(batchId, jobIds, batch?.rows);
    const response = await fetch('/api/commercial/batch-approve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'A aprovação do lote foi recusada.');
    commercialSelection.delete(batchId);
    const approvalFeedback = commercialApprovalFeedback(data);
    commercialApprovalFeedbackByBatch.set(batchId, approvalFeedback);
    feedback.textContent = approvalFeedback;
    previousSignature = '';
    await poll();
  } catch (error) {
    commercialApprovalFeedbackByBatch.delete(batchId);
    feedback.textContent = error.message;
    button.disabled = false;
  }
});
$('#stage-filters').addEventListener('click', event => {
  const button = event.target.closest('[data-filter]');
  if (!button) return;
  stageFilter = button.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(item => { const active = item === button; item.classList.toggle('active', active); item.setAttribute('aria-pressed', String(active)); });
  render();
});
$('#jobs').addEventListener('click', event => {
  const card = event.target.closest('[data-job]');
  if (!card) return;
  selectedJob = card.dataset.job; renderDialog(); $('#job-dialog').showModal();
});
$('#dialog-content').addEventListener('click', async event => {
  if (['gmail-simulate', 'gmail-followup'].includes(event.target.id)) {
    const button = event.target;
    button.disabled = true;
    try {
      const route = button.id;
      const response = await fetch(`/api/commercial/${route}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({job_id:selectedJob, touch:route === 'gmail-followup' ? Number(button.dataset.touch) : undefined})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      $('#commercial-feedback').textContent = route === 'gmail-simulate'
        ? `Simulação: contato ${data.commercial_eligibility.eligible ? 'elegível' : 'bloqueado'} (${data.commercial_eligibility.reason}); envio live ${data.live_authorized ? 'autorizado' : 'não autorizado'} (${data.authorization.reason}). Nenhum e-mail enviado.`
        : `Resultado: ${data.status}${data.gmail_message_id ? ' · Gmail ID: ' + data.gmail_message_id : ''}`;
      previousSignature = '';
    } catch (error) { $('#commercial-feedback').textContent = error.message; }
    finally { button.disabled = false; }
    return;
  }
  const copyPhone = event.target.closest('.copy-phone');
  if (copyPhone) {
    const status = copyPhone.nextElementSibling;
    try {
      await navigator.clipboard.writeText(copyPhone.dataset.copyPhone);
      status.textContent = 'Copiado.';
    } catch { status.textContent = 'Não foi possível copiar.'; }
    return;
  }
  const button = event.target.closest('#copy-message');
  if (!button) return;
  const message = $('#manual-message'), status = $('#copy-status');
  button.disabled = true;
  try {
    await navigator.clipboard.writeText(message.value);
    status.textContent = 'Mensagem copiada.';
  } catch {
    message.focus();
    message.select();
    status.textContent = 'Não foi possível copiar automaticamente. A mensagem foi selecionada; use o comando de copiar do dispositivo.';
  } finally { button.disabled = false; }
});
$('#close-dialog').addEventListener('click', () => $('#job-dialog').close());
$('#job-dialog').addEventListener('close', () => { selectedJob = null; });
$('#job-dialog').addEventListener('click', event => { if (event.target === event.currentTarget) { const rect = event.currentTarget.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) event.currentTarget.close(); } });
render(); poll();
setInterval(refreshWorkerAges, 10000);

$('#dialog-content').addEventListener('click', async event => {
  if (event.target.id === 'regenerate-commercial') {
    const button = event.target;
    button.disabled = true;
    try {
      const response = await fetch('/api/commercial/regenerate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({job_id:selectedJob})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Não foi possível regenerar a mensagem.');
      $('#commercial-feedback').textContent = 'Mensagem regenerada sem telefone. Nenhum contato foi enviado.';
      previousSignature = '';
    } catch (error) { $('#commercial-feedback').textContent = error.message; }
    finally { button.disabled = false; }
    return;
  }
  if (event.target.id === 'copy-commercial') {
    const field = $('#commercial-message');
    try { await navigator.clipboard.writeText(field.value); $('#commercial-feedback').textContent = 'Mensagem copiada.'; }
    catch { field.select(); $('#commercial-feedback').textContent = 'Selecione e copie a mensagem.'; }
  }
  if (event.target.id === 'prepare-commercial') {
    const job = state.jobs.find(item => item.id === selectedJob);
    let observation = '';
    if (job?.data?.presence_status === 'site_inoperante') observation = window.prompt('Descreva a falha técnica verificada recentemente:') || '';
    try {
      const response = await fetch('/api/commercial/prepare', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({job_id:selectedJob, observation})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      $('#commercial-feedback').textContent = 'Mensagem preparada. Nenhum contato foi enviado.';
      previousSignature = '';
    } catch (error) { $('#commercial-feedback').textContent = error.message; }
  }
});
$('#dialog-content').addEventListener('submit', async event => {
  if (event.target.id !== 'commercial-record') return;
  event.preventDefault();
  const payload = {job_id:selectedJob, status:event.target.elements.status.value, evidence:event.target.elements.evidence.value, channel:event.target.elements.channel?.value || '', proof:event.target.elements.proof?.value || ''};
  try {
    const response = await fetch('/api/commercial/record', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    $('#commercial-feedback').textContent = 'Resultado registrado.';
    previousSignature = '';
  } catch (error) { $('#commercial-feedback').textContent = error.message; }
});

$('#dialog-content').addEventListener('change', event => {
  if (event.target.name !== 'status' || event.target.form?.id !== 'commercial-record') return;
  updateRecordFields(event.target.form, event.target.value);
});
