# Verificação técnica de URLs candidatas

Toda URL candidata precisa passar pelo verificador antes de ser considerada confirmada. URLs apenas indicadas em buscas são entradas pendentes, não resultados finais.

O coordenador pode chamar este comando após descobrir URLs, antes de qualquer auditoria visual:

```sh
python3 tools/check_urls.py \
  --input runs/scouting/lote-b-bauru-2026-10-10/B_deduplicado.csv \
  --output runs/scouting/lote-b-bauru-2026-10-10/B_urls_verificadas.csv \
  --report runs/scouting/lote-b-bauru-2026-10-10/B_urls_relatorio.json \
  --byte-limit 1048576
```

O CSV de entrada não é sobrescrito. As colunas originais são mantidas e a classificação nova fica em `status_url` e `encaminhamento`. Por padrão, o programa reconhece `empresa` e `site_identificado`, além de nomes comuns como `nome_empresa`, `business_name`, `url_candidata` e `website`. Use `--name-column`, `--url-column` e, se necessário, `--id-column` para outros cabeçalhos. Uma linha sem URL recebe `sem_url` sem acesso à rede.

Os limites padrão são 8 segundos por tentativa, 5 sondagens simultâneas, uma repetição apenas para falhas transitórias, 4 redirecionamentos e 256 KiB de HTML por resposta. `--timeout`, `--workers`, `--retries`, `--redirects` e `--byte-limit` permitem reduzi-los. O programa reaproveita resultados acessíveis do mesmo CSV de saída por até 24 horas para a mesma URL e empresa; `--reuse-hours 0` força nova verificação. O campo `reutilizado` distingue esse caso. Falhas são verificadas de novo.

## Caminho A — URL encontrada

O verificador tenta a URL por HTTP, registra status, URL final e motivo, e encaminha sem iniciar etapas seguintes. `confirmada` exige uma correspondência forte do nome comercial no HTML. Além do nome completo, uma forma abreviada pode ser suficiente quando aparece no título ou cabeçalho e contém um termo distintivo. Termos genéricos como “chaveiro”, “vidraçaria” e “Bauru” sozinhos não confirmam identidade. Se a evidência não bastar, o estado é `acessivel_inconclusiva`.

Se a resposta for HTTP 200 com HTML acima do limite de bytes, o estado também é `acessivel_inconclusiva`, com `motivo=limite_bytes` e `http_status=200`. Isso registra que o servidor respondeu, sem afirmar que o site está fora do ar ou que a identidade foi verificada. Páginas de domínio estacionado, suspensão e erro genérico conhecidas recebem `falha_tecnica`. Falha de acesso não exclui a oportunidade; ela segue para `avaliar_site_inoperante`.

## Caminho B — URL não encontrada

O CSV mantém `status_url=sem_url`. Uma pesquisa leve pode preencher sinais de presença digital e mudar apenas o encaminhamento: `primeiro_site_potencial` quando houver sinal suficientemente relacionado à empresa; `avaliar_primeiro_site` caso contrário. Se a pesquisa revelar uma URL própria, ela entra em `url_candidata_pendente`, com `encaminhamento=revisao_pendente`, até passar pela verificação HTTP. Nenhuma prioridade comercial ou etapa de geração é iniciada automaticamente.

O agente usa o navegador `iab` para pesquisar o nome exato. Se for ambíguo, faz no máximo uma segunda consulta com a cidade. Examine até dez resultados relevantes. O projeto não possui uma API de busca programática do navegador; por isso, o verificador aceita resultados estruturados e gera um plano de consultas, sem raspar diretamente o HTML do Google. Exemplo:

```sh
python3 tools/check_urls.py \
  --input runs/scouting/lote-b-bauru-2026-10-10/B_deduplicado.csv \
  --output runs/scouting/lote-b-bauru-2026-10-10/B_urls_presenca_verificadas.csv \
  --report runs/scouting/lote-b-bauru-2026-10-10/B_urls_presenca_relatorio.json \
  --search-plan runs/scouting/lote-b-bauru-2026-10-10/B_consultas_preparadas.csv \
  --search-results runs/scouting/lote-b-bauru-2026-10-10/B_presenca_resultados_navegador.json \
  --byte-limit 1048576
```

O JSON de resultados contém uma lista `empresas`. Cada registro usa `id` (ou `empresa`), `consultas` (máximo 2), `status` (`concluida`, `indisponivel` ou `nao_executada`), `pesquisado_em`, `fonte` e até dez `resultados`. Cada resultado pode ter `tipo` (`google_business`, `instagram`, `facebook`, `diretorio` ou `site_proprio`), `titulo`, `cidade`, `url`, `dominio_exibido`, `fonte_url` e `origem`. Para resultados sociais sem URL direta disponível, registre o domínio exibido e a URL da página de busca em `fonte_url`; não visite o perfil. Um resultado em outra cidade ou com nome fraco não conta como sinal da empresa.

Quando apenas o CSV de prospecção anterior estiver disponível, `--use-existing-observations` reaproveita categorias explícitas como `ficha_local`, identificando-as como `levantamento_anterior`. Isso não equivale a uma pesquisa nova e não inventa URLs de resultados. Os CSVs de entrada e JSONs de evidência ficam privados em `runs/`.

Os sinais `google_business_observado`, `presenca_social_observada`, `presenca_diretorio_observada`, `instagram_observado` e `facebook_observado` aceitam `sim`, `nao_observado` e `nao_verificado`. `nao_observado` significa apenas que o sinal não apareceu na pesquisa registrada. Pesquisa indisponível mantém `nao_verificado`. `fonte_sinal`, `fonte_busca`, `consulta_presenca`, `data_pesquisa_presenca` e `referencias_busca` preservam a rastreabilidade. Valores e fonte já fornecidos pelo operador não são sobrescritos.

As informações sobre **Chaveiro Bandeirantes** (`https://chaveirobandeirantes.com.br/`) e **Destak Vidros** (`https://www.destakvidros.com.br/`) vieram do operador: ele relatou sites inacessíveis e presença em Perfil da Empresa no Google, redes sociais e diretórios. Esses dados não são evidência produzida pelo verificador. Ao adicioná-las a um CSV, registre `sim` nos três sinais, `fonte_sinal=operador` e `revisao_humana=pendente`. Mesmo se a sondagem técnica falhar, preserve as linhas com encaminhamento `avaliar_site_inoperante`.

O relatório JSON reúne estados técnicos, encaminhamentos, erros por motivo, respostas limitadas por bytes e tempo total. O CSV e o relatório devem ficar no diretório privado `runs/`, sem commit. URLs em campos de auditoria são exibidas sem usuário, senha, query ou fragmento. O CSV de origem permanece privado e pode conter dados originais. A revisão humana é possível, mas não é iniciada automaticamente.
