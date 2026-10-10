# Piloto de prospecção pós-PR #4 — Bauru/SP

Execução em 10/10/2026, sobre a `main` que contém o merge do PR #4 (`5e54d61`). Este documento publica somente resultados agregados e limitações do workflow. Os registros por empresa, URLs, telefones e evidências permanecem no diretório local privado `runs/scouting/piloto-pos-pr4-bauru/`, conforme `AGENTS.md` e `.gitignore`.

## Escopo e método

- Descoberta pelo navegador: 3 empresas de climatização, 3 chaveiros, 3 serralherias/portões automáticos e 3 vidraçarias/esquadrias.
- Comparação dos candidatos com os lotes A e B e com o histórico local por nome, domínio e telefone. Nenhuma duplicidade foi confirmada entre os 12 selecionados. Aliases não conhecidos continuam sendo uma limitação.
- Toda URL candidata passou por `tools/check_urls.py` antes de qualquer confirmação. Para empresas sem URL própria identificada, a busca por nome exato e, quando necessário, cidade foi registrada em JSON e classificada pelo fluxo de `tools/digital_presence.py`.
- Os encaminhamentos foram apenas registrados. Não houve auditoria visual, geração de prévia, contato comercial ou gravação no banco de produção.

## Resultado

| Métrica | Resultado |
|---|---:|
| Candidatos distintos encontrados | 13 |
| Empresas únicas selecionadas | 12 |
| URLs candidatas no conjunto selecionado | 6 |
| URLs confirmadas por resposta HTTP e correspondência no HTML | 4 |
| URLs acessíveis, mas com identidade inconclusiva | 2 |
| URLs inacessíveis no conjunto selecionado | 0 |
| Empresas sem URL própria identificada, com pesquisa de presença digital | 6 |

Distribuição dos encaminhamentos: `auditoria_visual_futura` **4**, `revisao_pendente` **2**, `avaliar_site_inoperante` **0**, `primeiro_site_potencial` **6** e `avaliar_primeiro_site` **0**. Nenhum foi executado automaticamente.

As seis URLs selecionadas retornaram HTTP 200 na execução final, sem reutilização de cache e sem exceder o limite de 1 MiB. A resposta 200, isoladamente, não foi tomada como confirmação de identidade. A sondagem final de seis URLs levou 1.415 ms segundo o verificador. O tempo total de pesquisa não foi medido de ponta a ponta. Não foram usados créditos Firecrawl nem APIs pagas; o custo da navegação e das requisições HTTP não foi mensurável.

## Limitações encontradas

1. Um candidato adicional foi excluído porque uma busca associou sua ficha local a um site de empresa homônima em outra região. O verificador retornou HTTP 200 e `confirmada` por correspondência de nome, mas a leitura do conteúdo revelou cidade e telefone incompatíveis. A URL não foi contabilizada entre as quatro confirmações. O caso demonstra que a confirmação por nome no HTML pode gerar falso positivo quando há homônimos.
2. Duas URLs do conjunto selecionado ficaram `acessivel_inconclusiva`. Elas permanecem em `revisao_pendente`, sem auditoria visual automática.
3. A classificação estruturada usa correspondência estrita de nome. Um possível alias em resultados sociais foi preservado no registro privado, sem contar como sinal confirmado da empresa.
4. Uma primeira sondagem em ambiente com DNS restrito produziu erros de infraestrutura. As mesmas URLs foram verificadas novamente com acesso de rede; os resultados finais refletem a segunda sondagem. O erro inicial não foi interpretado como site inoperante.

Uma correção futura possível é confrontar localidade e telefone ao associar domínio e ficha, encaminhando divergências para revisão. Outra é aceitar aliases somente quando houver evidência independente de identidade. Nenhuma dessas mudanças foi implementada neste piloto.

## Avaliação

O workflow funcionou para descoberta, comparação com lotes anteriores, verificação HTTP, preservação de empresas sem site identificado e classificação de presença digital. A falha observada com homônimo exige revisão de identidade antes de usar `confirmada` como gatilho para etapas posteriores. O relatório completo e os CSVs/JSONs por empresa continuam privados no diretório de execução citado acima.
