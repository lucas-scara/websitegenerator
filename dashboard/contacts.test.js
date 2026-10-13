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

test('operações mostram tentativas sem injetar HTML em falhas e artefatos', () => {
  const display = vm.createContext({ URL, Intl, Date });
  vm.runInContext(app.slice(0, app.indexOf('function category(job)')) + '\nstate.operations = [{ job_id: "job-1", kind: "deploy", status: "uncertain", executor: "vercel-cli", model: null, attempts: 1, duration_seconds: null, failure: "<script>alert(1)</script>", artifact: "runs/job-1/file", remote_url: "javascript:alert(1)" }]; this.operationSection = operationSection;', display);
  const html = display.operationSection({ id: 'job-1' });
  assert.match(html, /resultado|uncertain/);
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<script>|href="javascript:/);
});
