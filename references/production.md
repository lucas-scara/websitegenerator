# Produção rápida com template preparado

## Gerar a prévia

Use `python3 tools/quick_site.py templates` para listar modelos. O único modelo atual é `electrician`, adequado somente a eletricistas. Preserve layout, imagens ilustrativas e rotas. Por empresa, personalize nome, telefone, e-mail, rua, cidade, CEP, cor da marca e `enabled_services`. Não invente preços, horários, certificações, avaliações, equipe ou projetos.

Os IDs permitidos estão em `templates/electrician/services.json`. Ative **somente** serviços confirmados no site original ou outra fonte verificável da própria empresa. Registre, em notas privadas da execução, cada ID ativado e a URL/trecho que o comprova. Ausência de evidência significa serviço desativado; não use imagens ilustrativas nem textos deste template como prova. Chamadas antigas sem `enabled_services` continuam aceitas e geram uma prévia sem serviços específicos ativados. O filtro cobre menus, cartões, textos, formulário, galeria e páginas de serviço; uma URL direta de serviço desativado exibe a página não encontrada. Todas as prévias incluem `noindex, nofollow`.

```sh
./website --template electrician --name 'Elétrica Exemplo' --theme-color '#2563eb' --phone '+55 11 99999-9999' --email 'contato@exemplo.com.br' --street 'Rua Exemplo, 10' --city 'São Paulo' --zip '01000-000'

# Somente após conferir e registrar a fonte de cada serviço:
./website --template electrician --name 'Elétrica Exemplo' --phone '+55 11 99999-9999' --enabled-services electrical-repairs maintenance
```

Nome e pelo menos um contato público verificado são obrigatórios; endereço e CEP são opcionais. Registre fontes. A saída fica em `runs/quick/ID/site/`, com manifesto ao lado. O gerador cria cópia isolada do build preparado, sem `npm` por empresa. Valide nome, contatos, layout e navegação. O formulário da prévia é demonstrativo e não envia mensagens.

## Preparar o template após edição

```sh
python3 tools/quick_site.py prepare --template electrician
```

O comando instala dependências se necessário, roda lint e `vite build`, depois grava a impressão digital do template. Faça QA desktop/mobile e das rotas após editar o modelo. O prerender legado `templates/electrician/scripts/prerender.mjs` é inseguro e **não deve ser executado**. Não use `build:static` nem prepare cópia por empresa.

## Vercel

Lucas optou por operar localmente e autorizou remover o projeto fictício `revamp-br-mvp-demo-20261010`. Ele foi removido; nenhuma nova publicação faz parte da operação local. A geração e o dashboard continuam funcionando na máquina, mas uma URL `127.0.0.1` não pode ser enviada a uma empresa como prévia pública. Antes de contato real que contenha link, definir e autorizar a forma de publicação e verificar a URL acessível sem sessão.

O escopo de `settings.json` foi identificado por `whoami` e `teams ls` na conta Lucas; reconfirme-o antes de publicar com a CLI indicada (`pnpm dlx vercel@59.16.0`). Não use o escopo do autor original. Crie um projeto novo `revamp-JOB_ID` para a pasta `site/`, sem copiar `.vercel` nem variáveis de outro projeto. Confira o conteúdo de `.vercel/project.json` antes do deploy.

**Atenção ao primeiro deploy:** na CLI 59.16.0, o primeiro `vercel deploy` do projeto de demonstração retornou `target: production` e criou alias de produção, mesmo sem `--prod`. Portanto, antes de criar outro projeto ou fazer seu primeiro deploy, confirme a autorização explícita para essa mudança ou um procedimento de prévia comprovado pela CLI. Não presuma que omitir `--prod` basta. A conta também redirecionou a URL a login Vercel para visitante sem sessão; ela não é uma prévia pública utilizável. Não desative a proteção sem autorização. Verifique a URL sem login, página inicial, rota de serviço, imagens, CTA e os cabeçalhos `noindex` antes de usá-la em contato comercial. Não altere domínios ou projetos existentes.

Depois, siga [contato](outreach.md) ou [fallback manual](manual-outreach.md). Sem autorização específica do lote, prepare apenas a simulação, sem submit. Uma pasta local ou resposta de CLI não equivale a publicação verificada.
