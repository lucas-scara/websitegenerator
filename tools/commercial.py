"""Deterministic, offline commercial copy and channel selection."""
import re
import datetime as dt
from urllib.parse import quote, urlsplit

SEARCHES = {
    'chaveiros': ('chaveiro', 'chaveiro perto de mim'),
    'climatizacao': ('empresa de climatização', 'instalação de ar-condicionado em {cidade}'),
    'serralheria': ('serralheria', 'serralheria para portão em {cidade}'),
    'electrician': ('eletricista', 'eletricista perto de mim'),
    'vidracaria': ('vidraçaria', 'box de banheiro em {cidade}'),
    'dedetizacao': ('dedetizadora', 'dedetizadora em {cidade}'),
    'toldos': ('empresa de toldos', 'instalação de toldos em {cidade}'),
}
ALLOWED = {'empresa','cidade','segmento','busca_exemplo','preview_url','observacao_verificada','assinatura','email_comercial','telefone_comercial'}
COPY = {
    'primeiro_site': {
        'subject': 'Uma proposta visual para {empresa}',
        'short': "Olá! Sou Lucas, da scarasoft. Quem procura {segmento} pode buscar, por exemplo, '{busca_exemplo}'. Um site profissional ajuda a conhecer os serviços da {empresa}, transmite confiança e facilita o contato. Veja a prévia demonstrativa: {preview_url}\nÉ independente, não oficial e sem compromisso. O que achou?",
        'full': "Olá! Tudo bem?\n\nSou Lucas, da scarasoft. Quem precisa de {segmento} pode pesquisar, por exemplo, '{busca_exemplo}'. Um site profissional ajuda a conhecer os serviços da {empresa}, transmite confiança na primeira impressão e facilita o contato.\n\nPreparamos esta prévia demonstrativa:\n{preview_url}\n\nEla é independente, não oficial e sem compromisso. Gostaria de saber o que achou!\n\n{assinatura}\n{email_comercial}\n{telefone_comercial}",
    },
    'redesign': {
        'subject': 'Proposta visual para {empresa}',
        'short': "Olá! Sou Lucas, da scarasoft. Quem busca, por exemplo, '{busca_exemplo}' pode conhecer a {empresa} pelo site. Uma apresentação profissional ajuda a descobrir os serviços, transmite confiança e facilita o contato. Preparei uma prévia renovada: {preview_url}\nÉ demonstrativa, independente e não oficial; não altera o site atual. O que achou?",
        'full': "Olá! Tudo bem?\n\nSou Lucas, da scarasoft. Conheci a {empresa} e seu site. Quem busca, por exemplo, '{busca_exemplo}' pode conhecer os serviços pela internet antes de entrar em contato. Uma apresentação profissional e fácil de navegar ajuda a transmitir confiança nessa primeira impressão.\n\nPreparei uma prévia renovada:\n{preview_url}\n\nÉ demonstrativa, independente, não oficial e sem compromisso; não altera o site atual. O que achou?\n\n{assinatura}\n{email_comercial}\n{telefone_comercial}",
    },
    'site_inoperante': {
        'subject': 'Uma demonstração de site para {empresa}',
        'short': 'Olá! Sou Lucas, da scarasoft. Ao pesquisar a {empresa}, encontrei esta dificuldade ao acessar o site informado: {observacao_verificada}. Uma apresentação profissional ajuda a mostrar os serviços, transmitir confiança e facilitar o contato. Preparei uma prévia: {preview_url}\nÉ demonstrativa, independente, não oficial e sem compromisso. O que achou?',
        'full': 'Olá! Tudo bem?\n\nSou Lucas, da scarasoft. Ao pesquisar a {empresa}, tentei acessar o site informado e encontrei esta dificuldade: {observacao_verificada}.\n\nQuando alguém procura um serviço pela internet, não conseguir abrir o site pode levar essa pessoa a buscar outra opção. Uma apresentação profissional ajuda a mostrar os serviços, transmitir confiança e facilitar o contato.\n\nPreparei esta prévia demonstrativa:\n{preview_url}\n\nEla é independente, não oficial e sem compromisso. Gostaria de saber o que achou.\n\n{assinatura}\n{email_comercial}\n{telefone_comercial}',
    },
}

def route(contacts, exclude=()):
    contacts = contacts if isinstance(contacts, dict) else {}
    form = contacts.get('form') or {}
    if not isinstance(form, dict): form = {}
    form_url = str(form.get('url', ''))
    try: parsed = urlsplit(form_url)
    except ValueError: parsed = urlsplit('')
    if ('form' not in exclude and form.get('status') == 'encontrado' and form.get('eligible') is True
            and isinstance(form.get('purpose'), str) and form['purpose'].strip()
            and parsed.scheme in ('https','http') and parsed.hostname and not parsed.username and not parsed.password
            and not any(word in form['purpose'].lower() for word in ('orçamento','orcamento','suporte','atendimento'))
            and not form.get('restrictions')):
        return 'form', form_url
    email = contacts.get('email') or {}
    if not isinstance(email, dict): email = {}
    if 'email' not in exclude and email.get('status') == 'encontrado' and re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', str(email.get('value',''))):
        return 'email', email['value']
    if contacts.get('whatsapp') is False: return 'no_channel', ''
    whatsapp = contacts.get('whatsapp') or {}
    if not isinstance(whatsapp, dict): whatsapp = {}
    if 'whatsapp_manual' not in exclude and whatsapp.get('status') != 'nao_utiliza':
        phone = contacts.get('phone') or {}
        if not isinstance(phone, dict): phone = {}
        source = whatsapp if whatsapp.get('status') == 'confirmado' else phone
        number = source.get('value')
        if isinstance(number, str) and re.fullmatch(r'\+[1-9][0-9]{7,14}', number) and reliable_source(source):
            return 'whatsapp_manual', number
    return 'no_channel', ''

def reliable_source(record):
    """A public number needs a traceable source and a real verification date."""
    try:
        url = urlsplit(record.get('source', ''))
        checked = dt.date.fromisoformat(record.get('checked_at', ''))
        host = (url.hostname or '').lower().rstrip('.')
        return (url.scheme in ('http', 'https') and '.' in host
                and host != 'localhost' and not host.endswith(('.local','.localhost'))
                and not url.username and not url.password and checked <= dt.datetime.now(dt.timezone.utc).date())
    except (TypeError, ValueError):
        return False

def render(template, variant, values):
    if template not in COPY or variant not in ('short','full','subject'):
        raise ValueError('Unknown commercial template or variant')
    source = COPY[template][variant]
    names = set(re.findall(r'{([^{}]+)}', source))
    if not names <= ALLOWED: raise ValueError('Unknown message placeholder')
    missing = [name for name in names if not isinstance(values.get(name), str) or not values[name].strip()]
    if missing: raise ValueError('Missing message values: ' + ', '.join(sorted(missing)))
    result = re.sub(r'{([^{}]+)}', lambda match: values[match.group(1)], source)
    if re.search(r'{[^{}]+}', result): raise ValueError('Unfilled message placeholder')
    return result

def whatsapp_link(number, message):
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}', number): raise ValueError('Invalid WhatsApp number')
    return 'https://wa.me/' + number[1:] + '?text=' + quote(message, safe='')
