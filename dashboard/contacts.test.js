const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const app = fs.readFileSync(path.join(__dirname, 'app.js'), 'utf8');
const context = vm.createContext({ URL, Intl, Date });
vm.runInContext(app.slice(0, app.indexOf('function manualOutreach')) + '\nthis.renderContacts = renderContacts;', context);
const render = context.renderContacts;

test('telefone válido gera discagem, formatação e cópia; inválido fica sem link', () => {
  const valid = render({ phone: { value: '+55 (14) 99999-1234' } });
  assert.match(valid, /\+55 \(14\) 99999-1234/);
  assert.match(valid, /href="tel:\+5514999991234"/);
  assert.match(valid, /data-copy-phone="\+5514999991234"/);
  const invalid = render({ phone: { value: '123<script>' } });
  assert.match(invalid, /Número inválido/);
  assert.doesNotMatch(invalid, /href="tel:|data-copy-phone=|<script>/);
});

test('WhatsApp distingue confirmado, presumido, indisponível e não verificado', () => {
  const phone = { value: '(14) 3222-1234', source: 'https://example.org/ficha', checked_at: '2026-10-11' };
  const confirmed = render({ phone, whatsapp: { status: 'confirmado', value: '+55 (14) 98888-7777', source: 'https://example.org/whatsapp', checked_at: '2026-10-11' } });
  assert.match(confirmed, /Confirmado · \+55 \(14\) 98888-7777 · <a href="https:\/\/wa.me\/5514988887777"/);
  assert.doesNotMatch(confirmed, /wa.me\/551432221234/);
  const presumed = render({ phone, whatsapp: { status: 'presumido' } });
  assert.match(presumed, /Presumido · telefone público · \(14\) 3222-1234 · <a href="https:\/\/wa.me\/551432221234"/);
  assert.match(presumed, /example.org ↗/);
  assert.doesNotMatch(render({ phone: { value: phone.value }, whatsapp: { status: 'presumido' } }), /wa.me/);
  assert.doesNotMatch(render({ phone: { ...phone, source: 'http://localhost/ficha' }, whatsapp: { status: 'presumido' } }), /wa.me/);
  assert.doesNotMatch(render({ phone: { ...phone, checked_at: '2999-01-01' }, whatsapp: { status: 'presumido' } }), /wa.me/);
  assert.doesNotMatch(render({ phone, whatsapp: { status: 'confirmado', value: '+5514988887777' } }), /wa.me/);
  for (const status of ['nao_utiliza', 'nao_verificado']) assert.doesNotMatch(render({ phone, whatsapp: { status } }), /wa.me/);
  assert.match(render({ phone, whatsapp: { status: 'confirmado', value: 'abc' } }), /Número indisponível/);
  assert.doesNotMatch(render({ phone, whatsapp: { status: 'presumido' }, phone: { value: 'abc' } }), /wa.me/);
});

test('e-mail separa encontrado, não encontrado e não verificado', () => {
  assert.match(render({ email: { status: 'encontrado', value: 'oi@example.org' } }), /href="mailto:oi%40example.org"/);
  assert.match(render({ email: { status: 'nao_encontrado' } }), /E-mail<\/div><div class="contact-main">Não encontrado/);
  assert.match(render({ email: { status: 'nao_verificado' } }), /E-mail<\/div><div class="contact-main">Não verificado/);
  assert.doesNotMatch(render({ email: { status: 'encontrado', value: 'x@' } }), /href="mailto:/);
});

test('formulário mostra finalidade, elegibilidade e restrições sem submissão', () => {
  const base = { status: 'encontrado', url: 'https://example.org/contato', purpose: 'orçamento', restrictions: ['somente clientes'] };
  const eligible = render({ form: { ...base, eligible: true } });
  assert.match(eligible, /Formulário existente/);
  assert.match(eligible, /Apropriado para contato comercial/);
  assert.match(eligible, /Finalidade: orçamento/);
  assert.match(eligible, /Restrições: somente clientes/);
  assert.match(eligible, /href="https:\/\/example.org\/contato" target="_blank" rel="noopener noreferrer"/);
  assert.doesNotMatch(eligible, /<form|<input|<script/);
  assert.match(render({ form: { ...base, eligible: false } }), /Não apropriado para contato comercial/);
});

test('fonte, URL e data ausentes ou inválidas não geram evidência fictícia', () => {
  const missing = render({ phone: { value: '14 3222-1234' } });
  assert.match(missing, /Fonte não registrada/);
  assert.doesNotMatch(missing, /Verificado em/);
  const invalid = render({ phone: { value: '14 3222-1234', source: 'javascript:alert(1)', checked_at: '2026-02-30' } });
  assert.match(invalid, /Fonte não registrada/);
  assert.doesNotMatch(invalid, /javascript:|Verificado em/);
  const dated = render({ phone: { value: '14 3222-1234', source: 'https://www.example.org/ficha', checked_at: '2026-10-11' } });
  assert.match(dated, /example.org ↗/);
  assert.match(dated, /Verificado em 11\/10\/2026/);
});

test('dados parciais e legados são legíveis e seguros', () => {
  assert.match(render(undefined), /Não registrado/);
  assert.match(render({}), /Não registrado/);
  const legacy = render({ phone: '14 3222-1234', email: 'oi@example.org', form: 'https://example.org/contato', whatsapp: false });
  assert.match(legacy, /href="tel:1432221234"/);
  assert.match(legacy, /href="mailto:oi%40example.org"/);
  assert.match(legacy, /Formulário existente/);
  assert.match(legacy, /Não utiliza WhatsApp/);
});

test('strings maliciosas não entram como HTML ou URLs executáveis', () => {
  const html = render({
    phone: { value: '<img src=x onerror=alert(1)>', source: 'javascript:alert(1)' },
    whatsapp: { status: 'confirmado', value: 'javascript:alert(1)' },
    email: { status: 'encontrado', value: '" onmouseover="alert(1)@example.org' },
    form: { status: 'encontrado', url: 'javascript:alert(1)', purpose: '<script>alert(1)</script>', restrictions: ['<img src=x>'] },
  });
  assert.doesNotMatch(html, /<script|<img|onmouseover=|onerror=|href="javascript:/);
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
  assert.match(html, /URL inválida/);
});

test('layout limita largura do modal e quebra conteúdo no mobile', () => {
  const css = fs.readFileSync(path.join(__dirname, 'style.css'), 'utf8');
  assert.match(css, /dialog\{width:min\(540px,calc\(100vw - 32px\)\)/);
  assert.match(css, /\.contact-grid\{display:grid;grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
  assert.match(css, /\.contact-main\{[^}]*overflow-wrap:anywhere/);
  assert.match(css, /@media\(max-width:650px\)\{dialog\{padding:18px\}\.contact-grid\{grid-template-columns:minmax\(0,1fr\)\}\}/);
});

test('produção publicada e contato comercial permanecem separados', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nthis.commercialSection = commercialSection; this.productionCategory = productionCategory; this.production = production;', display);
  const job = { id: 'job-1', stage: 'ready', contact_status: 'prepared', preview_url: 'https://preview.example',
    data: { preview_verified: true, commercial_contact: { channel: 'whatsapp_manual', template: 'redesign', message: 'Proposta', whatsapp_url: 'https://wa.me/5514999999999?text=Proposta' } } };
  const prepared = display.commercialSection(job);
  assert.match(prepared, /Contato comercial/);
  assert.match(prepared, /Contato externo comprovado/);
  assert.doesNotMatch(prepared, /<option value="replied">/);
  assert.match(prepared, /abrir não registra envio/);
  job.contact_status = 'sent';
  assert.equal(display.production(job), 'Prévia verificada');
  assert.equal(display.productionCategory(job), 'ready');
  assert.match(display.commercialSection(job), /<option value="replied">/);
});

test('cartão de prévia verificada e envio confirmado oculta andamento legado na fila', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function render()')) + '\nthis.jobCard = jobCard; this.production = production;', display);
  const job = { id: 'job-1', name: 'Empresa Teste', stage: 'queued', detail: 'Na fila', contact_status: 'sent', preview_url: 'https://preview.example', data: { preview_verified: true } };
  const html = display.jobCard(job, 0);
  assert.match(html, /Produção: Prévia verificada/);
  assert.match(html, /Contato: Enviado/);
  assert.match(html, /Próxima ação: Aguardar resposta/);
  assert.doesNotMatch(html, /Na fila/);
  assert.equal(job.stage, 'queued');
  assert.equal(job.contact_status, 'sent');
  assert.match(display.jobCard({ ...job, reason: 'Revisão necessária' }, 0), /Revisão necessária/);
  assert.match(display.jobCard({ ...job, data: { preview_verified: false } }, 0), /Na fila/);
});

test('mensagem de e-mail preparada mostra simulação e não oferece envio individual', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nstate.gmail_authorization = { "job-1": { mode: "live", authorized: true, sender: "scarasoftbauru@gmail.com", reason: "Autorizado" } }; this.commercialSection = commercialSection;', display);
  const job = { id: 'job-1', stage: 'ready', contact_status: 'prepared', preview_url: 'https://preview.example',
    data: { preview_verified: true, commercial_contact: { channel: 'email', destination: 'empresa@example.org', subject: 'Proposta', message: 'Texto preparado' } } };
  const html = display.commercialSection(job);
  assert.match(html, /Destinatário: empresa@example.org/);
  assert.match(html, /Remetente: scarasoftbauru@gmail.com/);
  assert.match(html, /id="gmail-simulate"/);
  assert.doesNotMatch(html, /id="gmail-send"/);
  assert.match(html, /revisão do lote comercial/);
  assert.doesNotMatch(html, /id="prepare-commercial"/);
});

test('visão de lote mostra mensagem integral, capacidade e permite selecionar apenas e-mail elegível', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function jobCard(job, index)')) + '\nthis.commercialBatchesHTML = commercialBatchesHTML;', display);
  const html = display.commercialBatchesHTML({ lote1: { rows: [
    { job_id: 'j1', name: 'Oficina Um', segment: 'Oficina', opportunity_type: 'Sem site', preview_url: 'https://example.org/p', recipient: 'a@example.org', subject: 'Assunto', message: 'Mensagem completa sem corte.', channel: 'email', eligible: true, blockers: [] },
    { job_id: 'j2', name: 'Oficina Dois', recipient: '14 99999-1111', channel: 'whatsapp_manual', eligible: true, blockers: [] },
    { job_id: 'j3', name: 'Oficina Três', recipient: 'b@example.org', channel: 'email', eligible: false, blockers: ['Opt-out registrado'] }
  ], counts: { prospected: 3, in_production: 1, previews_verified: 2, messages_prepared: 2, awaiting_approval: 1, sending: 0, sent: 1, blocked: 1, uncertain: 0 }, duration_seconds: { discovery: 4, publish: 8 }, capacity: { prior_attempts: 1, remaining_batch: 4, remaining_daily: 8, approvable_now: 4 } } });
  assert.match(html, /Mensagem completa sem corte\./);
  assert.match(html, /<strong>Assunto:<\/strong>/);
  assert.match(html, /Em produção 1/);
  assert.match(html, /Prévias verificadas 2/);
  assert.match(html, /Mensagens preparadas 2/);
  assert.match(html, /disabled aria-label="Selecionar Oficina Dois"/);
  assert.match(html, /disabled aria-label="Selecionar Oficina Três"/);
  assert.match(html, /Opt-out registrado/);
  assert.match(html, /1 tentativas anteriores/);
  assert.match(html, /12\.0 s/);
  assert.match(html, /Discovery: 4\.0 s/);
  assert.doesNotMatch(html, /javascript:/);
});

test('aprovação inclui hash revisado de cada contato e recusa linha inelegível ou desatualizada', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function jobCard(job, index)')) + '\nthis.commercialApprovalPayload = commercialApprovalPayload;', display);
  const rows = [
    { job_id: 'a', eligible: true, channel: 'email', approval_digest: 'sha256:a' },
    { job_id: 'b', eligible: true, channel: 'email', approval_digest: 'sha256:b' },
    { job_id: 'c', eligible: false, channel: 'email', approval_digest: 'sha256:c' }
  ];
  assert.deepEqual(JSON.parse(JSON.stringify(display.commercialApprovalPayload('batch-x', ['a', 'b'], rows))), {
    batch_id: 'batch-x', job_ids: ['a', 'b'], reviewed: { a: 'sha256:a', b: 'sha256:b' }
  });
  assert.throws(() => display.commercialApprovalPayload('batch-x', ['c'], rows), /não está mais válida/);
  assert.throws(() => display.commercialApprovalPayload('batch-x', ['missing'], rows), /não está mais válida/);
  rows[0].approval_digest = '';
  assert.throws(() => display.commercialApprovalPayload('batch-x', ['a'], rows), /não está mais válida/);
});

test('aprovação fica desabilitada sem seleção e lote vazio orienta o operador', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function jobCard(job, index)')) + '\nthis.commercialBatchesHTML = commercialBatchesHTML;', display);
  const empty = display.commercialBatchesHTML({});
  assert.match(empty, /Nenhuma mensagem preparada/);
  const html = display.commercialBatchesHTML({ b: { rows: [{ job_id: 'j', name: 'X', channel: 'email', eligible: true }], capacity: { approvable_now: 2 } } });
  assert.match(html, /Aprovar seleção e iniciar envio/);
  assert.match(html, /disabled/);
});

test('mensagem antiga com telefone exige revisão e não oferece ações de envio ou cópia', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nstate.gmail_authorization = { "job-1": { mode: "live", authorized: true, sender: "scarasoftbauru@gmail.com", reason: "Autorizado" } }; this.commercialSection = commercialSection; this.manualOutreach = manualOutreach; this.contactSimulation = contactSimulation;', display);
  const job = { id: 'job-1', stage: 'ready', contact_status: 'prepared', commercial_requires_review: true, preview_url: 'https://preview.example', data: { preview_verified: true, commercial_contact: { channel: 'email', destination: 'empresa@example.org', subject: 'Proposta', message: 'Mensagem antiga' } } };
  let html = display.commercialSection(job);
  assert.match(html, /revise antes de qualquer envio/);
  assert.doesNotMatch(html, /id="copy-commercial"|id="gmail-send"|id="gmail-simulate"/);
  job.data.commercial_contact = { channel: 'whatsapp_manual', message: 'Mensagem antiga', whatsapp_url: 'https://wa.me/5514999999999?text=Mensagem' };
  html = display.commercialSection(job);
  assert.doesNotMatch(html, /Abrir WhatsApp com texto|id="copy-commercial"/);
  job.stage = 'manual';
  job.data.manual_outreach = { message: 'Mensagem antiga', phone: '+5514999999999' };
  assert.doesNotMatch(display.manualOutreach(job), /id="copy-message"/);
  assert.match(display.manualOutreach(job), /Telefone verificado/);
  job.stage = 'simulated';
  job.data.contact_simulation = { message: 'Mensagem antiga' };
  assert.doesNotMatch(display.contactSimulation(job), /id="copy-message"/);
});

test('regeneração aparece somente para mensagem antiga elegível e bloqueada para revisão', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nthis.commercialSection = commercialSection;', display);
  const job = { id: 'job-1', stage: 'ready', contact_status: 'prepared', commercial_requires_review: true, commercial_can_regenerate: true, preview_url: 'https://preview.example', data: { preview_verified: true, commercial_contact: { channel: 'email', destination: 'empresa@example.org', subject: 'Proposta', message: 'Mensagem antiga com telefone' } } };
  let html = display.commercialSection(job);
  assert.match(html, /id="regenerate-commercial"/);
  assert.match(html, /Regenerar mensagem sem telefone/);
  assert.doesNotMatch(html, /id="gmail-send"|id="gmail-simulate"|id="copy-commercial"/);

  job.commercial_can_regenerate = false;
  html = display.commercialSection(job);
  assert.match(html, /Mensagem com número de telefone/);
  assert.doesNotMatch(html, /id="regenerate-commercial"/);

  job.commercial_can_regenerate = true;
  job.contact_status = 'sent';
  html = display.commercialSection(job);
  assert.doesNotMatch(html, /id="regenerate-commercial"/);
});

test('acompanhamento mostra datas e ação apenas quando vencido e autorizado', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nstate.gmail_authorization = { "job-1": { mode: "live", authorized: true, sender: "scarasoftbauru@gmail.com", reason: "Autorizado" } }; state.gmail_followups = { "job-1": { available: true, first_sent_at: "2026-10-01T12:00:00+00:00", day4_due_at: "2026-10-05T12:00:00+00:00", day10_due_at: "2026-10-11T12:00:00+00:00", day4_status: "pending", day10_status: "pending", next_touch: 1, due: true, message: "Olá!" } }; this.commercialSection = commercialSection;', display);
  const job = { id: 'job-1', stage: 'ready', contact_status: 'sent', preview_url: 'https://preview.example', data: { preview_verified: true, commercial_contact: { channel: 'email', destination: 'empresa@example.org', subject: 'Proposta', message: 'Texto preparado' } } };
  assert.match(display.commercialSection(job), /id="gmail-followup" data-touch="1"/);
  assert.match(display.commercialSection(job), /Primeiro envio:/);
  vm.runInContext('state.gmail_followups["job-1"].due = false;', display);
  assert.doesNotMatch(display.commercialSection(job), /id="gmail-followup"/);
});

test('após Gmail confirmado, resposta e opt-out pedem somente evidência textual', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nstate.commercial_attempts = [{ job_id: "job-1", source: "gmail_api", channel: "email", status: "sent", evidence: "Gmail confirmou", sender: "scarasoftbauru@gmail.com", gmail_message_id: "gmail12345678", created_at: "2026-10-01T12:00:00Z" }]; this.commercialSection = commercialSection;', display);
  const job = { id: 'job-1', stage: 'ready', contact_status: 'sent', preview_url: 'https://preview.example', data: { preview_verified: true, commercial_contact: { channel: 'email', destination: 'empresa@example.org', subject: 'Proposta', message: 'Texto preparado' } } };
  const html = display.commercialSection(job);
  for (const status of ['replied', 'interested', 'not_interested', 'opted_out']) assert.match(html, new RegExp(`value="${status}"`));
  assert.match(html, /name="evidence" required/);
  assert.doesNotMatch(html, /name="channel"|name="proof"|id="gmail-send"|id="gmail-simulate"/);
  assert.match(html, /Destinatário: empresa@example.org/);
  assert.match(html, /Remetente: scarasoftbauru@gmail.com/);
  assert.match(html, /Assunto: Proposta/);
  assert.match(html, /Ver a prévia do site/);
  assert.match(html, /Gmail ID: gmail12345678/);
});

test('envio externo exige canal e comprovante; resultado incerto mantém reconciliação', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nthis.commercialSection = commercialSection;', display);
  const job = { id: 'job-1', stage: 'ready', contact_status: 'prepared', preview_url: 'https://preview.example', data: { preview_verified: true, commercial_contact: { channel: 'email', destination: 'empresa@example.org', subject: 'Proposta', message: 'Texto preparado' } } };
  let html = display.commercialSection(job);
  assert.match(html, /value="sent_external"/);
  assert.match(html, /name="proof" required/);
  assert.match(html, /name="channel"/);
  job.contact_status = 'not_sent';
  html = display.commercialSection(job);
  assert.match(html, /name="channel" required/);
  job.contact_status = 'uncertain';
  html = display.commercialSection(job);
  assert.match(html, /reconcilie a tentativa antes de qualquer novo envio/);
  assert.match(html, /value="opted_out"/);
  assert.doesNotMatch(html, /value="sent_external"|value="sent"|id="gmail-send"|id="gmail-simulate"|name="proof"|name="channel"/);
  vm.runInContext('state.commercial_attempts = [{ job_id: "job-1", source: "gmail_api", status: "uncertain", channel: "email", evidence: "Timeout", created_at: "2026-10-01T12:00:00Z" }];', display);
  assert.match(display.commercialSection(job), /reconcilie a tentativa Gmail/);
});

test('trocar para opt-out remove exigência de comprovante oculto', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nthis.updateRecordFields = updateRecordFields;', display);
  const field = () => ({ hidden: false, control: { required: false }, querySelector() { return this.control; } });
  const channel = field(), proof = field();
  const form = { querySelector(selector) { return selector === '.external-channel' ? channel : proof; } };
  display.updateRecordFields(form, 'sent_external');
  assert.equal(channel.control.required, true);
  assert.equal(proof.control.required, true);
  display.updateRecordFields(form, 'opted_out');
  assert.equal(channel.hidden, true);
  assert.equal(proof.hidden, true);
  assert.equal(channel.control.required, false);
  assert.equal(proof.control.required, false);
  assert.doesNotThrow(() => display.updateRecordFields({ querySelector: () => null }, 'replied'));
});

test('operações mostram tentativas sem injetar HTML em falhas e artefatos', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nstate.operations = [{ job_id: "job-1", kind: "deploy", status: "uncertain", executor: "vercel-cli", model: null, attempts: 1, duration_seconds: null, failure: "<script>alert(1)</script>", artifact: "runs/job-1/file", remote_url: "javascript:alert(1)" }]; this.operationSection = operationSection;', display);
  const html = display.operationSection({ id: 'job-1' });
  assert.match(html, /resultado|uncertain/);
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<script>|href="javascript:/);
});
