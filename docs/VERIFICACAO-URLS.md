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

`confirmada` exige o nome completo da empresa no texto HTML. `acessivel_inconclusiva` significa que há HTML utilizável, mas a identidade não foi confirmada. Páginas de domínio estacionado, suspensão e erro genérico conhecidas recebem `falha_tecnica`. A ausência de correspondência simples não prova que o site pertence a outra empresa; exige revisão humana. `falha_tecnica` e `sem_url` continuam elegíveis à avaliação comercial posterior. Nenhuma classificação dispara outra etapa.

Os sinais opcionais `google_business_observado`, `presenca_social_observada` e `presenca_diretorio_observada` aceitam `sim`, `nao_observado` e `nao_verificado`. Campos vazios viram `nao_verificado`. Preencha `fonte_sinal` quando houver observação. `nao_observado` não comprova ausência de presença digital. O verificador não consulta essas fontes.

As informações sobre **Chaveiro Bandeirantes** (`https://chaveirobandeirantes.com.br/`) e **Destak Vidros** (`https://www.destakvidros.com.br/`) vieram do operador: ele relatou sites inacessíveis e presença em Perfil da Empresa no Google, redes sociais e diretórios. Esses dados não são evidência produzida pelo verificador. Ao adicioná-las a um CSV, registre `sim` nos três sinais, `fonte_sinal=operador` e `revisao_humana=pendente`. Mesmo se a sondagem técnica falhar, preserve as linhas com encaminhamento `avaliar_site_inoperante`.

O relatório JSON reúne contagens, erros por motivo e tempo total. O CSV e o relatório devem ficar no diretório privado `runs/`, sem commit. URLs em campos de auditoria são exibidas sem usuário, senha, query ou fragmento. O CSV de origem permanece privado e pode conter dados originais.
