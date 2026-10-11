# Prévia comercial com o motor multissegmento

O fluxo usa os perfis de `templates/electrician/segments/` e os comandos existentes em `tools/quick_site.py`. Dados reais de prospectos, evidências, capturas e IDs de deployment permanecem em `runs/`, fora do Git.

1. Verifique identidade, cidade, URL, contato e serviços em fontes identificadas. Escolha apenas IDs de `service-catalog.json` que essas fontes sustentam.
2. Crie um JSON privado em `runs/` com `template`, `name`, `city`, `state`, contatos, `enabled_services` e `preview: true`. Deixe campos sem evidência vazios. Não use os serviços padrão de um perfil para uma empresa real sem verificação.
3. Depois de alterar o motor, rode `python3 tools/quick_site.py prepare --template <id>`. Gere com `python3 tools/quick_site.py batch runs/<arquivo>.json`. O retorno indica a pasta `site` estática de cada empresa.
4. Confirme `.vercel/project.json`, a equipe e o projeto antes do deploy. Vincule cada pasta `site` ao projeto já autorizado e publique com `vercel deploy --cwd <site> --target preview`. Nunca envie o repositório completo ou use `--prod` neste fluxo.
5. Confirme a URL exclusiva e o ID do deployment. Teste acesso sem login, rotas, imagens, CTAs, viewport desktop/mobile, formulário desativado, meta `noindex` e cabeçalho `X-Robots-Tag`. Revalide todas as URLs depois do último deploy.

O formulário de `preview: true` é demonstrativo e não permite envio. Os links de telefone e WhatsApp continuam disponíveis para inspeção, mas este workflow não autoriza contato comercial. `noindex` reduz indexação; não restringe acesso à URL.
