"""Deterministic, offline commercial copy and channel selection."""
import re
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
        'short': "Olá! Sou Lucas, da scarasoft. Quem procura {segmento} pode pesquisar por '{busca_exemplo}'. Um site profissional ajuda a apresentar seus serviços e facilita o contato. Preparamos uma demonstração independente para {empresa}: {preview_url}\nÉ uma proposta visual não oficial e sem compromisso. O que achou?",
        'full': "Olá! Tudo bem?\n\nSou Lucas, da scarasoft. Quando alguém precisa de {segmento}, pode começar pesquisando por '{busca_exemplo}'. Esse é apenas um exemplo ilustrativo de busca.\n\nTer um site profissional pode ajudar {empresa} a apresentar seus serviços, transmitir confiança na primeira impressão e facilitar o contato.\n\nPreparamos uma demonstração independente de como poderia ficar um site para a empresa:\n{preview_url}\n\nÉ uma proposta visual não oficial e sem compromisso. Gostaria de saber o que achou!\n\n{assinatura}\n{email_comercial}\n{telefone_comercial}",
    },
    'redesign': {
        'subject': 'Proposta visual para {empresa}',
        'short': 'Olá! Sou Lucas, da scarasoft. Conheci a {empresa} e preparei uma demonstração independente de uma apresentação digital renovada: {preview_url}\nÉ uma proposta visual não oficial, sem compromisso e sem alteração do site atual. O que achou?',
        'full': 'Olá! Tudo bem?\n\nSou Lucas, da scarasoft. Conheci a {empresa} e seu site e preparei uma proposta visual de apresentação digital renovada.\n\nMuitos clientes pesquisam e comparam empresas pela internet antes de entrar em contato. Um site agradável e fácil de navegar pode fazer diferença nessa primeira impressão.\n\nPreparei uma demonstração independente para vocês:\n{preview_url}\n\nÉ uma proposta visual não oficial, sem compromisso e sem alteração do site atual. O que achou?\n\n{assinatura}\n{email_comercial}\n{telefone_comercial}',
    },
    'site_inoperante': {
        'subject': 'Uma demonstração de site para {empresa}',
        'short': 'Olá! Sou Lucas, da scarasoft. Ao pesquisar a {empresa}, tentei acessar o site informado e encontrei uma dificuldade de acesso: {observacao_verificada}. Preparei uma demonstração independente: {preview_url}\nÉ uma proposta visual não oficial e sem compromisso. O que achou?',
        'full': 'Olá! Tudo bem?\n\nSou Lucas, da scarasoft. Ao pesquisar a {empresa}, tentei acessar o site informado e encontrei uma dificuldade de acesso: {observacao_verificada}.\n\nQuando alguém procura um serviço pela internet, não conseguir abrir o site pode levar essa pessoa a buscar outra opção. Por isso, preparei uma demonstração independente de um novo site para apresentar os serviços e facilitar o contato:\n{preview_url}\n\nÉ uma proposta visual não oficial e sem compromisso. Gostaria de mostrar essa possibilidade para vocês.\n\n{assinatura}\n{email_comercial}\n{telefone_comercial}',
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
    whatsapp = contacts.get('whatsapp') or {}
    if not isinstance(whatsapp, dict): whatsapp = {}
    if 'whatsapp_manual' not in exclude and whatsapp.get('status') != 'nao_utiliza':
        phone = contacts.get('phone') or {}
        if not isinstance(phone, dict): phone = {}
        number = whatsapp.get('value') if whatsapp.get('status') == 'confirmado' else phone.get('value')
        if isinstance(number, str) and re.fullmatch(r'\+[1-9][0-9]{7,14}', number):
            return 'whatsapp_manual', number
    return 'no_channel', ''

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
